"""Загрузка YAML-сценариев для Player."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_scenario(path: str | Path) -> Dict[str, Any]:
    """Читает YAML-файл сценария и возвращает словарь."""

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Не найден файл сценария: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("Содержимое сценария должно быть словарём (YAML map).")

    validate_scenario_dict(data)
    return data


def validate_scenario_dict(data: Dict[str, Any]) -> None:
    """Проверяет минимальные поля сценария."""

    if "name" not in data or not data["name"]:
        raise ValueError("Сценарий должен содержать поле 'name'.")

    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("Сценарий должен содержать непустой список 'steps'.")

    for idx, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"Шаг #{idx} должен быть словарём.")
        if not step.get("id"):
            raise ValueError(f"Шаг #{idx} не имеет поля 'id'.")
        if not step.get("action"):
            raise ValueError(f"Шаг #{idx} не имеет поля 'action'.")
