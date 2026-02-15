"""Обёртка над pywinauto для работы с окнами и элементами (MVP)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pywinauto import Desktop, WindowSpecification
from pywinauto import keyboard as pw_keyboard
from pywinauto.base_wrapper import BaseWrapper
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.findwindows import ElementAmbiguousError, ElementNotFoundError

RETRY_INTERVAL_SEC = 0.2

_WS_RE = re.compile(r"\s+")


def _norm_title(s: Optional[str]) -> str:
    """Нормализует заголовок: NBSP -> space, схлопывание пробелов."""
    if not s:
        return ""
    s = str(s).replace("\u00A0", " ")
    s = _WS_RE.sub(" ", s).strip()
    return s


def _contains_to_title_re(title_contains: str) -> str:
    """
    Делает regex для title_re, устойчивый к вариациям пробелов.
    'Hello  World' -> '.*Hello\\s+World.*'
    """
    needle = _norm_title(title_contains)
    if not needle:
        return ".*"
    escaped = re.escape(needle)
    escaped = escaped.replace(r"\ ", r"\s+")
    return rf".*{escaped}.*"


def find_window(
    title_contains: str,
    timeout_ms: int = 15000,
    process: Optional[int] = None,
) -> WindowSpecification:
    """
    Находит окно (включая модалки), используя Desktop.window(...).
    Важно: top_level_only=False и visible_only=False помогают находить больше случаев.
    """
    title_contains = _norm_title(title_contains)
    if not title_contains:
        raise ValueError("title_contains не должен быть пустым")

    desktop = Desktop(backend="uia", allow_magic_lookup=False)

    try:
        spec = desktop.window(
            title_re=_contains_to_title_re(title_contains)
        )
    except ElementAmbiguousError as exc:
        spec = desktop.windows(
            title_re=_contains_to_title_re(title_contains),
        )
        print(spec[0].process_id)
        print(spec[1].process_id)
        return spec[0].iface_window()


    try:
        spec.wait("exists", timeout=timeout_ms / 1000, retry_interval=RETRY_INTERVAL_SEC)
        return spec
    except Exception as exc:
        spec = desktop.windows(
            title_re=_contains_to_title_re(title_contains),
        )
        spec[0].set_focus()
        print(spec[1].element_info.runtime_id)
        print(len(spec))
        return spec[0]


def activate_window(win: UIAWrapper) -> None:
    """Активирует окно и выводит на передний план."""
    try:
        try:
            if win.is_minimized():
                win.restore()
        except Exception:
            pass
        win.set_focus()
    except Exception as exc:
        raise RuntimeError(f"Не удалось активировать окно: {exc}") from exc


def _filter_wrappers(
    wrappers: List[BaseWrapper],
    passport: Dict[str, Any],
) -> List[BaseWrapper]:
    """Фильтрует wrappers по полям паспорта через element_info."""
    auto_id = passport.get("automation_id") or None
    ct = passport.get("control_type") or None
    name = passport.get("name") or None
    class_name = passport.get("class_name") or None

    out: List[Any] = []
    for w in wrappers:
        info = getattr(w, "element_info", None)
        if info is None:
            continue

        if auto_id and getattr(info, "automation_id", None) != auto_id:
            continue
        if ct and getattr(info, "control_type", None) != ct:
            continue
        if name and getattr(info, "name", None) != name:
            continue
        if class_name and getattr(info, "class_name", None) != class_name:
            continue

        out.append(w)
    return out


def _find_container_by_path(win_spec: WindowSpecification, path: List[Dict[str, Any]]) -> WindowSpecification:
    """
    Пытается сузить поиск, найдя один из предков из path как контейнер.
    Реализация: ищем контейнер через child_window и exists().
    """
    if not path:
        return win_spec

    for anc in path:
        # не пытаемся сузиться "до Window" — это бессмысленно
        if (anc.get("control_type") or "").strip() == "Window":
            continue

        kwargs = {
            "title": anc.get("name") or None,
            "control_type": anc.get("control_type") or None,
            "class_name": anc.get("class_name") or None,
            "auto_id": anc.get("automation_id") or None,
        }
        kwargs = {k: v for k, v in kwargs.items() if v}

        if not kwargs:
            continue

        try:
            spec = win_spec.child_window(**kwargs)
        except Exception:
            spec = win_spec.descendants(**kwargs)
        try:
            if spec.exists(timeout=0.3, retry_interval=0.05):
                return spec
        except Exception:
            continue

    return win_spec


def find_element(win_spec: WindowSpecification, passport: Dict[str, Any], timeout_ms: int = 20000):
    """
    Ищет элемент в окне по паспорту.
    """
    timeout_s = timeout_ms / 1000

    path: List[Dict[str, Any]] = passport.get("path") or []
    search_root = _find_container_by_path(win_spec, path)

    auto_id = passport.get("automation_id") or None
    ct = passport.get("control_type") or None
    name = passport.get("name") or None
    class_name = passport.get("class_name") or None

    if auto_id:
        kwargs = {"auto_id": auto_id}
        if ct:
            kwargs["control_type"] = ct
        if name:
            kwargs["title"] = name
        if class_name:
            kwargs["class_name"] = class_name

        spec = search_root.child_window(**kwargs)
        try:
            spec.wait("exists", timeout=timeout_s, retry_interval=RETRY_INTERVAL_SEC)
            return spec.wrapper_object()
        except ElementAmbiguousError:
            root_w = search_root.wrapper_object()
            cands = _filter_wrappers(root_w.descendants(), passport)
            if cands:
                return cands[0]
            raise
        except ElementNotFoundError:
            pass

    kwargs2 = {}
    if name:
        kwargs2["title"] = name
    if ct:
        kwargs2["control_type"] = ct
    if class_name:
        kwargs2["class_name"] = class_name

    if kwargs2:
        spec2 = search_root.child_window(**kwargs2)
        try:
            spec2.wait("exists", timeout=timeout_s, retry_interval=RETRY_INTERVAL_SEC)
            return spec2.wrapper_object()
        except ElementAmbiguousError:
            root_w = search_root.wrapper_object()
            cands = _filter_wrappers(root_w.descendants(), passport)
            if cands:
                return cands[0]
            raise
        except ElementNotFoundError:
            pass

    root_w = search_root.wrapper_object()
    cands = _filter_wrappers(root_w.descendants(), passport)
    if cands:
        return cands[0]

    raise LookupError(f"Элемент по паспорту не найден за {timeout_ms} мс (passport={passport}).")

# def _matches_passport(info: Any, passport: Dict[str, Any]) -> bool:
#     """Сравнение полей паспорта с element_info кандидата."""
#     auto_id = _norm(passport.get("automation_id"))
#     ct = _norm(passport.get("control_type"))
#     name = _norm(passport.get("name"))
#     class_name = _norm(passport.get("class_name"))
#
#     if auto_id and _norm(getattr(info, "automation_id", None)) != auto_id:
#         return False
#     if ct and _norm(getattr(info, "control_type", None)) != ct:
#         return False
#     if name and _norm(getattr(info, "name", None)) != name:
#         return False
#     if class_name and _norm(getattr(info, "class_name", None)) != class_name:
#         return False
#
#     return True
#
#
# def _collect_candidates(root: BaseWrapper, passport: Dict[str, Any]) -> List[BaseWrapper]:
#     """
#     Собирает кандидатов в пределах root, фильтруя по полям паспорта.
#     """
#     ct = _norm(passport.get("control_type"))
#
#     try:
#         raw: List[BaseWrapper]
#         if ct:
#             raw = cast(List[BaseWrapper], root.descendants(control_type=ct))
#         else:
#             raw = cast(List[BaseWrapper], root.descendants())
#     except Exception:
#         return []
#
#     out: List[BaseWrapper] = []
#     for w in raw:
#         info = getattr(w, "element_info", None)
#         if info is None:
#             continue
#         if _matches_passport(info, passport):
#             out.append(w)
#     return out
#
#
# def _ancestor_chain(info: Any, max_depth: int) -> List[Any]:
#     """Возвращает цепочку родителей (parent, grandparent, ...) до max_depth."""
#     chain: List[Any] = []
#     cur = getattr(info, "parent", None)
#     while cur is not None and len(chain) < max_depth:
#         chain.append(cur)
#         cur = getattr(cur, "parent", None)
#     return chain
#
#
# def _score_by_path(candidate: BaseWrapper, path: List[Dict[str, Any]]) -> int:
#     """
#     Скоринг кандидата по path.
#     """
#     if not path:
#         return 0
#
#     info = getattr(candidate, "element_info", None)
#     if info is None:
#         return 0
#
#     chain = _ancestor_chain(info, max_depth=len(path))
#
#     score = 0
#     for depth, anc_tpl in enumerate(path):
#         if depth >= len(chain):
#             break
#         anc_info = chain[depth]
#
#         tpl_auto = _norm(anc_tpl.get("automation_id"))
#         tpl_ct = _norm(anc_tpl.get("control_type"))
#         tpl_name = _norm(anc_tpl.get("name"))
#         tpl_cls = _norm(anc_tpl.get("class_name"))
#
#         if tpl_auto and _norm(getattr(anc_info, "automation_id", None)) == tpl_auto:
#             score += 6
#         if tpl_ct and _norm(getattr(anc_info, "control_type", None)) == tpl_ct:
#             score += 3
#         if tpl_name and _norm(getattr(anc_info, "name", None)) == tpl_name:
#             score += 3
#         if tpl_cls and _norm(getattr(anc_info, "class_name", None)) == tpl_cls:
#             score += 1
#
#         if score > 0:
#             score += max(0, 2 - depth)
#
#     return score
#
#
# def _pick_best_by_path(candidates: List[BaseWrapper], path: List[Dict[str, Any]]) -> Optional[BaseWrapper]:
#     if not candidates:
#         return None
#     if not path:
#         return candidates[0]
#
#     best = None
#     best_score = -1
#     for c in candidates:
#         s = _score_by_path(c, path)
#         if s > best_score:
#             best = c
#             best_score = s
#
#     return best
#
#
# def _iter_containers_by_path(root: BaseWrapper, path: List[Dict[str, Any]]) -> Iterable[BaseWrapper]:
#     """
#     Находит потенциальные контейнеры по предкам из path.
#     Это вызывается только как fallback, если "по всему окну" не нашли.
#     """
#     for anc in path:
#         # пропускаем Window, оно обычно слишком общее
#         if _norm(anc.get("control_type")) == "Window":
#             continue
#
#         # Собираем кандидатов контейнеров "похоже на anc"
#         try:
#             pool = cast(List[BaseWrapper], root.descendants(control_type=_norm(anc.get("control_type")) or None))
#         except Exception:
#             pool = []
#
#         for w in pool:
#             info = getattr(w, "element_info", None)
#             if info is None:
#                 continue
#
#             ok = True
#             if anc.get("automation_id") and _norm(getattr(info, "automation_id", None)) != _norm(anc.get("automation_id")):
#                 ok = False
#             if anc.get("name") and _norm(getattr(info, "name", None)) != _norm(anc.get("name")):
#                 ok = False
#             if anc.get("class_name") and _norm(getattr(info, "class_name", None)) != _norm(anc.get("class_name")):
#                 ok = False
#
#             if ok:
#                 yield w
#
#
# def find_element(win: WindowSpecification, passport: Dict[str, Any], timeout_ms: int = 20000) -> BaseWrapper:
#     """
#     1) Ищем кандидатов по всему окну.
#     2) Если 1 -> ок.
#        Если много -> выбираем по path.
#        Если 0 -> пробуем контейнеры по path и повторяем.
#     """
#     deadline = time.monotonic() + timeout_ms / 1000
#
#     path = passport.get("path") or []
#
#     while True:
#         root = to_wrapper(win)
#
#         # A) поиск "в лоб"
#         cands = _collect_candidates(root, passport)
#         if len(cands) == 1:
#             return cands[0]
#         if len(cands) > 1:
#             best = _pick_best_by_path(cands, path)
#             if best is not None:
#                 return best
#
#         # B) fallback: если не нашли вообще — пробуем сузиться по path
#         if not cands and path:
#             for container in _iter_containers_by_path(root, path):
#                 sub = _collect_candidates(container, passport)
#                 if len(sub) == 1:
#                     return sub[0]
#                 if len(sub) > 1:
#                     best = _pick_best_by_path(sub, path)
#                     if best is not None:
#                         return best
#
#         if time.monotonic() >= deadline:
#             break
#         time.sleep(RETRY_INTERVAL_SEC)
#
#     raise LookupError(f"Элемент по паспорту не найден за {timeout_ms} мс (passport={passport}).")

def click_left(element: Any) -> None:
    """Выполняет левый клик по элементу."""
    try:
        if hasattr(element, "scroll_into_view"):
            element.scroll_into_view()
        element.click_input(button="left")
    except Exception as exc:
        raise RuntimeError(f"Не удалось выполнить клик: {exc}") from exc


def type_text(element: Any, text: str) -> None:
    """Фокусирует элемент и вводит текст."""
    try:
        if hasattr(element, "scroll_into_view"):
            element.scroll_into_view()
        print(element)
        element.set_edit_text(text)
        element.type_keys(text, with_spaces=True, set_foreground=True)
        return
    except Exception:
        pass

    try:
        element.set_focus()
        pw_keyboard.send_keys(text)
    except Exception as exc:
        raise RuntimeError(f"Не удалось ввести текст: {exc}") from exc