import re
import time

from .scenario import load_scenario, render_template


def _safe_selector(selector):
    return {
        k: v
        for k, v in (selector or {}).items()
        if k in {"automation_id", "name", "control_type", "class_name"} and v not in (None, "")
    }


class ScenarioPlayer:
    def __init__(self, backend="uia"):
        self.backend = backend

    def _desktop(self):
        from pywinauto import Desktop

        return Desktop(backend=self.backend)

    def _resolve_window(self, desktop, selector):
        class_name = selector.get("class_name")
        title_contains = selector.get("top_title_contains")
        title_regex = selector.get("top_title_regex")
        candidates = desktop.windows(class_name=class_name) if class_name else desktop.windows()
        for item in candidates:
            title = item.window_text() or ""
            if title_contains and title_contains not in title:
                continue
            if title_regex and not re.search(title_regex, title):
                continue
            return item
        raise RuntimeError(f"Window not found for selector: {selector}")

    def _matches_wrapper(self, wrapper, selector):
        info = wrapper.element_info
        for key, value in _safe_selector(selector).items():
            if getattr(info, key, None) != value:
                return False
        return True

    def _descend_path(self, root, path):
        current = root
        chain = list(reversed(path or []))
        if chain and self._matches_wrapper(root, chain[0]):
            chain = chain[1:]
        for item in chain:
            current = current.child_window(**_safe_selector(item)).wrapper_object()
        return current

    def _resolve_target(self, window_wrapper, target):
        parent = self._descend_path(window_wrapper, (target or {}).get("path"))
        return parent.child_window(**_safe_selector(target)).wrapper_object()

    def _run_step(self, window_wrapper, step, run_values):
        action = step["action"]
        if action == "wait":
            seconds = step.get("seconds", step.get("value", 1))
            time.sleep(float(seconds))
            return
        if action == "keys":
            target = self._resolve_target(window_wrapper, step["target"])
            target.type_keys(step["keys"], set_foreground=True)
            return
        target = self._resolve_target(window_wrapper, step["target"])
        if action == "click":
            target.click_input()
        elif action == "type":
            text = render_template(step.get("value", ""), run_values)
            target.type_keys(text, with_spaces=True, set_foreground=True)
        else:
            raise ValueError(f"Unsupported action: {action}")

    def play(self, scenario, run_id=None):
        runs = scenario.get("runs") or [{"id": "default", "values": {}}]
        if run_id:
            runs = [run for run in runs if run.get("id") == run_id]
            if not runs:
                raise ValueError(f"Run '{run_id}' not found")
        desktop = self._desktop()
        for run in runs:
            values = run.get("values", {})
            for block in scenario.get("blocks", []):
                selector = scenario["windows"][block["window_ref"]]["selector"]
                window_wrapper = self._resolve_window(desktop, selector)
                for step in block.get("steps", []):
                    self._run_step(window_wrapper, step, values)

    def play_file(self, path, run_id=None):
        self.play(load_scenario(path), run_id=run_id)
