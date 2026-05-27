"""Shared test-lab network values.

Loads a gitignored local config when present, otherwise falls back to the
committed example file with placeholder values.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).with_name("lab_test_config.yaml")
_EXAMPLE_PATH = Path(__file__).with_name("lab_test_config.example.yaml")


def _load_config() -> dict:
    source = _CONFIG_PATH if _CONFIG_PATH.exists() else _EXAMPLE_PATH
    data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    return data.get("network", {})


_NETWORK = _load_config()

CALLBACK_INTERNAL_IP = _NETWORK["callback_internal_ip"]
CALLBACK_ALT_IP = _NETWORK["callback_alt_ip"]
CALLBACK_SECONDARY_IP = _NETWORK["callback_secondary_ip"]
CALLBACK_EXTERNAL_IP = _NETWORK["callback_external_ip"]
MYTHIC_SERVER_URL = _NETWORK["mythic_server_url"]
MYTHIC_CALLBACK_HOST = _NETWORK["mythic_callback_host"]
UNC_SHARE = _NETWORK["unc_share"]
UNC_OTHER_SHARE = _NETWORK["unc_other_share"]
UNC_MISSING_SHARE = _NETWORK["unc_missing_share"]
