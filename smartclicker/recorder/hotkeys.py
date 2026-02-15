from __future__ import annotations

from typing import Optional

from pynput import keyboard, mouse

from .model import Scenario
from .recorder_core import RecorderCore


class HotkeyListener:
    """Слушатель глобальных хоткеев для записи сценария."""

    def __init__(self, core: RecorderCore):
        self.core = core
        self._mouse = mouse.Controller()
        self._param_counter = 1

    def _next_param_name(self) -> str:
        name = f"param_{self._param_counter:03d}"
        self._param_counter += 1
        return name

    def run(self) -> Scenario:
        """Запускает слушатель хоткеев и блокирует поток до нажатия F10."""

        self.core.start()
        scenario_result = None

        def on_press(key: keyboard.Key) -> Optional[bool]:
            nonlocal scenario_result

            if key == keyboard.Key.f2:
                x, y = self._mouse.position
                self.core.on_click_hotkey(int(x), int(y))
                print(f"[CLICK] x={int(x)} y={int(y)}")
            elif key == keyboard.Key.f3:
                x, y = self._mouse.position
                param_name = self._next_param_name()
                self.core.on_type_hotkey(int(x), int(y), param_name=param_name)
                print(f"[TYPE] param={param_name} x={int(x)} y={int(y)}")
            elif key == keyboard.Key.f10:
                scenario_result = self.core.stop()
                print("[STOP] запись завершена")
                return False

            return None

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

        if scenario_result is None:
            scenario_result = self.core.stop()

        return scenario_result
