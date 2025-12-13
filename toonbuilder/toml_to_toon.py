"""
TOML to TOON converter.

This module provides functions to encode TOML data to TOON format and decode
TOON format back to TOML. It mirrors the API of `json_to_toon` and `xml_to_toon`.

Notes:
- For reading TOML, Python 3.11+ includes `tomllib`. On older Pythons, the
  third-party `toml` package is required.
- For writing TOML (dumping), the third-party `toml` package is required on
  all Python versions. If it's not installed, `decode()` and `decode_file()` will
  raise an informative error.
"""

from pathlib import Path
from typing import Any, Optional, Union

# Prefer stdlib tomllib on Python 3.11+ for parsing
try:
    import tomllib as _toml_lib  # type: ignore
    _HAS_TOML_STDLIB = True
except Exception:
    _toml_lib = None
    _HAS_TOML_STDLIB = False

# Try third-party toml package for fallback and dumping
try:
    import toml as _toml_thirdparty  # type: ignore
    _HAS_TOML_THIRDPARTY = True
except Exception:
    _toml_thirdparty = None
    _HAS_TOML_THIRDPARTY = False

from . import json_to_toon


def _parse_toml_string(toml_text: str) -> Any:
    """Parse TOML text into Python objects using available parser."""
    if _HAS_TOML_STDLIB and _toml_lib is not None:
        return _toml_lib.loads(toml_text)
    if _HAS_TOML_THIRDPARTY and _toml_thirdparty is not None:
        return _toml_thirdparty.loads(toml_text)
    raise ImportError(
        "TOML parsing requires Python 3.11+ (tomllib) or the 'toml' package.\n"
        "Install with: pip install toml"
    )


def _dump_toml(obj: Any) -> str:
    """Serialize Python object to TOML string using third-party `toml` package.

    Raises ImportError if the dumper is not available.
    """
    if _HAS_TOML_THIRDPARTY and _toml_thirdparty is not None:
        return _toml_thirdparty.dumps(obj)
    raise ImportError(
        "TOML serialization requires the 'toml' package. Install with: pip install toml"
    )


def encode(data: Union[str, Any], indent_level: int = 0, indent_str: str = "  ") -> str:
    """
    Convert TOML data (string or parsed object) to TOON format.

    Args:
        data: TOML content as a string, or a Python object resulting from parsing TOML
        indent_level: indentation level passed to the TOON encoder
        indent_str: indentation string for TOON output

    Returns:
        TOON-formatted string
    """
    # If a string is provided, parse it as TOML
    if isinstance(data, str):
        parsed = _parse_toml_string(data)
    else:
        parsed = data

    # The parsed TOML is a Python mapping/list structure compatible with our
    # json_to_toon encoder
    return json_to_toon.encode(parsed, indent_level=indent_level, indent_str=indent_str)


def decode(toon_text: str) -> str:
    """
    Convert TOON text to a TOML-formatted string.

    Returns a TOML document as a string. Requires the third-party `toml`
    package for dumping; raises ImportError with instructions if unavailable.
    """
    if not toon_text or not toon_text.strip():
        return ""

    # Reuse json_to_toon to decode TOON -> Python objects
    obj = json_to_toon.decode(toon_text)

    # Dump Python object to TOML text
    return _dump_toml(obj)


def encode_file(toml_file_path: Union[str, Path], toon_file_path: Optional[Union[str, Path]] = None,
                indent_str: str = "  ") -> None:
    """
    Read a TOML file, encode to TOON, and write to a .toon file.

    Raises ImportError if no TOML parser is available.
    """
    toml_path = Path(toml_file_path)
    if not toml_path.exists():
        raise FileNotFoundError(f"TOML file not found: {toml_file_path}")

    if toon_file_path is None:
        toon_path = toml_path.with_suffix('.toon')
    else:
        toon_path = Path(toon_file_path)

    # Read and parse TOML
    text = toml_path.read_text(encoding='utf-8')
    parsed = _parse_toml_string(text)

    toon_content = json_to_toon.encode(parsed, indent_str=indent_str)

    toon_path.write_text(toon_content, encoding='utf-8')


def decode_file(toon_file_path: Union[str, Path], toml_file_path: Optional[Union[str, Path]] = None) -> None:
    """
    Read a TOON file, decode to TOML, and write to a .toml file.

    Requires the third-party `toml` package for serialization if available.
    """
    toon_path = Path(toon_file_path)
    if not toon_path.exists():
        raise FileNotFoundError(f"TOON file not found: {toon_file_path}")

    if toml_file_path is None:
        toml_path = toon_path.with_suffix('.toml')
    else:
        toml_path = Path(toml_file_path)

    toon_text = toon_path.read_text(encoding='utf-8')

    obj = json_to_toon.decode(toon_text)

    toml_text = _dump_toml(obj)

    toml_path.write_text(toml_text, encoding='utf-8')
