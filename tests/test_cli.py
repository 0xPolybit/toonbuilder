"""Tests for the `toon` command-line interface (toonbuilder.cli)."""

import io
import json

import pytest

from toonbuilder import cli


def run(argv, monkeypatch=None, stdin=None):
    """Invoke cli.main() directly and capture its exit code."""
    if monkeypatch is not None and stdin is not None:
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
    return cli.main(argv)


# --------------------------------------------------------------------------- #
# encode: input/output resolution
# --------------------------------------------------------------------------- #

def test_encode_sibling_file_default(tmp_path, capsys):
    json_path = tmp_path / "data.json"
    json_path.write_text('{"a": 1}', encoding="utf-8")

    code = run(["encode", str(json_path)])
    assert code == 0

    toon_path = tmp_path / "data.toon"
    assert toon_path.exists()
    assert toon_path.read_text(encoding="utf-8") == "a: 1"

    err = capsys.readouterr().err
    assert "Wrote" in err and "data.toon" in err


def test_encode_explicit_output(tmp_path):
    json_path = tmp_path / "data.json"
    json_path.write_text('{"a": 1}', encoding="utf-8")
    out_path = tmp_path / "custom.toon"

    code = run(["encode", str(json_path), "-o", str(out_path)])
    assert code == 0
    assert out_path.read_text(encoding="utf-8") == "a: 1"


def test_encode_creates_output_directory(tmp_path):
    json_path = tmp_path / "data.json"
    json_path.write_text('{"a": 1}', encoding="utf-8")
    out_path = tmp_path / "nested" / "dir" / "out.toon"

    code = run(["encode", str(json_path), "-o", str(out_path)])
    assert code == 0
    assert out_path.exists()


def test_encode_stdin_with_from(monkeypatch, capsys):
    code = run(["encode", "--from", "json"], monkeypatch=monkeypatch, stdin='{"a": 1}')
    assert code == 0
    assert capsys.readouterr().out == "a: 1"


def test_encode_stdin_without_from_errors(monkeypatch, capsys):
    code = run(["encode"], monkeypatch=monkeypatch, stdin='{"a": 1}')
    assert code == 1
    assert "--from" in capsys.readouterr().err


def test_encode_output_dash_forces_stdout(tmp_path, capsys):
    json_path = tmp_path / "data.json"
    json_path.write_text('{"a": 1}', encoding="utf-8")

    code = run(["encode", str(json_path), "-o", "-"])
    assert code == 0
    assert capsys.readouterr().out == "a: 1"
    assert not (tmp_path / "data.toon").exists()


def test_encode_unrecognized_extension_without_from_errors(tmp_path, capsys):
    mystery = tmp_path / "data.mystery"
    mystery.write_text("hello", encoding="utf-8")

    code = run(["encode", str(mystery)])
    assert code == 1
    assert "--from" in capsys.readouterr().err


def test_encode_missing_input_file_errors(tmp_path, capsys):
    code = run(["encode", str(tmp_path / "nope.json")])
    assert code == 1
    assert "not found" in capsys.readouterr().err


def test_encode_invalid_json_errors(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json}", encoding="utf-8")

    code = run(["encode", str(bad)])
    assert code == 1
    assert "invalid JSON" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# decode: input/output resolution and format inference
# --------------------------------------------------------------------------- #

def test_decode_sibling_file_default_is_json(tmp_path):
    toon_path = tmp_path / "data.toon"
    toon_path.write_text("a: 1", encoding="utf-8")

    code = run(["decode", str(toon_path)])
    assert code == 0

    json_path = tmp_path / "data.json"
    assert json.loads(json_path.read_text(encoding="utf-8")) == {"a": 1}


def test_decode_to_xml_via_flag(tmp_path, capsys):
    toon_path = tmp_path / "data.toon"
    toon_path.write_text("person:\n  name: Alice", encoding="utf-8")

    code = run(["decode", str(toon_path), "--to", "xml", "-o", "-"])
    assert code == 0
    out = capsys.readouterr().out
    assert "<person>" in out and "<name>Alice</name>" in out


def test_decode_output_extension_infers_format(tmp_path):
    toon_path = tmp_path / "data.toon"
    toon_path.write_text("person:\n  name: Alice", encoding="utf-8")
    out_path = tmp_path / "restored.xml"

    code = run(["decode", str(toon_path), "-o", str(out_path)])
    assert code == 0
    assert "<name>Alice</name>" in out_path.read_text(encoding="utf-8")


def test_decode_root_name(tmp_path, capsys):
    toon_path = tmp_path / "data.toon"
    toon_path.write_text("a: 1\nb: 2", encoding="utf-8")

    code = run(["decode", str(toon_path), "--to", "xml", "--root-name", "mydata", "-o", "-"])
    assert code == 0
    assert "<mydata>" in capsys.readouterr().out


def test_decode_json_indent(tmp_path, capsys):
    toon_path = tmp_path / "data.toon"
    toon_path.write_text("a: 1", encoding="utf-8")

    code = run(["decode", str(toon_path), "--indent", "4", "-o", "-"])
    assert code == 0
    assert capsys.readouterr().out == '{\n    "a": 1\n}'


def test_decode_malformed_toon_errors(tmp_path, capsys):
    bad = tmp_path / "bad.toon"
    bad.write_text("not a valid line\nanother bad line without structure", encoding="utf-8")

    code = run(["decode", str(bad)])
    assert code == 1
    assert "Invalid TOON syntax" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# Round-trips through the CLI
# --------------------------------------------------------------------------- #

def test_encode_decode_round_trip_json(tmp_path):
    data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
    json_path = tmp_path / "data.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")

    assert run(["encode", str(json_path)]) == 0
    assert run(["decode", str(tmp_path / "data.toon"), "-o", str(tmp_path / "back.json")]) == 0

    restored = json.loads((tmp_path / "back.json").read_text(encoding="utf-8"))
    assert restored == data


@pytest.mark.parametrize("indent_flag,expect", [
    ("tab", "\tdebug: true"),
    ("4", "    debug: true"),
])
def test_encode_indent_variants(tmp_path, indent_flag, expect):
    json_path = tmp_path / "data.json"
    json_path.write_text('{"config": {"debug": true}}', encoding="utf-8")
    out_path = tmp_path / "out.toon"

    assert run(["encode", str(json_path), "-o", str(out_path), "--indent", indent_flag]) == 0
    assert expect in out_path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Misc
# --------------------------------------------------------------------------- #

def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc_info:
        run(["--version"])
    assert exc_info.value.code == 0
    assert "toon" in capsys.readouterr().out


def test_no_command_errors(capsys):
    with pytest.raises(SystemExit) as exc_info:
        run([])
    assert exc_info.value.code != 0
