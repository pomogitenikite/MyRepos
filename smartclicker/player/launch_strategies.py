"""Стратегии: подключиться к окну или запустить приложение."""

from __future__ import annotations

import subprocess
import time
from typing import Any, Optional

from pywinauto import Desktop

def try_attach_window(title_contains: str):
    """Пытается найти существующее окно по подстроке в заголовке."""

    title_contains = title_contains.strip()
    if not title_contains:
        return None

    for win in Desktop(backend="uia").windows():
        if _contains(_window_title(win), title_contains):
            return win

    return None


def _window_title(win: Any) -> str:
    """Возвращает текст заголовка окна (best-effort)."""

    try:
        return win.window_text() or win.element_info.name or ""
    except Exception:
        return ""


def _contains(haystack: str, needle: str) -> bool:
    """Проверяет вхождение needle в haystack без учёта регистра."""

    if not haystack or not needle:
        return False
    return needle.lower() in haystack.lower()


def launch_by_exec(app_path: str, args=None):
    """Запускает процесс приложения."""

    cmd = [app_path] + (args or [])
    try:
        subprocess.Popen(cmd, shell=False)
    except Exception as exc:
        raise RuntimeError(f"Не удалось запустить '{app_path}' с args={args}: {exc}") from exc


def wait_for_window(title_contains: str, timeout_ms: int, poll_interval_ms: int):
    """Ожидает появления окна по заголовку, опрашивая до таймаута."""

    deadline = time.monotonic() + timeout_ms / 1000
    while True:
        win = try_attach_window(title_contains)
        if win:
            return win

        if time.monotonic() >= deadline:
            break
        time.sleep(poll_interval_ms / 1000)

    return None
