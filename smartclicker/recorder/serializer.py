from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

import yaml

from .model import Scenario, Step


def _put_if_not_none(d: Dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        d[key] = value


def _step_to_dict(step: Step) -> Dict[str, Any]:
    """Переводит шаг в словарь, пригодный для YAML."""
    data: Dict[str, Any] = {
        "id": step.id,
        "action": step.action.value,
    }

    _put_if_not_none(data, "comment", step.comment)
    _put_if_not_none(data, "timeout_ms", step.timeout_ms)
    _put_if_not_none(data, "value", step.value)

    if step.window is not None:
        data["window"] = asdict(step.window)

    if step.target is not None:
        data["target"] = asdict(step.target)

    return data


def _scenario_to_dict(scenario: Scenario) -> Dict[str, Any]:
    """Переводит сценарий в словарь для сохранения в YAML."""
    payload: Dict[str, Any] = {
        "name": scenario.name,
        "steps": [_step_to_dict(step) for step in scenario.steps],
    }

    if scenario.params:
        payload["params"] = scenario.params

    return payload


def save_scenario(scenario: Scenario, base_dir: Path | str) -> Path:
    """Сохраняет сценарий в YAML-файл внутри base_dir."""
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    file_path = base_path / f"{scenario.name}.yaml"
    payload = _scenario_to_dict(scenario)

    with file_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)

    return file_path