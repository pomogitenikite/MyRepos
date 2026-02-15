"""Основной цикл выполнения шагов сценария."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from pywinauto import Desktop

from .launcher import LaunchPlan, ensure_window
from .resolver import resolve_value
from .uia_driver import activate_window, click_left, find_element, find_window, type_text

DEFAULT_ELEMENT_TIMEOUT_MS = 20000
DEFAULT_WAIT_AFTER_MS = 300
DEFAULT_WINDOW_TIMEOUT_MS = 15000


class Player:
    """Простой исполнитель сценариев."""

    def __init__(self, params: Optional[Dict[str, str]] = None, defaults: Optional[Dict[str, Any]] = None):
        self.params = params or {}
        self.defaults = defaults or {}
        self._main_window = None

    def _sleep_after(self, step: Dict[str, Any]) -> None:
        wait_after = step.get("wait_after_ms", DEFAULT_WAIT_AFTER_MS)
        if wait_after:
            time.sleep(wait_after / 1000)

    def run(self, scenario: Dict[str, Any]) -> None:
        """Выполняет шаги сценария по порядку."""
        launch_cfg = scenario.get("launch")

        if launch_cfg:
            args = launch_cfg.get("args")
            if args is not None and not isinstance(args, list):
                raise ValueError("launch.args должен быть списком строк или отсутствовать")
            plan = LaunchPlan(
                window_title_contains=launch_cfg.get("window_title_contains", ""),
                app_path=launch_cfg.get("app_path", ""),
                args=args,
                timeout_ms=launch_cfg.get("timeout_ms", 30000),
                poll_interval_ms=launch_cfg.get("poll_interval_ms", 300),
            )
            self._main_window = ensure_window(plan)

        steps = scenario.get("steps", [])
        for step in steps:
            step_id = step.get("id", "unknown")
            action = step.get("action")
            window_info = step.get("window") or {}
            passport = step.get("target") or {}

            try:
                win = None
                title_contains = window_info.get("top_title_contains")

                # 1) Ждём окно, если оно задано; иначе используем основное окно (если есть)
                if title_contains:
                    win_timeout = step.get("timeout_ms") or DEFAULT_WINDOW_TIMEOUT_MS
                    win = find_window(title_contains, timeout_ms=win_timeout)
                    activate_window(win)
                elif self._main_window is not None:
                    win = self._main_window
                    activate_window(win)

                # 2) WAIT_FOR_WINDOW
                if action == "wait_for_window":
                    if not title_contains:
                        raise ValueError("wait_for_window требует window.title_contains")
                    print(f"[STEP {step_id}] action={action} OK")
                    self._sleep_after(step)
                    continue

                # 3) CLICK / TYPE
                if action in ("click", "type"):
                    element_timeout = step.get("timeout_ms") or DEFAULT_ELEMENT_TIMEOUT_MS

                    # Если окно не задано и нет главного окна — работаем в активном
                    if win is None:
                        win = Desktop(backend="uia").window(title_re = 'ПолигонСофт')
                        if win is None:
                            raise LookupError("Не удалось получить активное окно для поиска элемента.")

                    target = find_element(win, passport, timeout_ms=element_timeout)

                    if action == "click":
                        click_left(target)
                    else:
                        resolved = resolve_value(step.get("value"), self.params) or ""
                        type_text(target, resolved)

                    print(f"[STEP {step_id}] action={action} OK")
                    self._sleep_after(step)
                    continue

                raise ValueError(f"Неизвестное действие: {action}")

            except Exception as exc:
                print(f"[STEP {step_id}] action={action} FAILED: {exc}")
                return
