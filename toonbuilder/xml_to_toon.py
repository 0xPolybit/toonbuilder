"""
XML to TOON format converter.

This module provides functions to encode XML data to TOON format and decode
TOON format back to XML. TOON (Token-Oriented Object Notation) is a compact,
human-readable encoding optimized for LLM token efficiency.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, List, Dict, Union, Optional
from xml.dom import minidom

from . import json_to_toon


def encode(data: Any, indent_level: int = 0, indent_str: str = "  ") -> str:
    """
    Convert XML data to TOON format.
    
    TOON uses indentation-based structure for nested objects (like YAML) and
    CSV-style tabular arrays for uniform data, minimizing tokens while maintaining
    readability and structure.
    
    Args:
        data: The XML data to encode (string, Element, or ElementTree)
        indent_level: Current indentation level (used internally for recursion)
        indent_str: String used for one level of indentation (default: two spaces)
    
    Returns:
        A string containing the TOON-formatted representation of the input data
    
    Examples:
        >>> xml_str = '<person><name>Alice</name><age>30</age></person>'
        >>> encode(xml_str)
        'person:\\n  name: Alice\\n  age: 30'

        >>> xml_str = '<users><user><id>1</id><name>Alice</name></user><user><id>2</id><name>Bob</name></user></users>'
        >>> encode(xml_str)
        'users:\\n  user[2]{id,name}:\\n    1,Alice\\n    2,Bob'
    """
    # Parse XML if string is provided
    if isinstance(data, str):
        root = ET.fromstring(data)
    elif isinstance(data, ET.ElementTree):
        root = data.getroot()
    else:
        root = data

    if root is None:
        return ""

    # Convert XML element to a dictionary structure, wrapping once under the
    # root tag, then reuse the json_to_toon encoder.
    dict_data = {root.tag: _element_to_value(root)}
    return json_to_toon.encode(dict_data, indent_level, indent_str)


def _coerce_scalar(text: str) -> Any:
    """Coerce XML leaf text into a scalar type where unambiguous.

    XML is untyped (all text), but to keep TOON output compact (and tabular
    arrays clean, e.g. ``1,Alice`` rather than ``"1",Alice``) numeric and
    boolean-looking text is coerced. Note this is intentionally lossy for
    values like ``007`` -> ``7``; everything else is left as a string.
    """
    if text in ("true", "false"):
        return text == "true"
    if json_to_toon._parses_as_number(text):
        return float(text) if '.' in text else int(text)
    return text


def _element_to_value(element: ET.Element) -> Any:
    """
    Convert an XML element to its TOON-friendly *content* (unwrapped).

    The caller is responsible for wrapping the root element under its tag, so
    this returns only the element's value. Handles:
    - Leaf elements (no attributes/children) -> a coerced scalar (or None)
    - Attributes -> ``@name`` keys
    - Child elements -> nested values, repeated tags become lists
    - Mixed content (text alongside children) -> ``#text`` key
    """
    children = list(element)
    text = (element.text or "").strip()

    # Pure leaf: no attributes and no child elements -> a scalar value.
    if not element.attrib and not children:
        return _coerce_scalar(text) if text else None

    result: Dict[str, Any] = {}

    # Attributes, prefixed with @ (kept as raw strings to preserve them exactly).
    for name, value in element.attrib.items():
        result[f"@{name}"] = value

    # Group children by tag: a single child is a value, repeats become a list.
    children_by_tag: Dict[str, List[ET.Element]] = {}
    for child in children:
        children_by_tag.setdefault(child.tag, []).append(child)
    for tag, group in children_by_tag.items():
        if len(group) == 1:
            result[tag] = _element_to_value(group[0])
        else:
            result[tag] = [_element_to_value(child) for child in group]

    # Mixed content: element has attributes/children *and* its own text.
    if text:
        result["#text"] = _coerce_scalar(text)

    return result


def decode(toon_text: str, root_name: str = "root") -> str:
    """
    Convert TOON format text to XML data.
    
    Parses TOON-formatted text and reconstructs XML structure.
    
    Args:
        toon_text: A string containing TOON-formatted data
        root_name: Name for the root XML element if TOON data is not wrapped (default: "root")
    
    Returns:
        A string containing the XML representation of the TOON data
    
    Examples:
        >>> toon = "person:\\n  name: Alice\\n  age: 30"
        >>> decode(toon)
        '<person><name>Alice</name><age>30</age></person>'
        
        >>> toon = "users:\\n  user[2]{id,name}:\\n    1,Alice\\n    2,Bob"
        >>> decode(toon)
        '<users><user><id>1</id><name>Alice</name></user><user><id>2</id><name>Bob</name></user></users>'
    
    Raises:
        ValueError: If the TOON format is invalid or cannot be parsed
    """
    # Decode TOON to dictionary
    dict_data = json_to_toon.decode(toon_text)

    if dict_data is None:
        return f"<{root_name}/>"

    # The encoder wraps everything under the original root tag. Unwrap it once
    # here (using that tag as the element name) so we don't add an extra
    # <root> wrapper; otherwise fall back to root_name.
    if (isinstance(dict_data, dict) and len(dict_data) == 1
            and not next(iter(dict_data)).startswith(('@', '#'))):
        tag = next(iter(dict_data))
        root = _dict_to_xml(dict_data[tag], tag)
    else:
        root = _dict_to_xml(dict_data, root_name)

    # Convert to string with pretty formatting
    return _prettify_xml(root)


def _scalar_to_text(value: Any) -> str:
    """Render a scalar as XML text, using lowercase ``true``/``false`` for bools.

    ``str(True)`` is ``"True"``, which would not survive an XML round-trip, so
    booleans are rendered to match the TOON/XML convention.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _dict_to_xml(data: Any, tag_name: str = "item") -> ET.Element:
    """
    Convert a dictionary structure to an XML element named ``tag_name``.

    Handles:
    - Dicts -> nested elements (one child per key; list values repeat the tag)
    - Lists -> repeated child elements wrapped in a ``tag_name`` container
    - Primitives -> text content
    - @attributes -> XML attributes, #text -> element text
    """
    if isinstance(data, dict):
        element = ET.Element(tag_name)
        
        # Process attributes first
        attributes = {}
        regular_keys = {}
        text_content = None
        
        for key, value in data.items():
            if key.startswith('@'):
                # Attribute
                attr_name = key[1:]
                attributes[attr_name] = _scalar_to_text(value)
            elif key == '#text':
                # Text content
                text_content = _scalar_to_text(value)
            else:
                regular_keys[key] = value
        
        # Set attributes
        for attr, val in attributes.items():
            element.set(attr, val)
        
        # Set text content if present (mixed content keeps text before children)
        if text_content is not None:
            element.text = text_content
        
        # Process child elements
        for key, value in regular_keys.items():
            if isinstance(value, list):
                # Create multiple child elements
                for item in value:
                    child = _dict_to_xml(item, key)
                    element.append(child)
            else:
                # Single child element
                child = _dict_to_xml(value, key)
                element.append(child)
        
        return element
    
    elif isinstance(data, list):
        # If we have a list at the top level, wrap in container
        container = ET.Element(tag_name)
        for item in data:
            child = _dict_to_xml(item, "item")
            container.append(child)
        return container
    
    else:
        # Primitive value
        element = ET.Element(tag_name)
        if data is not None:
            element.text = _scalar_to_text(data)
        return element


