"""Tests for toonbuilder.json_to_toon.

Covers encode/decode round-trips plus explicit regressions for the bugs fixed
in 0.2.0 (lossless quoting, tabular-safety, indentation-aware decoding and
round-tripping of non-tabular arrays).
"""

import json

import pytest

from toonbuilder import json_to_toon


def rt(data, **kwargs):
    """Encode then decode, asserting the value survives unchanged."""
    encoded = json_to_toon.encode(data, **kwargs)
    decoded = json_to_toon.decode(encoded)
    assert decoded == data, f"round-trip mismatch\n encoded: {encoded!r}\n decoded: {decoded!r}"
    return encoded


# --------------------------------------------------------------------------- #
# Basic round-trips
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("data", [
    {"name": "Alice", "age": 30},
    {"a": 1, "b": 1.5, "c": True, "d": False, "e": None, "f": "hello"},
    {"config": {"debug": True, "timeout": 30, "nested": {"deep": "value"}}},
    {"tags": ["python", "json", "toon"]},
    {"nums": [1, 2, 3, 4]},
    {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]},
    {"empty_obj": {}, "empty_list": []},
    {"mixed": [1, "two", None, True, 3.5]},
    {},
])
def test_basic_round_trip(data):
    rt(data)


def test_tabular_output_shape():
    data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
    assert json_to_toon.encode(data) == "users[2]{id,name}:\n  1,Alice\n  2,Bob"


def test_primitive_array_inline():
    assert json_to_toon.encode({"tags": ["a", "b", "c"]}) == "tags[3]: a,b,c"


# --------------------------------------------------------------------------- #
# Regression: lossless quoting of scalar-looking strings
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("value", [
    "01234",      # leading zero
    "1.0",        # float-looking
    "42",         # int-looking
    "-5",         # signed
    "true",       # bool-looking
    "false",
    "null",       # null-looking
    "{}",         # structural token
    "[]",
])
def test_scalar_looking_strings_stay_strings(value):
    data = {"key": value}
    encoded = json_to_toon.encode(data)
    decoded = json_to_toon.decode(encoded)
    assert decoded == data
    assert isinstance(decoded["key"], str)


def test_genuine_scalars_preserved():
    data = {"i": 42, "f": 1.0, "t": True, "f2": False, "n": None}
    rt(data)
    decoded = json_to_toon.decode(json_to_toon.encode(data))
    assert decoded["i"] == 42 and isinstance(decoded["i"], int)
    assert decoded["f"] == 1.0 and isinstance(decoded["f"], float)
    assert decoded["t"] is True and decoded["f2"] is False and decoded["n"] is None


def test_strings_that_are_not_numbers_stay_unquoted():
    # scientific / hex / mixed-dot forms are NOT parsed as numbers, so they must
    # still round-trip as strings without being quoted unnecessarily.
    for value in ("1e5", "0x1F", "1.2.3", "v1.0"):
        assert json_to_toon.decode(json_to_toon.encode({"k": value})) == {"k": value}


# --------------------------------------------------------------------------- #
# Regression: tabular detection only for scalar-valued uniform objects
# --------------------------------------------------------------------------- #

def test_nested_values_are_not_tabular():
    data = {"rows": [{"a": 1, "b": {"x": 9}}, {"a": 2, "b": {"x": 8}}]}
    encoded = json_to_toon.encode(data)
    assert "{a,b}" not in encoded  # must not be collapsed to a tabular header
    assert json_to_toon.decode(encoded) == data


def test_non_uniform_objects_round_trip():
    rt({"items": [{"a": 1}, {"a": 1, "b": 2}]})


# --------------------------------------------------------------------------- #
# Regression: non-tabular arrays (objects / mixed / nested) round-trip
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("data", [
    {"rows": [{"a": 1, "b": {"x": 9}}, {"a": 2, "b": {"x": 8}}]},
    {"mix": [1, "two", {"k": "v"}, None, True]},
    {"matrix": [[1, 2, 3], [4, 5, 6]]},
    {"groups": [[{"id": 1}, {"id": 2}], [{"id": 3}]]},
    {"a": {"b": {"c": {"d": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]}}}},
    [{"a": 1}, {"a": 1, "b": 2}],   # top-level complex array
    [[1, 2], [3, 4]],               # top-level array of arrays
    [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}],  # top-level tabular
])
def test_complex_arrays_round_trip(data):
    rt(data)


# --------------------------------------------------------------------------- #
# Regression: decode honours the encoder's indent_str (tabs / 4 spaces)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("indent_str", ["  ", "    ", "\t"])
def test_custom_indent_round_trip(indent_str):
    data = {"config": {"debug": True, "timeout": 30}, "users": [{"id": 1, "name": "Alice"}]}
    rt(data, indent_str=indent_str)


# --------------------------------------------------------------------------- #
# Strings with special characters / unicode
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("value", [
    "hello, world",     # comma
    "key: value",       # colon
    "line1\nline2",     # newline
    "  padded  ",       # surrounding whitespace
    "",                 # empty
    "héllo wörld",      # unicode
    'has "quotes"',     # embedded quotes
])
def test_special_string_round_trip(value):
    rt({"k": value})


# --------------------------------------------------------------------------- #
# decode edge cases
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("text", ["", "   ", "\n\n"])
def test_decode_empty_returns_none(text):
    assert json_to_toon.decode(text) is None


# --------------------------------------------------------------------------- #
# File helpers
# --------------------------------------------------------------------------- #

def test_encode_decode_file_round_trip(tmp_path):
    data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}], "count": 2}
    json_path = tmp_path / "data.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")

    json_to_toon.encode_file(json_path)          # default -> data.toon
    toon_path = tmp_path / "data.toon"
    assert toon_path.exists()

    json_to_toon.decode_file(toon_path, tmp_path / "restored.json")
    restored = json.loads((tmp_path / "restored.json").read_text(encoding="utf-8"))
    assert restored == data


def test_encode_file_creates_output_directory(tmp_path):
    json_path = tmp_path / "in.json"
    json_path.write_text(json.dumps({"a": 1}), encoding="utf-8")
    out = tmp_path / "nested" / "dir" / "out.toon"
    json_to_toon.encode_file(json_path, out)
    assert out.exists()


def test_encode_file_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        json_to_toon.encode_file(tmp_path / "does_not_exist.json")


def test_encode_file_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json}", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        json_to_toon.encode_file(bad)
