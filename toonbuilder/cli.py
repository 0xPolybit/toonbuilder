"""
Command-line interface for toonbuilder.

Provides the ``toon`` command with two subcommands:

- ``toon encode`` - convert JSON, XML, or TOML into TOON.
- ``toon decode`` - convert TOON back into JSON, XML, or TOML.

Both read from a file or stdin and write to a file or stdout. See
``toon --help``, ``toon encode --help``, and ``toon decode --help``.
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Tuple

from . import __version__, json_to_toon, toml_to_toon, xml_to_toon

_EXT_TO_FORMAT = {".json": "json", ".xml": "xml", ".toml": "toml"}
_FORMAT_TO_EXT = {"json": ".json", "xml": ".xml", "toml": ".toml"}
_FORMATS = ("json", "xml", "toml")


class CLIError(Exception):
    """Raised for CLI-level problems (bad args, undetectable format, ...)."""


def _read_input(input_arg: Optional[str]) -> Tuple[str, Optional[Path]]:
    """Read input text from a file, or from stdin if omitted or '-'.

    Returns (text, path) - path is None when the input came from stdin, which
    matters later for deciding whether a "sibling file" default output makes
    sense.
    """
    if input_arg is None or input_arg == "-":
        return sys.stdin.read(), None

    path = Path(input_arg)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_arg}")
    return path.read_text(encoding="utf-8"), path


def _write_output(text: str, output_arg: Optional[str], input_path: Optional[Path],
                   default_ext: str) -> None:
    """Write output text to a file, or to stdout.

    Resolution order for where to write:
    1. output_arg == '-' -> stdout (explicit, even if input_path is set).
    2. output_arg given -> that path.
    3. input_path given (a real input file, no -o) -> a sibling file with
       default_ext, mirroring encode_file()/decode_file()'s own default.
    4. otherwise (stdin input, no -o) -> stdout.
    """
    if output_arg == "-":
        sys.stdout.write(text)
        return

    if output_arg is not None:
        out_path = Path(output_arg)
    elif input_path is not None:
        out_path = input_path.with_suffix(default_ext)
    else:
        sys.stdout.write(text)
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Wrote {out_path}", file=sys.stderr)


def _infer_format(explicit: Optional[str], path: Optional[Path]) -> Optional[str]:
    """Resolve a format from an explicit flag or a path's extension."""
    if explicit:
        return explicit
    if path is not None:
        return _EXT_TO_FORMAT.get(path.suffix.lower())
    return None


def _parse_indent(value: str) -> str:
    """Parse --indent into a TOON indent string.

    Accepts a plain integer ("4" -> four spaces), the word "tab", or any
    literal string (including the default, two spaces) passed straight
    through.
    """
    if value.lower() == "tab":
        return "\t"
    if value.isdigit():
        return " " * int(value)
    return value


def _encode_text(fmt: str, text: str, indent_str: str) -> str:
    if fmt == "json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise CLIError(f"invalid JSON input: {e}") from e
        return json_to_toon.encode(data, indent_str=indent_str)
    if fmt == "xml":
        return xml_to_toon.encode(text, indent_str=indent_str)
    if fmt == "toml":
        return toml_to_toon.encode(text, indent_str=indent_str)
    raise CLIError(f"unsupported format: {fmt}")  # pragma: no cover - guarded by argparse choices


def _decode_text(fmt: str, toon_text: str, json_indent: int, root_name: str) -> str:
    if fmt == "json":
        data = json_to_toon.decode(toon_text)
        return json.dumps(data, indent=json_indent, ensure_ascii=False)
    if fmt == "xml":
        return xml_to_toon.decode(toon_text, root_name=root_name)
    if fmt == "toml":
        return toml_to_toon.decode(toon_text)
    raise CLIError(f"unsupported format: {fmt}")  # pragma: no cover - guarded by argparse choices


def _run_encode(args: argparse.Namespace) -> None:
    text, input_path = _read_input(args.input)

    fmt = _infer_format(args.from_format, input_path)
    if fmt is None:
        raise CLIError(
            "cannot determine the input format"
            + (f" of {args.input!r}" if args.input else " when reading from stdin")
            + f"; pass --from {{{','.join(_FORMATS)}}}"
        )

    indent_str = _parse_indent(args.indent)
    toon_text = _encode_text(fmt, text, indent_str)
    _write_output(toon_text, args.output, input_path, ".toon")


def _run_decode(args: argparse.Namespace) -> None:
    toon_text, input_path = _read_input(args.input)

    output_path = Path(args.output) if args.output and args.output != "-" else None
    fmt = _infer_format(args.to_format, output_path) or "json"

    result = _decode_text(fmt, toon_text, args.indent, args.root_name)
    _write_output(result, args.output, input_path, _FORMAT_TO_EXT[fmt])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="toon",
        description="Convert JSON, XML, and TOML to TOON, and back.",
    )
    parser.add_argument("--version", action="version", version=f"toon {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    encode_p = subparsers.add_parser("encode", help="Convert JSON/XML/TOML to TOON")
    encode_p.add_argument(
        "input", nargs="?", default=None,
        help="Input file (.json/.xml/.toml). Omit or pass '-' to read from stdin.",
    )
    encode_p.add_argument(
        "-o", "--output", default=None,
        help="Output file, or '-' for stdout. Defaults to a sibling .toon file "
             "when INPUT is a file, or stdout when reading from stdin.",
    )
    encode_p.add_argument(
        "--from", dest="from_format", choices=_FORMATS, default=None,
        help="Input format. Inferred from INPUT's extension if omitted "
             "(required when reading from stdin).",
    )
    encode_p.add_argument(
        "--indent", default="  ",
        help="TOON indentation: a literal string, an integer (N spaces), or "
             "'tab'. Default: two spaces.",
    )
    encode_p.set_defaults(func=_run_encode)

    decode_p = subparsers.add_parser("decode", help="Convert TOON to JSON/XML/TOML")
    decode_p.add_argument(
        "input", nargs="?", default=None,
        help="Input TOON file. Omit or pass '-' to read from stdin.",
    )
    decode_p.add_argument(
        "-o", "--output", default=None,
        help="Output file, or '-' for stdout. Defaults to a sibling file "
             "(named after --to) when INPUT is a file, or stdout when reading "
             "from stdin.",
    )
    decode_p.add_argument(
        "--to", dest="to_format", choices=_FORMATS, default=None,
        help="Output format. Inferred from OUTPUT's extension if omitted, "
             "otherwise defaults to json.",
    )
    decode_p.add_argument(
        "--indent", type=int, default=2,
        help="JSON output indentation, in spaces. Only applies when the "
             "output format is json. Default: 2.",
    )
    decode_p.add_argument(
        "--root-name", default="root",
        help="Root element name to use when the output format is xml and the "
             "TOON data has no single wrapping key. Default: root.",
    )
    decode_p.set_defaults(func=_run_decode)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("Aborted.", file=sys.stderr)
        return 130
    except (CLIError, FileNotFoundError, ValueError, ImportError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except ET.ParseError as e:
        print(f"error: invalid XML input: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
