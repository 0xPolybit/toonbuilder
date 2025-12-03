"""
JSON to TOON format converter.

This module provides functions to encode JSON data to TOON format and decode
TOON format back to JSON. TOON (Token-Oriented Object Notation) is a compact,
human-readable encoding optimized for LLM token efficiency.
"""

import json
from pathlib import Path
from typing import Any, List, Dict, Union, Optional


def encode(data: Any, indent_level: int = 0, indent_str: str = "  ") -> str:
    """
    Convert JSON data to TOON format.
    
    TOON uses indentation-based structure for nested objects (like YAML) and
    CSV-style tabular arrays for uniform data, minimizing tokens while maintaining
    readability and structure.
    
    Args:
        data: The JSON-compatible data to encode (dict, list, str, int, float, bool, None)
        indent_level: Current indentation level (used internally for recursion)
        indent_str: String used for one level of indentation (default: two spaces)
    
    Returns:
        A string containing the TOON-formatted representation of the input data
    
    Examples:
        >>> encode({"name": "Alice", "age": 30})
        'name: Alice\\nage: 30'
        
        >>> encode({"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]})
        'users[2]{id,name}:\\n  1,Alice\\n  2,Bob'
        
        >>> encode({"tags": ["python", "json", "toon"]})
        'tags[3]: python,json,toon'
    """
    indent = indent_str * indent_level
    
    if data is None:
        return "null"
    elif isinstance(data, bool):
        return "true" if data else "false"
    elif isinstance(data, (int, float)):
        return str(data)
    elif isinstance(data, str):
        # Quote strings if they contain special characters, commas, or colons
        if _needs_quoting(data):
            return json.dumps(data)
        return data
    elif isinstance(data, dict):
        return _encode_object(data, indent_level, indent_str)
    elif isinstance(data, list):
        return _encode_array(data, indent_level, indent_str)
    else:
        return str(data)


def _needs_quoting(s: str) -> bool:
    """Check if a string needs to be quoted in TOON format."""
    if not s:
        return True
    special_chars = [',', ':', '\n', '\r', '\t']
    return any(char in s for char in special_chars) or s.strip() != s


def _encode_object(obj: Dict[str, Any], indent_level: int, indent_str: str) -> str:
    """Encode a dictionary as a TOON object."""
    if not obj:
        return "{}"
    
    indent = indent_str * indent_level
    lines = []
    
    for key, value in obj.items():
        if isinstance(value, dict):
            # Nested object
            if value:
                lines.append(f"{indent}{key}:")
                nested = _encode_object(value, indent_level + 1, indent_str)
                lines.append(nested)
            else:
                lines.append(f"{indent}{key}: {{}}")
        elif isinstance(value, list):
            # Check if this is a tabular array (list of uniform objects)
            if _is_tabular_array(value):
                encoded = _encode_tabular_array(key, value, indent_level, indent_str)
                lines.append(encoded)
            else:
                # Non-tabular array
                encoded = _encode_non_tabular_array(key, value, indent_level, indent_str)
                lines.append(encoded)
        else:
            # Simple key-value pair
            encoded_value = encode(value, 0, indent_str)
            lines.append(f"{indent}{key}: {encoded_value}")
    
    return '\n'.join(lines)


def _is_tabular_array(arr: List[Any]) -> bool:
    """Check if an array is tabular (list of uniform dictionaries)."""
    if not arr or not isinstance(arr[0], dict):
        return False
    
    # Check if all elements are dicts with the same keys
    first_keys = set(arr[0].keys())
    return all(isinstance(item, dict) and set(item.keys()) == first_keys for item in arr)


