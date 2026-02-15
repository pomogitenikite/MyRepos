import re
from pathlib import Path

import yaml

PARAM_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def default_scenario(name):
    return {
        "format_version": 2,
        "name": name,
        "params": [],
        "runs": [],
        "windows": {},
        "blocks": [],
    }


def load_scenario(path):
    with Path(path).open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if data.get("format_version") != 2:
        raise ValueError("Only format_version=2 is supported")
    return data


def save_scenario(path, scenario):
    with Path(path).open("w", encoding="utf-8") as fh:
        yaml.safe_dump(scenario, fh, sort_keys=False, allow_unicode=True)


def extract_params(text):
    if not isinstance(text, str):
        return []
    return PARAM_RE.findall(text)


def register_params(scenario, text):
    for name in extract_params(text):
        if name not in scenario["params"]:
            scenario["params"].append(name)


def render_template(value, values):
    if not isinstance(value, str):
        return value
    return PARAM_RE.sub(lambda m: str(values.get(m.group(1), m.group(0))), value)
