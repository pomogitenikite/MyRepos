"""Подстановка параметров в значения сценария."""

from __future__ import annotations

import re
from typing import Optional

PARAM_PATTERN = re.compile(r"^\$\{(?P<name>[^}]+)}$")


def extract_param_name(template: str) -> Optional[str]:
    """Возвращает имя параметра из строки вида '${param}'."""

    match = PARAM_PATTERN.match(template)
    if not match:
        return None
    return match.group("name")


def resolve_value(template: Optional[str], params: dict[str, str]) -> Optional[str]:
    """
    Подставляет значение параметра, если template вида ${name}.

    Примеры:
    - resolve_value("${param_001}", {"param_001": "hello"}) -> "hello"
    - resolve_value("plain text", {"param_001": "hello"}) -> "plain text"
    - resolve_value(None, ...) -> None
    """

    if template is None:
        return None

    name = extract_param_name(template)
    if name is None:
        return template

    if name not in params:
        raise KeyError(f"Параметр '{name}' не найден в словаре params.")

    return params[name]
