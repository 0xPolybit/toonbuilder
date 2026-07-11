"""
toonbuilder.

Convert JSON, XML, and TOML data to TOON — a schema-aware, token-efficient
data format for LLM prompts — and back.
"""

from importlib.metadata import PackageNotFoundError, version

from . import json_to_toon, toml_to_toon, xml_to_toon

try:
    __version__ = version("toonbuilder")
except PackageNotFoundError:
    # Package isn't installed (e.g. running straight from a source checkout).
    __version__ = "0.0.0+unknown"

__author__ = "Polybit"
__credits__ = "Johann Schopplich"

__all__ = ["json_to_toon", "xml_to_toon", "toml_to_toon"]
