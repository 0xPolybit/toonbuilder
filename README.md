<p align="center">
    <img src="https://raw.githubusercontent.com/0xPolybit/toonbuilder/main/banner.png" alt="toonbuilder banner" style="display: block; margin-left: auto; margin-right: auto;margin-top: 15px; margin-bottom: 20px; height: 250px;">
</p>

<h1 align="center" style="text-align: center; font-size: 35px; font-weight: 700;">toonbuilder</h1>

<p align="center" style="text-align: center; font-size: 16px;">Convert JSON and XML files to TOON, a schema-aware data formatting for LLM prompts.</p>

> [!IMPORTANT]
> The original author of the TOON data formatting is xxx and an implementation of a TOON conversion system in Python already exists (https://github.com/toon-format/toon-python). This serves as a more thorough implementation of the package.


## Table of Contents

- [Why Toon?](#why-toon)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## Why Toon?

**TOON (Token-Oriented Object Notation)** is a compact, human-readable data format specifically designed to minimize token usage in Large Language Model (LLM) prompts while maintaining full compatibility with JSON's data model.

### The Problem with Traditional Formats

When working with LLMs, every token counts—both for cost and context window limitations. Traditional data formats like JSON and XML are verbose and token-expensive:

**JSON Example (verbose):**
```json
{
  "users": [
    {
      "id": 1,
      "name": "Alice",
      "role": "admin",
      "active": true
    },
    {
      "id": 2,
      "name": "Bob",
      "role": "user",
      "active": true
    },
    {
      "id": 3,
      "name": "Charlie",
      "role": "user",
      "active": false
    }
  ]
}
```

**TOON Example (compact):**
```toon
users[3]{id,name,role,active}:
  1,Alice,admin,true
  2,Bob,user,true
  3,Charlie,user,false
```

### Key Benefits

- **Approximately 40% token reduction:** TOON uses far fewer tokens than JSON, with the biggest savings for tabular data.
- **Higher LLM retrieval accuracy:** In multi-model benchmarks TOON achieved 73.9% accuracy compared with JSON’s 69.7%.
- **Lossless, bidirectional conversion:** Converts to and from JSON and XML without losing information.
- **LLM-friendly schema:** Explicit array lengths ([N]) and field headers `({fields})` provide clear structure that helps models parse reliably.
- **Tabular optimization:** Uniform arrays of objects are collapsed into CSV-style rows for compactness and efficiency.
- **Human-readable layout:** YAML-like indentation keeps the format easy to read and debug.

### When to Use TOON

TOON excels when you have:
- Large datasets with uniform structures (e.g., database records, API responses)
- Arrays of objects with consistent fields
- Token-limited LLM contexts where every token matters
- Need for both human readability and machine efficiency

### When to Stick with JSON/XML

- Deeply nested, non-uniform structures with low tabular eligibility
- Existing systems that require native JSON/XML compatibility
- Applications where parsing performance is more critical than token efficiency

For more details, see the [official TOON specification](https://github.com/toon-format/spec).

## Installation

Install `toonbuilder` from PyPI using pip:

```bash
pip install toonbuilder
```

Or using pip3:

```bash
pip3 install toonbuilder
```

### Requirements

- Python 3.7 or higher
- No external dependencies required (uses only Python standard library)

### Development Installation

To install from source for development:

```bash
git clone https://github.com/0xPolybit/toonbuilder.git
cd toonbuilder
pip install -e .
```

## Quick Start

### JSON to TOON Conversion

```python
from toonbuilder import json_to_toon

# Convert JSON string to TOON
json_data = {
    "users": [
        {"id": 1, "name": "Alice", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "user"}
    ]
}

toon_output = json_to_toon.encode(json_data)
print(toon_output)
# Output:
# users[2]{id,name,role}:
#   1,Alice,admin
#   2,Bob,user

# Convert TOON back to JSON
original_data = json_to_toon.decode(toon_output)
print(original_data)
```

### XML to TOON Conversion

```python
from toonbuilder import xml_to_toon

# Convert XML string to TOON
xml_string = """
<users>
    <user>
        <id>1</id>
        <name>Alice</name>
        <role>admin</role>
    </user>
    <user>
        <id>2</id>
        <name>Bob</name>
        <role>user</role>
    </user>
</users>
"""

toon_output = xml_to_toon.encode(xml_string)
print(toon_output)

# Convert TOON back to XML
xml_output = xml_to_toon.decode(toon_output)
print(xml_output)
```

### File Conversion

```python
from toonbuilder import json_to_toon, xml_to_toon

# JSON file conversion
json_to_toon.encode_file("input.json", "output.toon")
json_to_toon.decode_file("output.toon", "restored.json")

# XML file conversion
xml_to_toon.encode_file("input.xml", "output.toon")
xml_to_toon.decode_file("output.toon", "restored.xml")
```

## Usage

### Converting Python Data Structures

#### JSON Module

```python
from toonbuilder import json_to_toon

# Encode Python dict/list to TOON string
data = {
    "name": "Project Alpha",
    "version": "1.0.0",
    "dependencies": ["numpy", "pandas", "scipy"],
    "config": {
        "debug": True,
        "timeout": 30
    }
}

toon_string = json_to_toon.encode(data)
print(toon_string)
# Output:
# name: Project Alpha
# version: 1.0.0
# dependencies[3]: numpy,pandas,scipy
# config:
#   debug: true
#   timeout: 30

# Decode TOON string back to Python dict
restored_data = json_to_toon.decode(toon_string)
```

#### XML Module

```python
from toonbuilder import xml_to_toon

# Encode XML string to TOON
xml_data = """<?xml version="1.0"?>
<catalog>
    <book id="bk101">
        <author>Gambardella, Matthew</author>
        <title>XML Developer's Guide</title>
        <price>44.95</price>
    </book>
    <book id="bk102">
        <author>Ralls, Kim</author>
        <title>Midnight Rain</title>
        <price>5.95</price>
    </book>
</catalog>"""

toon_string = xml_to_toon.encode(xml_data)
print(toon_string)

# Decode back to XML
xml_output = xml_to_toon.decode(toon_string)
```

### Working with Files

#### Automatic File Extension Handling

When you don't specify an output file path, `toonbuilder` automatically uses the input filename with the appropriate extension:

```python
from toonbuilder import json_to_toon, xml_to_toon

# These will create data.toon from data.json
json_to_toon.encode_file("data.json")

# These will create data.xml from data.toon
xml_to_toon.decode_file("data.toon")
```

#### Custom Output Paths

```python
# Specify custom output paths
json_to_toon.encode_file("input.json", "output/converted.toon")
xml_to_toon.encode_file("config.xml", "toon_files/config.toon")
```

#### Custom Indentation

```python
# Use tabs instead of spaces
json_to_toon.encode_file("data.json", "data.toon", indent_str="\t")

# Use 4 spaces for indentation
toon_output = json_to_toon.encode(data, indent_str="    ")
```

### Advanced Usage

#### Handling Complex Nested Structures

```python
from toonbuilder import json_to_toon

complex_data = {
    "company": "Tech Corp",
    "employees": [
        {
            "id": 1,
            "name": "Alice Johnson",
            "department": "Engineering",
            "skills": ["Python", "JavaScript", "Go"],
            "salary": 120000,
            "active": True
        },
        {
            "id": 2,
            "name": "Bob Smith",
            "department": "Engineering",
            "skills": ["Java", "Kotlin", "SQL"],
            "salary": 115000,
            "active": True
        },
        {
            "id": 3,
            "name": "Carol White",
            "department": "Design",
            "skills": ["Figma", "Photoshop", "Illustrator"],
            "salary": 95000,
            "active": False
        }
    ],
    "metadata": {
        "updated": "2025-12-04",
        "version": 2
    }
}

# TOON format efficiently handles tabular employee data
toon_output = json_to_toon.encode(complex_data)
print(toon_output)
```

#### Error Handling

```python
from toonbuilder import json_to_toon, xml_to_toon
import json

# Handle missing files
try:
    json_to_toon.encode_file("nonexistent.json")
except FileNotFoundError as e:
    print(f"Error: {e}")

# Handle invalid JSON
try:
    with open("invalid.json", "w") as f:
        f.write("{invalid json content}")
    json_to_toon.encode_file("invalid.json")
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}")

# Handle invalid TOON format
try:
    json_to_toon.decode("malformed [ toon content")
except ValueError as e:
    print(f"Invalid TOON format: {e}")
```

## API Reference

### `json_to_toon` Module

#### `encode(data, indent_level=0, indent_str="  ")`

Convert Python data structures to TOON format.

**Parameters:**
- `data` (Any): Python object to encode (dict, list, str, int, float, bool, None)
- `indent_level` (int): Starting indentation level (default: 0)
- `indent_str` (str): String used for one level of indentation (default: two spaces)

**Returns:** `str` - TOON formatted string

**Example:**
```python
data = {"name": "Alice", "age": 30}
toon_str = json_to_toon.encode(data)
```

#### `decode(toon_text)`

Convert TOON format to Python data structures.

**Parameters:**
- `toon_text` (str): TOON formatted string

**Returns:** `Any` - Python object (dict, list, primitives)

**Example:**
```python
data = json_to_toon.decode("name: Alice\nage: 30")
```

#### `encode_file(json_file_path, toon_file_path=None, indent_str="  ")`

Read JSON file and write TOON output.

**Parameters:**
- `json_file_path` (str | Path): Input JSON file path
- `toon_file_path` (str | Path | None): Output TOON file path (default: same name with .toon extension)
- `indent_str` (str): Indentation string (default: two spaces)

**Raises:**
- `FileNotFoundError`: If input file doesn't exist
- `json.JSONDecodeError`: If input contains invalid JSON

#### `decode_file(toon_file_path, json_file_path=None, indent=2)`

Read TOON file and write JSON output.

**Parameters:**
- `toon_file_path` (str | Path): Input TOON file path
- `json_file_path` (str | Path | None): Output JSON file path (default: same name with .json extension)
- `indent` (int): Number of spaces for JSON indentation (default: 2)

**Raises:**
- `FileNotFoundError`: If input file doesn't exist
- `ValueError`: If input contains invalid TOON format

### `xml_to_toon` Module

#### `encode(data, indent_level=0, indent_str="  ")`

Convert XML data to TOON format.

**Parameters:**
- `data` (str | Element | ElementTree): XML data to encode
- `indent_level` (int): Starting indentation level (default: 0)
- `indent_str` (str): String used for one level of indentation (default: two spaces)

**Returns:** `str` - TOON formatted string

**Example:**
```python
xml_str = "<person><name>Alice</name><age>30</age></person>"
toon_str = xml_to_toon.encode(xml_str)
```

#### `decode(toon_text, root_name="root")`

Convert TOON format to XML string.

**Parameters:**
- `toon_text` (str): TOON formatted string
- `root_name` (str): Name for root element if needed (default: "root")

**Returns:** `str` - XML formatted string

**Example:**
```python
xml_str = xml_to_toon.decode("person:\n  name: Alice\n  age: 30")
```

#### `encode_file(xml_file_path, toon_file_path=None, indent_str="  ")`

Read XML file and write TOON output.

**Parameters:**
- `xml_file_path` (str | Path): Input XML file path
- `toon_file_path` (str | Path | None): Output TOON file path (default: same name with .toon extension)
- `indent_str` (str): Indentation string (default: two spaces)

**Raises:**
- `FileNotFoundError`: If input file doesn't exist
- `xml.etree.ElementTree.ParseError`: If input contains invalid XML

#### `decode_file(toon_file_path, xml_file_path=None, root_name="root")`

Read TOON file and write XML output.

**Parameters:**
- `toon_file_path` (str | Path): Input TOON file path
- `xml_file_path` (str | Path | None): Output XML file path (default: same name with .xml extension)
- `root_name` (str): Name for root element if needed (default: "root")

**Raises:**
- `FileNotFoundError`: If input file doesn't exist
- `ValueError`: If input contains invalid TOON format

## Features

- **Lossless Conversion**: Full bidirectional conversion between JSON/XML and TOON
- **Zero Dependencies**: Uses only Python standard library
- **Type Preservation**: Maintains data types (strings, numbers, booleans, null)
- **Tabular Optimization**: Automatically detects and optimizes uniform arrays
- **Path Objects**: Supports both string paths and `pathlib.Path` objects
- **UTF-8 Support**: Full Unicode support for international characters
- **Pretty Formatting**: Human-readable indentation and structure
- **XML Attributes**: Preserves XML attributes using `@attribute` notation
- **Error Messages**: Clear, descriptive error messages for debugging

## Examples

### Real-World Use Case: API Response

```python
from toonbuilder import json_to_toon

# Typical API response
api_response = {
    "status": "success",
    "total": 150,
    "page": 1,
    "results": [
        {"id": 1, "product": "Laptop", "price": 999.99, "stock": 15},
        {"id": 2, "product": "Mouse", "price": 24.99, "stock": 150},
        {"id": 3, "product": "Keyboard", "price": 79.99, "stock": 45}
    ]
}

# Convert to TOON for LLM prompt
toon_format = json_to_toon.encode(api_response)
print(toon_format)
# Output:
# status: success
# total: 150
# page: 1
# results[3]{id,product,price,stock}:
#   1,Laptop,999.99,15
#   2,Mouse,24.99,150
#   3,Keyboard,79.99,45

# Now you can use this in your LLM prompt with ~40% fewer tokens!
```

### Database Records

```python
from toonbuilder import json_to_toon

# Database query results
db_records = {
    "query": "SELECT * FROM users WHERE active = true",
    "count": 3,
    "records": [
        {"user_id": 101, "username": "alice_dev", "email": "alice@example.com", "created": "2024-01-15", "active": True},
        {"user_id": 102, "username": "bob_admin", "email": "bob@example.com", "created": "2024-02-20", "active": True},
        {"user_id": 103, "username": "carol_user", "email": "carol@example.com", "created": "2024-03-10", "active": True}
    ]
}

# Efficiently encode for LLM analysis
toon_output = json_to_toon.encode(db_records)
```

## Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Add features, fix bugs, or improve documentation
4. **Run tests**: Ensure all tests pass (coming soon)
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Setup

```bash
# Clone the repository
git clone https://github.com/0xPolybit/toonbuilder.git
cd toonbuilder

# Install in development mode
pip install -e .

# Make your changes and test them
python -c "from toonbuilder import json_to_toon; print(json_to_toon.encode({'test': 'data'}))"
```

### Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include type hints where appropriate
- Update README.md if you add new features
- Be respectful and constructive in discussions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **TOON Format Specification**: Thanks to the [toon-format](https://github.com/toon-format/toon) team for creating and maintaining the TOON specification
- **Community**: Thanks to all contributors and users who help improve this library

## Links

- **TOON Specification**: [https://github.com/toon-format/spec](https://github.com/toon-format/spec)
- **TOON Playground**: [https://toonformat.dev/playground](https://toonformat.dev/playground)
- **Report Issues**: [https://github.com/0xPolybit/toonbuilder/issues](https://github.com/0xPolybit/toonbuilder/issues)
- **PyPI Package**: [https://pypi.org/project/toonbuilder/](https://pypi.org/project/toonbuilder/)

## FAQ

**Q: Is TOON compatible with all JSON data?**  
A: Yes! TOON supports the complete JSON data model with lossless conversion.

**Q: Can I use this in production?**  
A: Yes, the library uses only Python's standard library with no external dependencies.

**Q: Does TOON work with all LLMs?**  
A: TOON is designed to be universally compatible with any LLM. Benchmarks show improved accuracy across Claude, GPT, Gemini, and Grok models.

**Q: How much token reduction can I expect?**  
A: It depends on your data structure. Uniform arrays see ~40% reduction, while deeply nested objects may see less benefit. Use the [TOON Playground](https://toonformat.dev/playground) to test your specific data.

**Q: Is XML attribute order preserved?**  
A: XML attributes are preserved during conversion, though Python dictionaries may reorder them during processing.

---

<p align="center">Made with ❤️ for the LLM community</p>