def _prettify_xml(element: ET.Element) -> str:
    """Convert XML element to a pretty-printed string."""
    rough_string = ET.tostring(element, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent="  ")
    
    # Remove XML declaration and clean up empty lines
    lines = [line for line in pretty.split('\n') if line.strip() and not line.strip().startswith('<?xml')]
    return '\n'.join(lines)


def encode_file(xml_file_path: Union[str, Path], toon_file_path: Optional[Union[str, Path]] = None, 
                indent_str: str = "  ") -> None:
    """
    Read an XML file, encode its contents to TOON format, and write to a .toon file.
    
    Args:
        xml_file_path: Path to the input XML file
        toon_file_path: Path to the output TOON file. If not provided, will use the
                       same name as the input file with .toon extension
        indent_str: String used for one level of indentation (default: two spaces)
    
    Examples:
        >>> encode_file("data.xml", "data.toon")
        # Reads data.xml and writes TOON format to data.toon
        
        >>> encode_file("config.xml")
        # Reads config.xml and writes TOON format to config.toon
    
    Raises:
        FileNotFoundError: If the input XML file does not exist
        ET.ParseError: If the input file contains invalid XML
        IOError: If there are issues reading or writing files
    """
    xml_path = Path(xml_file_path)
    
    # Validate input file exists
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_file_path}")
    
    # Determine output path
    if toon_file_path is None:
        toon_path = xml_path.with_suffix('.toon')
    else:
        toon_path = Path(toon_file_path)
    
    # Read and parse XML file
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ET.ParseError(f"Invalid XML in file {xml_file_path}: {e}")
    
    # Encode to TOON format
    toon_content = encode(root, indent_str=indent_str)

    # Write to TOON file (creating the output directory if needed)
    toon_path.parent.mkdir(parents=True, exist_ok=True)
    with open(toon_path, 'w', encoding='utf-8') as f:
        f.write(toon_content)


def decode_file(toon_file_path: Union[str, Path], xml_file_path: Optional[Union[str, Path]] = None,
                root_name: str = "root") -> None:
    """
    Read a TOON file, decode its contents to XML format, and write to an .xml file.
    
    Args:
        toon_file_path: Path to the input TOON file
        xml_file_path: Path to the output XML file. If not provided, will use the
                      same name as the input file with .xml extension
        root_name: Name for the root XML element if needed (default: "root")
    
    Examples:
        >>> decode_file("data.toon", "data.xml")
        # Reads data.toon and writes XML format to data.xml
        
        >>> decode_file("config.toon")
        # Reads config.toon and writes XML format to config.xml
    
    Raises:
        FileNotFoundError: If the input TOON file does not exist
        ValueError: If the input file contains invalid TOON format
        IOError: If there are issues reading or writing files
    """
    toon_path = Path(toon_file_path)
    
    # Validate input file exists
    if not toon_path.exists():
        raise FileNotFoundError(f"TOON file not found: {toon_file_path}")
    
    # Determine output path
    if xml_file_path is None:
        xml_path = toon_path.with_suffix('.xml')
    else:
        xml_path = Path(xml_file_path)
    
    # Read TOON file
    with open(toon_path, 'r', encoding='utf-8') as f:
        toon_content = f.read()
    
    # Decode from TOON format to XML
    try:
        xml_content = decode(toon_content, root_name)
    except Exception as e:
        raise ValueError(f"Invalid TOON format in file {toon_file_path}: {str(e)}")
    
    # Write to XML file (creating the output directory if needed)
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(xml_content)
