"""
toonbuilder.

Convert JSON, XML, and TOML data to TOON — a schema-aware, token-efficient
data format for LLM prompts — and back.
"""

from . import json_to_toon, toml_to_toon, xml_to_toon

__version__ = "0.2.0"
__author__ = "Polybit"
__credits__ = "Johann Schopplich"

__all__ = ["json_to_toon", "xml_to_toon", "toml_to_toon"]
