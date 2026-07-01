"""Tests for toonbuilder.xml_to_toon.

Covers encode/decode plus explicit regressions for the 0.2.0 fixes: no more
double-wrapped tags, attributes preserved on text-bearing elements, and correct
XML reconstruction of repeated (list) elements.
"""

import xml.etree.ElementTree as ET

import pytest

from toonbuilder import xml_to_toon


def canon(xml_string):
    """Whitespace-insensitive canonical form for structural comparison."""
    return ET.canonicalize(xml_string, strip_text=True)


def xml_round_trip(xml_string):
    toon = xml_to_toon.encode(xml_string)
    back = xml_to_toon.decode(toon)
    assert canon(xml_string) == canon(back), f"\n toon: {toon!r}\n back: {back!r}"
    return toon


# --------------------------------------------------------------------------- #
# Encode output shape
# --------------------------------------------------------------------------- #

def test_person_encode():
    xml = "<person><name>Alice</name><age>30</age></person>"
    assert xml_to_toon.encode(xml) == "person:\n  name: Alice\n  age: 30"


def test_users_tabular_encode():
    xml = ("<users><user><id>1</id><name>Alice</name></user>"
           "<user><id>2</id><name>Bob</name></user></users>")
    expected = "users:\n  user[2]{id,name}:\n    1,Alice\n    2,Bob"
    assert xml_to_toon.encode(xml) == expected


# --------------------------------------------------------------------------- #
# Regression: nested single children are no longer double-wrapped
# --------------------------------------------------------------------------- #

def test_no_double_wrapping():
    assert xml_to_toon.encode("<a><b><c>1</c></b></a>") == "a:\n  b:\n    c: 1"


# --------------------------------------------------------------------------- #
# Regression: attributes on text-bearing elements survive
# --------------------------------------------------------------------------- #

def test_attribute_on_text_element_preserved():
    toon = xml_to_toon.encode('<root><price currency="USD">44.95</price></root>')
    assert "@currency" in toon and "USD" in toon
    back = xml_to_toon.decode(toon)
    assert 'currency="USD"' in back
    assert "44.95" in back


# --------------------------------------------------------------------------- #
# Round-trips (structural)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("xml", [
    "<msg>hello world</msg>",
    "<person><name>Alice</name><age>30</age></person>",
    "<a><b><c>1</c></b></a>",
    ('<catalog><book id="bk101"><author>Gambardella</author><price>44.95</price></book>'
     '<book id="bk102"><author>Ralls</author><price>5.95</price></book></catalog>'),
    "<config><debug>true</debug><enabled>false</enabled><timeout>30</timeout></config>",
    "<root><item>1</item><item>2</item><item>3</item></root>",
])
def test_xml_round_trip(xml):
    xml_round_trip(xml)


def test_boolean_text_round_trips_lowercase():
    # coerced to bool then rendered back as lowercase 'true'/'false'
    back = xml_to_toon.decode(xml_to_toon.encode("<x><flag>true</flag></x>"))
    assert "<flag>true</flag>" in canon(back)


# --------------------------------------------------------------------------- #
# Accepting Element / ElementTree inputs
# --------------------------------------------------------------------------- #

def test_encode_accepts_element():
    element = ET.fromstring("<person><name>Alice</name></person>")
    assert xml_to_toon.encode(element) == "person:\n  name: Alice"


def test_encode_accepts_elementtree():
    tree = ET.ElementTree(ET.fromstring("<person><name>Alice</name></person>"))
    assert xml_to_toon.encode(tree) == "person:\n  name: Alice"


# --------------------------------------------------------------------------- #
# File helpers
# --------------------------------------------------------------------------- #

def test_encode_decode_file_round_trip(tmp_path):
    xml = ("<users><user><id>1</id><name>Alice</name></user>"
           "<user><id>2</id><name>Bob</name></user></users>")
    xml_path = tmp_path / "data.xml"
    xml_path.write_text(xml, encoding="utf-8")

    xml_to_toon.encode_file(xml_path)            # -> data.toon
    toon_path = tmp_path / "data.toon"
    assert toon_path.exists()

    xml_to_toon.decode_file(toon_path, tmp_path / "restored.xml")
    restored = (tmp_path / "restored.xml").read_text(encoding="utf-8")
    assert canon(xml) == canon(restored)


def test_encode_file_creates_output_directory(tmp_path):
    xml_path = tmp_path / "in.xml"
    xml_path.write_text("<r><a>1</a></r>", encoding="utf-8")
    out = tmp_path / "nested" / "out.toon"
    xml_to_toon.encode_file(xml_path, out)
    assert out.exists()


def test_encode_file_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        xml_to_toon.encode_file(tmp_path / "nope.xml")
