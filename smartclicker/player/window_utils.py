"""Хелперы для восстановления и активации окна."""

from __future__ import annotations

from typing import Any


def safe_restore(win: Any) -> None:
    """Пытается восстановить окно, если оно свернуто."""

    is_minimized = getattr(win, "is_minimized", None)
    if callable(is_minimized):
        try:
            if is_minimized():
                restore = getattr(win, "restore", None)
                if callable(restore):
                    restore()
        except Exception:
            # Игнорируем любые ошибки восстановления
            return


def safe_activate(win: Any) -> None:
    """Пытается активировать окно."""

    try:
        win.set_focus()
    except Exception as exc:
        raise RuntimeError(f"Не удалось активировать окно: {exc}") from exc


def safe_restore_and_activate(win: Any) -> None:
    """Комбинирует восстановление и активацию."""

    safe_restore(win)
    safe_activate(win)