def _encode_tabular_array(key: str, arr: List[Dict], indent_level: int, indent_str: str) -> str:
    """Encode a uniform array of objects in tabular format."""
    indent = indent_str * indent_level
    row_indent = indent_str * (indent_level + 1)
    
    if not arr:
        return f"{indent}{key}[0]:"
    
    # Get field names from first object
    fields = list(arr[0].keys())
    field_str = ','.join(fields)
    
    # Header line
    lines = [f"{indent}{key}[{len(arr)}]{{{field_str}}}:"]
    
    # Data rows
    for item in arr:
        values = []
        for field in fields:
            value = item.get(field)
            encoded = encode(value, 0, indent_str)
            values.append(encoded)
        lines.append(f"{row_indent}{','.join(values)}")
    
    return '\n'.join(lines)


def _encode_non_tabular_array(key: str, arr: List[Any], indent_level: int, indent_str: str) -> str:
    """Encode a non-tabular array (simple values or mixed types)."""
    indent = indent_str * indent_level
    
    if not arr:
        return f"{indent}{key}[0]:"
    
    # Check if all elements are simple primitives
    if all(isinstance(item, (str, int, float, bool, type(None))) for item in arr):
        # Simple array on one line
        values = [encode(item, 0, indent_str) for item in arr]
        return f"{indent}{key}[{len(arr)}]: {','.join(values)}"
    else:
        # Complex array with nested structures
        lines = [f"{indent}{key}[{len(arr)}]:"]
        for item in arr:
            if isinstance(item, (dict, list)):
                encoded = encode(item, indent_level + 1, indent_str)
                lines.append(encoded)
            else:
                row_indent = indent_str * (indent_level + 1)
                lines.append(f"{row_indent}{encode(item, 0, indent_str)}")
        return '\n'.join(lines)


def _encode_array(arr: List[Any], indent_level: int, indent_str: str) -> str:
    """Encode a top-level array."""
    if not arr:
        return "[]"
    
    # For top-level arrays, we need to handle them specially
    if _is_tabular_array(arr):
        indent = indent_str * indent_level
        row_indent = indent_str * (indent_level + 1)
        
        fields = list(arr[0].keys())
        field_str = ','.join(fields)
        
        lines = [f"[{len(arr)}]{{{field_str}}}:"]
        for item in arr:
            values = [encode(item.get(field), 0, indent_str) for field in fields]
            lines.append(f"{row_indent}{','.join(values)}")
        return '\n'.join(lines)
    else:
        # Simple array or mixed array
        if all(isinstance(item, (str, int, float, bool, type(None))) for item in arr):
            values = [encode(item, 0, indent_str) for item in arr]
            return f"[{len(arr)}]: {','.join(values)}"
        else:
            # Complex array
            lines = [f"[{len(arr)}]:"]
            for item in arr:
                encoded = encode(item, indent_level + 1, indent_str)
                lines.append(encoded)
            return '\n'.join(lines)


def decode(toon_text: str) -> Any:
    """
    Convert TOON format text to JSON data.
    
    Parses TOON-formatted text and reconstructs the original JSON-compatible
    data structure.
    
    Args:
        toon_text: A string containing TOON-formatted data
    
    Returns:
        The decoded data as Python objects (dict, list, str, int, float, bool, None)
    
    Examples:
        >>> decode("name: Alice\\nage: 30")
        {'name': 'Alice', 'age': 30}
        
        >>> decode("users[2]{id,name}:\\n  1,Alice\\n  2,Bob")
        {'users': [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]}
        
        >>> decode("tags[3]: python,json,toon")
        {'tags': ['python', 'json', 'toon']}
    
    Raises:
        ValueError: If the TOON format is invalid or cannot be parsed
    """
    if not toon_text or not toon_text.strip():
        return None
    
    lines = toon_text.split('\n')
    result, _ = _parse_lines(lines, 0, 0)
    return result


