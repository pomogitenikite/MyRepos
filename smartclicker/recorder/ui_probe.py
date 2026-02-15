from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.uia_element_info import UIAElementInfo

from .model import UIAPassport, WindowContext


_WS_RE = re.compile(r"\s+")


def _safe_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    try:
        s = str(v)
    except Exception:
        return None

    s = s.replace("\u00A0", " ")
    s = _WS_RE.sub(" ", s).strip()
    return s or None


def _build_ancestry_until_window(info: UIAElementInfo, limit: int = 8) -> List[Dict[str, Optional[str]]]:
    """
    Поднимаемся по parent, но стараемся дойти до control_type == 'Window'.
    limit ограничивает “глубину”, чтобы не раздувать YAML.
    """
    ancestors: List[Dict[str, Optional[str]]] = []
    current = getattr(info, "parent", None)

    while current is not None and len(ancestors) < limit:
        ct = _safe_str(getattr(current, "control_type", None))
        ancestors.append(
            {
                "name": _safe_str(getattr(current, "name", None)),
                "control_type": ct,
                "class_name": _safe_str(getattr(current, "class_name", None)),
                "automation_id": _safe_str(getattr(current, "automation_id", None)),
            }
        )
        if ct == "Window":
            break
        current = getattr(current, "parent", None)

    return ancestors


def get_element_under_point(x: int, y: int, ancestry_limit: int = 8) -> Tuple[WindowContext, UIAPassport]:
    info = UIAElementInfo.from_point(x, y)
    wrapper = UIAWrapper(info)
    top_parent = wrapper.top_level_parent()

    top_title = _safe_str(top_parent.window_text() or top_parent.element_info.name)

    window_ctx = WindowContext(top_title_contains=top_title)
    passport = UIAPassport(
        automation_id=_safe_str(getattr(info, "automation_id", None)),
        name=_safe_str(getattr(info, "name", None)),
        control_type=_safe_str(getattr(info, "control_type", None)),
        class_name=_safe_str(getattr(info, "class_name", None)),
        path=_build_ancestry_until_window(info, limit=ancestry_limit),
    )

    return window_ctx, passport
