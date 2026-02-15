from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class StepAction(str, Enum):
    """Типы действий сценария."""

    CLICK = "click"
    TYPE = "type"


@dataclass
class WindowContext:
    """Контекст окна, в котором выполняется шаг."""

    top_title_contains: Optional[str] = None


@dataclass
class UIAPassport:
    """Описание UI-элемента и его окружения."""

    automation_id: Optional[str] = None
    name: Optional[str] = None
    control_type: Optional[str] = None
    class_name: Optional[str] = None
    path: List[Dict[str, Optional[str]]] = field(default_factory=list)


@dataclass
class Step:
    """Отдельный шаг сценария."""

    id: str
    action: StepAction
    window: Optional[WindowContext] = None
    target: Optional[UIAPassport] = None
    value: Optional[str] = None
    comment: Optional[str] = None
    timeout_ms: Optional[int] = None


@dataclass
class Scenario:
    """Сценарий записи действий."""

    name: str
    steps: List[Step] = field(default_factory=list)
    params: List[str] = field(default_factory=list)
