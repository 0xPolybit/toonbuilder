<p align="center">
    <img src="https://raw.githubusercontent.com/0xPolybit/toonbuilder/main/banner.png" alt="toonbuilder banner" height="250">
</p>

<h1 align="center">toonbuilder</h1>

<p align="center">
    Convert JSON, XML, and TOML data to <strong>TOON</strong> — a schema-aware, token-efficient data format for LLM prompts — and back.
</p>

<p align="center">
    <a href="https://pypi.org/project/toonbuilder/"><img src="https://img.shields.io/pypi/v/toonbuilder.svg?color=blue" alt="PyPI version"></a>
    <a href="https://pypi.org/project/toonbuilder/"><img src="https://img.shields.io/pypi/pyversions/toonbuilder.svg" alt="Python versions"></a>
    <a href="https://github.com/0xPolybit/toonbuilder/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
    <a href="https://pypi.org/project/toonbuilder/"><img src="https://img.shields.io/pypi/dm/toonbuilder.svg?color=orange" alt="Downloads"></a>
    <a href="https://github.com/0xPolybit/toonbuilder/stargazers"><img src="https://img.shields.io/github/stars/0xPolybit/toonbuilder.svg?style=social" alt="GitHub stars"></a>
</p>

> [!NOTE]
> The **TOON** format was created by [Johann Schopplich](https://github.com/toon-format/toon), and an official Python implementation is available at [toon-format/toon-python](https://github.com/toon-format/toon-python). `toonbuilder` is an independent implementation that additionally provides first-class **XML** and **TOML** conversion.

---

## Table of Contents

- [Why TOON?](#why-toon)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Type Handling](#type-handling)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Contributing](#contributing)
  - [Releasing](#releasing)
- [FAQ](#faq)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Why TOON?

**TOON (Token-Oriented Object Notation)** is a compact, human-readable data format designed to minimize token usage in Large Language Model (LLM) prompts while preserving full compatibility with the JSON data model.

When working with LLMs, every token counts — for both cost and context-window limits. Traditional formats like JSON and XML are verbose and token-expensive. TOON keeps the same information in a fraction of the tokens.

<table>
<tr>
<th>JSON (verbose)</th>
<th>TOON (compact)</th>
</tr>
<tr>
<td>

```json
{
  "users": [
    { "id": 1, "name": "Alice", "role": "admin", "active": true },
    { "id": 2, "name": "Bob", "role": "user", "active": true },
    { "id": 3, "name": "Charlie", "role": "user", "active": false }
  ]
}
```

</td>
<td>

```toon
users[3]{id,name,role,active}:
  1,Alice,admin,true
  2,Bob,user,true
  3,Charlie,user,false
```

</td>
</tr>
</table>

### Key Benefits

- **~40% fewer tokens** than JSON, with the largest savings on tabular data.
- **Higher retrieval accuracy** — in multi-model benchmarks TOON reached 73.9% accuracy versus JSON's 69.7%.
- **Lossless JSON round-trips** — types are preserved in both directions (see [Type Handling](#type-handling)).
- **LLM-friendly schema** — explicit array lengths (`[N]`) and field headers (`{fields}`) give models clear structure to parse.
- **Tabular optimization** — uniform arrays of objects collapse into CSV-style rows.
- **Human-readable** — YAML-like indentation keeps output easy to read and debug.

### When to Use TOON

Reach for TOON when you have large, uniform datasets (database records, API responses), arrays of objects with consistent fields, or token-limited LLM contexts where every token matters.

Stick with native JSON/XML for deeply nested, non-uniform structures with low tabular eligibility, or when an existing system requires native compatibility.

For the format details, see the [official TOON specification](https://github.com/toon-format/spec).

## Features

| | |
|---|---|
| **Three formats** | Convert JSON, XML, and TOML to TOON and back |
| **Lossless JSON** | Full bidirectional conversion with type preservation |
| **Minimal dependencies** | JSON/XML use only the standard library; TOML uses `tomllib` (Python 3.11+) or the optional `toml` package |
| **Tabular optimization** | Automatically detects and collapses uniform arrays of scalar objects |
| **Flexible indentation** | Any `indent_str` (spaces or tabs) encodes *and* decodes correctly |
| **File helpers** | Read/write files directly; output directories are created automatically |
| **XML attributes** | Preserved via `@attribute` notation |
| **UTF-8 support** | Full Unicode support for international characters |
| **Path-friendly** | Accepts both `str` and `pathlib.Path` paths |

## Installation

Install the latest release from [PyPI](https://pypi.org/project/toonbuilder/):

```bash
pip install toonbuilder
```

To include the optional TOML serialization support:

```bash
pip install "toonbuilder[toml]"
```

### Requirements

- **Python 3.7+**
- JSON and XML conversion require **no external dependencies** (standard library only).
- TOML conversion parses with the standard-library `tomllib` on **Python 3.11+**. On older Pythons, or to serialize TOON *back* to TOML, install the optional `toml` package (`pip install "toonbuilder[toml]"`).

### Install from Source

```bash
git clone https://github.com/0xPolybit/toonbuilder.git
cd toonbuilder
pip install -e ".[test]"
```

## Quick Start

### JSON

```python
from toonbuilder import json_to_toon

data = {
    "users": [
        {"id": 1, "name": "Alice", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "user"},
    ]
}

toon = json_to_toon.encode(data)
print(toon)
# users[2]{id,name,role}:
#   1,Alice,admin
#   2,Bob,user

restored = json_to_toon.decode(toon)   # -> back to the original dict
```

### XML

```python
from toonbuilder import xml_to_toon

xml = """
<users>
    <user><id>1</id><name>Alice</name><role>admin</role></user>
    <user><id>2</id><name>Bob</name><role>user</role></user>
</users>
"""

toon = xml_to_toon.encode(xml)
print(toon)
# users:
#   user[2]{id,name,role}:
#     1,Alice,admin
#     2,Bob,user

xml_out = xml_to_toon.decode(toon)     # -> XML string
```

### TOML

```python
from toonbuilder import toml_to_toon

toml_text = """
title = "Example"

[[servers]]
ip = "10.0.0.1"
role = "frontend"

[[servers]]
ip = "10.0.0.2"
role = "backend"
"""

toon = toml_to_toon.encode(toml_text)
print(toon)
# title: Example
# servers[2]{ip,role}:
#   10.0.0.1,frontend
#   10.0.0.2,backend

toml_out = toml_to_toon.decode(toon)   # requires the optional `toml` package
```

> [!TIP]
> `toml_to_toon.encode` works out of the box on Python 3.11+ (via `tomllib`). Decoding TOON back to TOML — and encoding on older Pythons — requires the optional `toml` package.

### File Conversion

```python
from toonbuilder import json_to_toon, xml_to_toon

json_to_toon.encode_file("input.json", "output.toon")
json_to_toon.decode_file("output.toon", "restored.json")

xml_to_toon.encode_file("input.xml", "output.toon")
xml_to_toon.decode_file("output.toon", "restored.xml")
```

## Usage

### Converting Python Objects

Encode any JSON-compatible Python object directly:

```python
from toonbuilder import json_to_toon

data = {
    "name": "Project Alpha",
    "version": "1.0.0",
    "dependencies": ["numpy", "pandas", "scipy"],
    "config": {"debug": True, "timeout": 30},
}

print(json_to_toon.encode(data))
# name: Project Alpha
# version: 1.0.0
# dependencies[3]: numpy,pandas,scipy
# config:
#   debug: true
#   timeout: 30
```

### Working with Files

**Automatic extension handling** — omit the output path and `toonbuilder` derives it from the input filename:

```python
from toonbuilder import json_to_toon, xml_to_toon

json_to_toon.encode_file("data.json")   # -> data.toon
xml_to_toon.decode_file("data.toon")    # -> data.xml
```

**Custom output paths** — nested directories are created automatically:

```python
json_to_toon.encode_file("input.json", "build/output/converted.toon")
```

**Custom indentation** — the decoder auto-detects the indentation used on encode:

```python
json_to_toon.encode_file("data.json", "data.toon", indent_str="\t")   # tabs
toon = json_to_toon.encode(data, indent_str="    ")                    # 4 spaces
```

### Error Handling

```python
from toonbuilder import json_to_toon
import json

try:
    json_to_toon.encode_file("nonexistent.json")
except FileNotFoundError as err:
    print(f"Missing file: {err}")

try:
    json_to_toon.encode_file("invalid.json")
except json.JSONDecodeError as err:
    print(f"Invalid JSON: {err}")
```

## Type Handling

To guarantee a **lossless JSON round-trip**, string values that would otherwise be read back as a different type are automatically quoted:

```python
from toonbuilder import json_to_toon

data = {"zip": "01234", "version": "1.0", "flag": "true"}
toon = json_to_toon.encode(data)
# zip: "01234"
# version: "1.0"
# flag: "true"

json_to_toon.decode(toon) == data   # True — types are preserved
```

Because **XML** is inherently untyped (all element text is a string), leaf text is *coerced* to a number or boolean when unambiguous. This keeps tabular output compact (`1,Alice` rather than `"1",Alice`) but is intentionally lossy for values such as `007` (which becomes `7`). Use the JSON module when exact string preservation matters.

## API Reference

All three modules share the same four-function surface: `encode`, `decode`, `encode_file`, and `decode_file`.

### `json_to_toon`

| Function | Description |
|---|---|
| `encode(data, indent_level=0, indent_str="  ")` | Encode a Python object (dict, list, or scalar) to a TOON string. |
| `decode(toon_text)` | Decode a TOON string back to a Python object. |
| `encode_file(json_file_path, toon_file_path=None, indent_str="  ")` | Read a JSON file, write TOON. Defaults to the same name with a `.toon` extension. Raises `FileNotFoundError` / `json.JSONDecodeError`. |
| `decode_file(toon_file_path, json_file_path=None, indent=2)` | Read a TOON file, write JSON. Raises `FileNotFoundError` / `ValueError`. |

### `xml_to_toon`

| Function | Description |
|---|---|
| `encode(data, indent_level=0, indent_str="  ")` | Encode XML (`str`, `Element`, or `ElementTree`) to TOON. |
| `decode(toon_text, root_name="root")` | Decode TOON back to an XML string. |
| `encode_file(xml_file_path, toon_file_path=None, indent_str="  ")` | Read an XML file, write TOON. Raises `FileNotFoundError` / `xml.etree.ElementTree.ParseError`. |
| `decode_file(toon_file_path, xml_file_path=None, root_name="root")` | Read a TOON file, write XML. Raises `FileNotFoundError` / `ValueError`. |

### `toml_to_toon`

Parsing uses the standard-library `tomllib` on Python 3.11+; serialization back to TOML (and parsing on older Pythons) requires the optional `toml` package.

| Function | Description |
|---|---|
| `encode(data, indent_level=0, indent_str="  ")` | Encode a TOML string (or parsed mapping) to TOON. Raises `ImportError` if no parser is available. |
| `decode(toon_text)` | Decode TOON back to a TOML string. Raises `ImportError` if `toml` is not installed. |
| `encode_file(toml_file_path, toon_file_path=None, indent_str="  ")` | Read a TOML file, write TOON. |
| `decode_file(toon_file_path, toml_file_path=None)` | Read a TOON file, write TOML. |

**Common parameters**

- `indent_str` (str) — string used for one indentation level (default: two spaces). Tabs and other widths are fully supported and auto-detected on decode.
- `indent_level` (int) — starting indentation level, used internally for recursion (default: `0`).
- `root_name` (str) — name for the XML root element when the TOON data is not already wrapped (default: `"root"`).

## Examples

### API Response

```python
from toonbuilder import json_to_toon

api_response = {
    "status": "success",
    "total": 150,
    "page": 1,
    "results": [
        {"id": 1, "product": "Laptop", "price": 999.99, "stock": 15},
        {"id": 2, "product": "Mouse", "price": 24.99, "stock": 150},
    ],
}

print(json_to_toon.encode(api_response))
# status: success
# total: 150
# page: 1
# results[2]{id,product,price,stock}:
#   1,Laptop,999.99,15
#   2,Mouse,24.99,150
```

### Database Records

```python
from toonbuilder import json_to_toon

records = {
    "company": "Tech Corp",
    "employees": [
        {"id": 1, "name": "Alice", "department": "Engineering", "active": True},
        {"id": 2, "name": "Bob", "department": "Design", "active": False},
    ],
    "metadata": {"updated": "2025-12-04", "version": 2},
}

print(json_to_toon.encode(records))
# company: Tech Corp
# employees[2]{id,name,department,active}:
#   1,Alice,Engineering,true
#   2,Bob,Design,false
# metadata:
#   updated: 2025-12-04
#   version: 2
```

## Contributing

Contributions are welcome! To get started:

1. **Fork** the repository and **create a branch**: `git checkout -b feature/amazing-feature`
2. **Install** the project with test dependencies: `pip install -e ".[test]"`
3. **Make your changes**, keeping to PEP 8 and adding docstrings and type hints.
4. **Run the tests**: `pytest`
5. **Commit and push**, then **open a Pull Request** describing your change.

### Development

```bash
git clone https://github.com/0xPolybit/toonbuilder.git
cd toonbuilder
pip install -e ".[test]"

# Run the test suite
pytest

# Quick sanity check
python -c "from toonbuilder import json_to_toon; print(json_to_toon.encode({'test': 'data'}))"
```

### Releasing

Releases are built and published to PyPI automatically by [`.github/workflows/publish.yml`](.github/workflows/publish.yml) via [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) — no API tokens involved. The package version is derived from the git tag at build time ([setuptools-scm](https://setuptools-scm.readthedocs.io/)), so there's no `version =` field to hand-edit.

To cut a release (maintainers only):

1. Make sure `main` is green and has everything you want to ship.
2. Create and push an annotated tag matching `vMAJOR.MINOR.PATCH`, e.g.:
   ```bash
   git tag -a v0.3.0 -m "v0.3.0"
   git push origin v0.3.0
   ```
3. On GitHub, go to **Releases → Draft a new release**, pick the tag you just pushed, add release notes, and click **Publish release**.
4. Publishing the release triggers the workflow: it builds the sdist/wheel, verifies the metadata with `twine check`, and uploads to PyPI. Watch progress under the repo's **Actions** tab; the package will appear at [pypi.org/project/toonbuilder](https://pypi.org/project/toonbuilder/) within a couple of minutes.

Every push and pull request also runs [`.github/workflows/ci.yml`](.github/workflows/ci.yml), which tests across Python 3.9/3.11/3.12/3.14 and verifies the package builds cleanly — so packaging issues surface long before tag time.

## FAQ

**Is TOON compatible with all JSON data?**
Yes. TOON supports the complete JSON data model, and the JSON module round-trips losslessly.

**Does it have external dependencies?**
JSON and XML conversion use only the Python standard library. TOML parsing needs `tomllib` (bundled with Python 3.11+) or the optional `toml` package.

**Does TOON work with all LLMs?**
TOON is model-agnostic. Benchmarks show improved accuracy across Claude, GPT, Gemini, and Grok models.

**How much token reduction can I expect?**
It depends on your data. Uniform arrays of objects see the largest savings (~40%); deeply nested, non-uniform data sees less. Try your own data in the [TOON Playground](https://toonformat.dev/playground).

**Are XML attributes preserved?**
Yes — attributes are encoded with the `@attribute` prefix, though attribute ordering may change during processing.

## Acknowledgments

- **TOON format** — created and maintained by [Johann Schopplich](https://github.com/toon-format/toon) and the [toon-format](https://github.com/toon-format) team.
- **Community** — thanks to everyone who reports issues and contributes improvements.

### Links

- [TOON Specification](https://github.com/toon-format/spec)
- [TOON Playground](https://toonformat.dev/playground)
- [PyPI Package](https://pypi.org/project/toonbuilder/)
- [Report an Issue](https://github.com/0xPolybit/toonbuilder/issues)

## License

Released under the [MIT License](LICENSE).

---

<p align="center">Made with care for the LLM community.</p>
