"""Tests for toonbuilder.toml_to_toon.

TOML parsing needs stdlib ``tomllib`` (Python 3.11+) or the third-party ``toml``
package; serialising TOON back to TOML always needs ``toml``. Tests skip
gracefully when a required dependency is unavailable.
"""

import pytest

from toonbuilder import toml_to_toon


has_parser = toml_to_toon._HAS_TOML_STDLIB or toml_to_toon._HAS_TOML_THIRDPARTY
requires_parser = pytest.mark.skipif(not has_parser, reason="no TOML parser available")


SAMPLE_TOML = """
title = "Example"

[owner]
name = "Tom"
age = 30

[[servers]]
ip = "10.0.0.1"
role = "frontend"

[[servers]]
ip = "10.0.0.2"
role = "backend"
"""


@requires_parser
def test_encode_from_string():
    toon = toml_to_toon.encode(SAMPLE_TOML)
    assert "title: Example" in toon
    assert "servers[2]{ip,role}:" in toon
    assert "10.0.0.1,frontend" in toon


@requires_parser
def test_encode_from_parsed_object():
    data = {"a": 1, "b": {"c": 2}}
    assert toml_to_toon.encode(data) == "a: 1\nb:\n  c: 2"


def test_decode_requires_toml_package():
    toml = pytest.importorskip("toml")  # noqa: F841 - skip if dumper missing
    toon = "title: Example\nport: 8080"
    out = toml_to_toon.decode(toon)
    assert 'title = "Example"' in out
    assert "port = 8080" in out


def test_decode_empty_returns_empty_string():
    assert toml_to_toon.decode("") == ""
    assert toml_to_toon.decode("   ") == ""


@requires_parser
def test_datetime_survives_as_native_toml_datetime():
    # Regression: datetimes previously round-tripped through the TOON codec
    # as plain strings, so the regenerated TOML re-typed the field as a
    # quoted string literal instead of a native datetime.
    pytest.importorskip("toml")  # decode side needs the dumper
    toml_text = (
        'title = "Example"\n'
        "updated = 1979-05-27T07:32:00-08:00\n"
        "day = 1979-05-27\n"
    )
    toon = toml_to_toon.encode(toml_text)
    assert '"1979-05-27' not in toon  # must be unquoted (a real datetime, not a string)

    restored = toml_to_toon.decode(toon)
    assert "updated = 1979-05-27T07:32:00-08:00" in restored
    assert "day = 1979-05-27" in restored
    assert 'updated = "' not in restored  # must not have been re-typed as a string


@requires_parser
def test_encode_decode_file_round_trip(tmp_path):
    pytest.importorskip("toml")  # decode side needs the dumper
    toml_path = tmp_path / "data.toml"
    toml_path.write_text(SAMPLE_TOML, encoding="utf-8")

    toml_to_toon.encode_file(toml_path)          # -> data.toon
    toon_path = tmp_path / "data.toon"
    assert toon_path.exists()

    toml_to_toon.decode_file(toon_path, tmp_path / "restored.toml")
    restored = (tmp_path / "restored.toml").read_text(encoding="utf-8")
    assert 'title = "Example"' in restored


@requires_parser
def test_encode_file_creates_output_directory(tmp_path):
    toml_path = tmp_path / "in.toml"
    toml_path.write_text('key = "value"\n', encoding="utf-8")
    out = tmp_path / "nested" / "out.toon"
    toml_to_toon.encode_file(toml_path, out)
    assert out.exists()


def test_encode_file_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        toml_to_toon.encode_file(tmp_path / "nope.toml")
