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
    
    # Convert XML element to dictionary structure
    dict_data = _xml_to_dict(root)
    
    # Use json_to_toon encoding logic
    from . import json_to_toon
    return json_to_toon.encode(dict_data, indent_level, indent_str)


def _xml_to_dict(element: ET.Element) -> Any:
    """
    Convert an XML element to a dictionary structure.
    
    Handles:
    - Elements with text content -> string values
    - Elements with attributes -> included in dict
    - Elements with children -> nested dicts or lists
    - Repeated child elements -> lists
    """
    result: Dict[str, Any] = {}
    
    # Add attributes with @ prefix
    if element.attrib:
        for key, value in element.attrib.items():
            result[f"@{key}"] = value
    
    # Group children by tag name
    children_by_tag: Dict[str, List[ET.Element]] = {}
    for child in element:
        tag = child.tag
        if tag not in children_by_tag:
            children_by_tag[tag] = []
        children_by_tag[tag].append(child)
    
    # Process children
    for tag, children in children_by_tag.items():
        if len(children) == 1:
            # Single child
            child = children[0]
            child_dict = _xml_to_dict(child)
            
            # If child has no children and no attributes, use text directly
            if isinstance(child_dict, dict) and len(child_dict) == 1 and '#text' in child_dict:
                result[tag] = child_dict['#text']
            else:
                result[tag] = child_dict
        else:
            # Multiple children with same tag -> array
            result[tag] = [_xml_to_dict(child) for child in children]
    
    # Add text content
    if element.text and element.text.strip():
        text = element.text.strip()
        if not children_by_tag:
            # Leaf node with only text
            return text
        else:
            # Mixed content
            result['#text'] = text
    
    # If we have a root element name, wrap it
    if not result:
        return None
    
    return {element.tag: result} if result else element.tag


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
    from . import json_to_toon
    dict_data = json_to_toon.decode(toon_text)
    
    if dict_data is None:
        return f"<{root_name}/>"
    
    # Convert dictionary to XML
    root = _dict_to_xml(dict_data, root_name)
    
    # Convert to string with pretty formatting
    return _prettify_xml(root)


def _dict_to_xml(data: Any, tag_name: str = "item") -> ET.Element:
    """
    Convert a dictionary structure to an XML element.
    
    Handles:
    - Dicts -> nested elements
    - Lists -> repeated child elements
    - Primitives -> text content
    - @attributes -> XML attributes
    """
    if isinstance(data, dict):
        # Check if there's a single key that should be the root
        if len(data) == 1:
            key = list(data.keys())[0]
            if not key.startswith('@') and not key.startswith('#'):
                return _dict_to_xml(data[key], key)
        
        element = ET.Element(tag_name)
        
        # Process attributes first
        attributes = {}
        regular_keys = {}
        text_content = None
        
        for key, value in data.items():
            if key.startswith('@'):
                # Attribute
                attr_name = key[1:]
                attributes[attr_name] = str(value)
            elif key == '#text':
                # Text content
                text_content = str(value)
            else:
                regular_keys[key] = value
        
        # Set attributes
        for attr, val in attributes.items():
            element.set(attr, val)
        
        # Set text content if present and no child elements
        if text_content and not regular_keys:
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
            element.text = str(data)
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
    
    # Write to TOON file
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
    
    # Write to XML file
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(xml_content)
