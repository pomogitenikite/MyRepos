import platform

from .scenario import default_scenario, register_params, save_scenario


def _selector_from_info(info):
    selector = {}
    for key in ("automation_id", "name", "control_type", "class_name"):
        value = getattr(info, key, None)
        if value:
            selector[key] = value
    return selector


class ScenarioBuilder:
    def __init__(self, name):
        self.scenario = default_scenario(name)
        self._window_counter = 0
        self._block_counter = 0
        self._step_counter = 0
        self._window_by_key = {}

    def _next_id(self, prefix, value):
        return f"{prefix}_{value:03d}"

    def _window_ref(self, title, class_name):
        key = (title or "", class_name or "")
        if key in self._window_by_key:
            return self._window_by_key[key]
        self._window_counter += 1
        ref = self._next_id("win", self._window_counter)
        self._window_by_key[key] = ref
        self.scenario["windows"][ref] = {
            "selector": {"top_title_contains": title or "", "class_name": class_name or ""},
        }
        return ref

    def _ensure_block(self, window_ref):
        blocks = self.scenario["blocks"]
        if blocks and blocks[-1]["window_ref"] == window_ref:
            return blocks[-1]
        self._block_counter += 1
        block = {"id": self._next_id("block", self._block_counter), "window_ref": window_ref, "steps": []}
        blocks.append(block)
        return block

    def add_step(self, window_title, window_class_name, action, target, value=None, keys=None):
        self._step_counter += 1
        step = {"id": self._next_id("step", self._step_counter), "action": action, "target": target}
        if value is not None:
            step["value"] = value
            register_params(self.scenario, value)
        if keys is not None:
            step["keys"] = keys
        window_ref = self._window_ref(window_title, window_class_name)
        self._ensure_block(window_ref)["steps"].append(step)

    def undo(self):
        blocks = self.scenario["blocks"]
        if not blocks:
            return
        steps = blocks[-1]["steps"]
        if steps:
            steps.pop()
        if not steps:
            blocks.pop()


class ScenarioRecorder:
    def __init__(self, out_path, name, backend="uia", max_depth=10):
        self.out_path = out_path
        self.backend = backend
        self.max_depth = max_depth
        self.builder = ScenarioBuilder(name)
        self.paused = False
        self._dialog_active = False
        self._hook = None

    def _root_dialog(self):
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        return root

    def _capture_target(self, x, y):
        from pywinauto.controls.uiawrapper import UIAWrapper
        from pywinauto.uia_element_info import UIAElementInfo

        info = UIAElementInfo.from_point(x, y)
        wrapper = UIAWrapper(info)
        top = wrapper.top_level_parent()
        target = _selector_from_info(info)
        path = []
        parent = getattr(info, "parent", None)
        while parent is not None and len(path) < self.max_depth:
            path.append(_selector_from_info(parent))
            if getattr(parent, "control_type", None) == "Window":
                break
            parent = getattr(parent, "parent", None)
        if path:
            target["path"] = path
        return top, target

    @staticmethod
    def _cursor_pos():
        from ctypes import Structure, byref, c_long, windll

        class _POINT(Structure):
            _fields_ = [("x", c_long), ("y", c_long)]

        pt = _POINT()
        windll.user32.GetCursorPos(byref(pt))
        return pt.x, pt.y

    @staticmethod
    def _is_ctrl_alt(event):
        if event.event_type != "key down":
            return False
        pressed = {str(key).lower() for key in event.pressed_key}
        ctrl = {"lcontrol", "rcontrol", "control"} & pressed
        alt = {"lmenu", "rmenu", "menu"} & pressed
        return bool(ctrl and alt)

    def _record_action_with_dialog(self, event, action):
        self._dialog_active = True
        root = self._root_dialog()
        try:
            from tkinter import simpledialog

            title = "smart_clicker recorder"
            prompt = "Type value:" if action == "type" else "Keys pattern:"
            value = simpledialog.askstring(title, prompt, parent=root)
        finally:
            root.destroy()
            self._dialog_active = False
        if not value:
            return
        x, y = self._cursor_pos()
        top, target = self._capture_target(x, y)
        if action == "type":
            self.builder.add_step(top.window_text(), top.class_name(), "type", target, value=value)
        else:
            self.builder.add_step(top.window_text(), top.class_name(), "keys", target, keys=value)

    def _handle_keyboard(self, event):
        if event.current_key == "F8" and event.event_type == "key down":
            self.paused = not self.paused
            return
        if event.current_key == "F9" and event.event_type == "key down":
            save_scenario(self.out_path, self.builder.scenario)
            self._hook.stop()
            return
        if self.paused or self._dialog_active:
            return
        if self._is_ctrl_alt(event) and event.current_key == "T":
            self._record_action_with_dialog(event, "type")
        elif self._is_ctrl_alt(event) and event.current_key == "K":
            self._record_action_with_dialog(event, "keys")
        elif self._is_ctrl_alt(event) and event.current_key == "Z":
            self.builder.undo()

    def _handle_mouse(self, event):
        if self.paused or self._dialog_active:
            return
        if event.current_key == "LButton" and event.event_type == "key up":
            top, target = self._capture_target(event.mouse_x, event.mouse_y)
            self.builder.add_step(top.window_text(), top.class_name(), "click", target)

    def _on_event(self, event):
        kind = type(event).__name__
        if kind == "KeyboardEvent":
            self._handle_keyboard(event)
        elif kind == "MouseEvent":
            self._handle_mouse(event)

    def record(self):
        if platform.system() != "Windows":
            raise RuntimeError("Recording is supported only on Windows")
        from pywinauto.win32_hooks import Hook

        self._hook = Hook()
        self._hook.handler = self._on_event
        self._hook.hook(keyboard=True, mouse=True)
        save_scenario(self.out_path, self.builder.scenario)