def _parse_lines(lines: List[str], start_idx: int, base_indent: int) -> tuple:
    """
    Parse TOON lines starting from start_idx with base indentation level.
    
    Returns (parsed_value, next_line_index)
    """
    if start_idx >= len(lines):
        return None, start_idx
    
    # Check if this is a top-level array
    first_line = lines[start_idx].strip()
    if first_line.startswith('[') and ':' in first_line:
        return _parse_top_level_array(lines, start_idx)
    
    # Otherwise, parse as object
    result = {}
    idx = start_idx
    
    while idx < len(lines):
        line = lines[idx]
        if not line.strip():
            idx += 1
            continue
        
        indent = _get_indent_level(line)
        
        # If indent is less than base, we're done with this level
        if indent < base_indent:
            break
        
        # Only process lines at our exact indent level
        if indent > base_indent:
            idx += 1
            continue
        
        line_content = line.strip()
        
        # Parse key-value or array declaration
        if ':' in line_content:
            key, rest = line_content.split(':', 1)
            key = key.strip()
            rest = rest.strip()
            
            # Check if key has array declaration
            if '[' in key and ']' in key:
                # Array
                array_name, array_info = key.split('[', 1)
                array_name = array_name.strip()
                
                if '{' in array_info:
                    # Tabular array
                    value, idx = _parse_tabular_array(lines, idx, indent)
                    result[array_name] = value
                else:
                    # Simple array
                    value, idx = _parse_simple_array(lines, idx, rest, indent)
                    result[array_name] = value
            elif not rest:
                # Nested object or array
                value, idx = _parse_lines(lines, idx + 1, indent + 1)
                result[key] = value
            else:
                # Simple value
                result[key] = _parse_value(rest)
                idx += 1
        else:
            idx += 1
    
    return result, idx


def _parse_top_level_array(lines: List[str], start_idx: int) -> tuple:
    """Parse a top-level array (starts with [N])."""
    first_line = lines[start_idx].strip()
    
    # Extract length and check for fields
    if '{' in first_line:
        # Tabular array
        return _parse_tabular_array(lines, start_idx, 0)
    else:
        # Simple array
        rest = first_line.split(':', 1)[1].strip() if ':' in first_line else ""
        return _parse_simple_array(lines, start_idx, rest, 0)


def _parse_tabular_array(lines: List[str], start_idx: int, base_indent: int) -> tuple:
    """Parse a tabular array with field headers."""
    header_line = lines[start_idx].strip()
    
    # Extract fields from {field1,field2,...}
    fields_start = header_line.index('{')
    fields_end = header_line.index('}')
    fields_str = header_line[fields_start + 1:fields_end]
    fields = [f.strip() for f in fields_str.split(',')]
    
    # Extract length
    length_start = header_line.index('[')
    length_end = header_line.index(']')
    expected_length = int(header_line[length_start + 1:length_end])
    
    # Parse data rows
    result = []
    idx = start_idx + 1
    row_indent = base_indent + 1
    
    while idx < len(lines) and len(result) < expected_length:
        line = lines[idx]
        if not line.strip():
            idx += 1
            continue
        
        indent = _get_indent_level(line)
        if indent < row_indent:
            break
        
        if indent == row_indent:
            values = _parse_csv_line(line.strip())
            if len(values) == len(fields):
                row_dict = {fields[i]: _parse_value(values[i]) for i in range(len(fields))}
                result.append(row_dict)
        
        idx += 1
    
    return result, idx


def _parse_simple_array(lines: List[str], start_idx: int, rest: str, base_indent: int) -> tuple:
    """Parse a simple array (primitives or inline values)."""
    if rest:
        # Inline array
        values = _parse_csv_line(rest)
        return [_parse_value(v) for v in values], start_idx + 1
    else:
        # Multi-line array
        result = []
        idx = start_idx + 1
        item_indent = base_indent + 1
        
        while idx < len(lines):
            line = lines[idx]
            if not line.strip():
                idx += 1
                continue
            
            indent = _get_indent_level(line)
            if indent < item_indent:
                break
            
            if indent == item_indent:
                result.append(_parse_value(line.strip()))
            
            idx += 1
        
        return result, idx


