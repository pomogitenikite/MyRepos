"""Модуль запуска/подключения к приложению."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from .launch_strategies import launch_by_exec, try_attach_window, wait_for_window
from .window_utils import safe_restore_and_activate


@dataclass
class LaunchPlan:
    """Параметры запуска приложения."""

    window_title_contains: str
    app_path: str
    args: Optional[List[str]] = None
    timeout_ms: int = 30000
    poll_interval_ms: int = 300


def ensure_window(plan: LaunchPlan) -> Any:
    """Гарантирует наличие окна приложения."""

    if not plan.window_title_contains:
        raise ValueError("LaunchPlan.window_title_contains не должен быть пустым")
    if not plan.app_path:
        raise ValueError("LaunchPlan.app_path не должен быть пустым")

    win = try_attach_window(plan.window_title_contains)
    if win:
        safe_restore_and_activate(win)
        return win
    launch_by_exec(plan.app_path, plan.args)
    win = wait_for_window(plan.window_title_contains, plan.timeout_ms, plan.poll_interval_ms)
    if win:
        safe_restore_and_activate(win)
        return win

    raise LookupError(
        f"Не удалось найти окно '{plan.window_title_contains}' "
        f"после запуска '{plan.app_path}' за {plan.timeout_ms} мс"
    )
