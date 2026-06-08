import os
from pathlib import Path

import yaml


def load_yaml_config(config_path: str = None) -> dict:
    if config_path is None:
        config_path = os.environ.get("CONFIG_YAML_PATH", "config.yaml")

    path = Path(config_path)
    if not path.exists():
        return {}

    with open(path) as f:
        return yaml.safe_load(f) or {}


def get_yaml_setting(key: str, default=None):
    config = load_yaml_config()
    keys = key.split(".")
    value = config
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
    return value if value is not None else default