def _parse_csv_line(line: str) -> List[str]:
    """Parse a CSV-style line, respecting quoted strings."""
    values = []
    current = []
    in_quotes = False
    i = 0
    
    while i < len(line):
        char = line[i]
        
        if char == '"':
            if in_quotes and i + 1 < len(line) and line[i + 1] == '"':
                # Escaped quote
                current.append('"')
                i += 2
                continue
            else:
                in_quotes = not in_quotes
                current.append(char)
                i += 1
        elif char == ',' and not in_quotes:
            values.append(''.join(current).strip())
            current = []
            i += 1
        else:
            current.append(char)
            i += 1
    
    # Add last value
    if current or line.endswith(','):
        values.append(''.join(current).strip())
    
    return values


def _parse_value(value_str: str) -> Any:
    """Parse a string value into appropriate Python type."""
    value_str = value_str.strip()
    
    if not value_str:
        return ""
    
    # Check for quoted string
    if value_str.startswith('"') and value_str.endswith('"'):
        return json.loads(value_str)
    
    # Check for special values
    if value_str == "null":
        return None
    elif value_str == "true":
        return True
    elif value_str == "false":
        return False
    
    # Try to parse as number
    try:
        if '.' in value_str:
            return float(value_str)
        else:
            return int(value_str)
    except ValueError:
        # Return as string
        return value_str


def _get_indent_level(line: str) -> int:
    """Calculate the indentation level of a line (assuming 2 spaces per level)."""
    if not line:
        return 0
    
    spaces = len(line) - len(line.lstrip(' '))
    return spaces // 2


def encode_file(json_file_path: Union[str, Path], toon_file_path: Optional[Union[str, Path]] = None, 
                indent_str: str = "  ") -> None:
    """
    Read a JSON file, encode its contents to TOON format, and write to a .toon file.
    
    Args:
        json_file_path: Path to the input JSON file
        toon_file_path: Path to the output TOON file. If not provided, will use the
                       same name as the input file with .toon extension
        indent_str: String used for one level of indentation (default: two spaces)
    
    Examples:
        >>> encode_file("data.json", "data.toon")
        # Reads data.json and writes TOON format to data.toon
        
        >>> encode_file("config.json")
        # Reads config.json and writes TOON format to config.toon
    
    Raises:
        FileNotFoundError: If the input JSON file does not exist
        JSONDecodeError: If the input file contains invalid JSON
        IOError: If there are issues reading or writing files
    """
    json_path = Path(json_file_path)
    
    # Validate input file exists
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")
    
    # Determine output path
    if toon_file_path is None:
        toon_path = json_path.with_suffix('.toon')
    else:
        toon_path = Path(toon_file_path)
    
    # Read JSON file
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in file {json_file_path}: {e.msg}",
            e.doc, e.pos
        )
    
    # Encode to TOON format
    toon_content = encode(data, indent_str=indent_str)
    
    # Write to TOON file
    with open(toon_path, 'w', encoding='utf-8') as f:
        f.write(toon_content)


def decode_file(toon_file_path: Union[str, Path], json_file_path: Optional[Union[str, Path]] = None,
                indent: int = 2) -> None:
    """
    Read a TOON file, decode its contents to JSON format, and write to a .json file.
    
    Args:
        toon_file_path: Path to the input TOON file
        json_file_path: Path to the output JSON file. If not provided, will use the
                       same name as the input file with .json extension
        indent: Number of spaces for JSON indentation (default: 2)
    
    Examples:
        >>> decode_file("data.toon", "data.json")
        # Reads data.toon and writes JSON format to data.json
        
        >>> decode_file("config.toon")
        # Reads config.toon and writes JSON format to config.json
    
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
    if json_file_path is None:
        json_path = toon_path.with_suffix('.json')
    else:
        json_path = Path(json_file_path)
    
    # Read TOON file
    with open(toon_path, 'r', encoding='utf-8') as f:
        toon_content = f.read()
    
    # Decode from TOON format
    try:
        data = decode(toon_content)
    except Exception as e:
        raise ValueError(f"Invalid TOON format in file {toon_file_path}: {str(e)}")
    
    # Write to JSON file
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
