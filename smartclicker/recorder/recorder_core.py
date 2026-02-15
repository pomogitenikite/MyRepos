from __future__ import annotations


from . import ui_probe
from .model import Scenario
from .step_builder import StepBuilder


class RecorderCore:
    """Оркестратор записи: хранит сценарий и реагирует на хоткеи."""

    def __init__(self, scenario_name: str) -> None:
        self.scenario = Scenario(name=scenario_name)
        self.builder = StepBuilder(scenario_name)
        self._is_running = False

    def start(self) -> None:
        """Запускает режим записи."""
        self._is_running = True

    def stop(self) -> Scenario:
        """Останавливает запись и возвращает сценарий."""
        self._is_running = False
        return self.scenario

    def on_click_hotkey(self, x: int, y: int) -> None:
        """Обрабатывает хоткей клика по элементу."""
        if not self._is_running:
            return

        try:
            window_ctx, passport = ui_probe.get_element_under_point(x, y)
        except Exception as e:
            # TODO: заменить на нормальный логгер
            print(f"[ERR] ui_probe failed for CLICK at ({x}, {y}): {e!r}")
            return

        step = self.builder.build_click_step(window_ctx, passport)
        self.scenario.steps.append(step)
        print(f"[REC] CLICK step added: {step.id}")

    def on_type_hotkey(self, x: int, y: int, param_name: str) -> None:
        """Обрабатывает хоткей ввода параметра."""
        if not self._is_running:
            return

        param_name = param_name.strip()
        if not param_name:
            print("[WARN] Empty param_name in on_type_hotkey, step skipped")
            return

        try:
            window_ctx, passport = ui_probe.get_element_under_point(x, y)
        except Exception as e:
            print(f"[ERR] ui_probe failed for TYPE at ({x}, {y}): {e!r}")
            return

        step = self.builder.build_type_step_with_param(window_ctx, passport, param_name)
        self.scenario.steps.append(step)

        if param_name not in self.scenario.params:
            self.scenario.params.append(param_name)

        print(f"[REC] TYPE step added: {step.id} with param '{param_name}'")
