from __future__ import annotations

from typing import Optional

from .model import Step, StepAction, UIAPassport, WindowContext


class StepBuilder:
    """
    Конструктор шагов сценария.

    Пример использования:
    builder = StepBuilder("demo")
    step = builder.build_click_step(window_ctx, target)
    """

    def __init__(self, scenario_name: str):
        self.scenario_name = scenario_name
        self._counter = 0

    def _next_id(self) -> str:
        """Генерирует идентификатор вида step_001, step_002 и т.д."""

        self._counter += 1
        return f"step_{self._counter:03d}"

    def build_click_step(
        self,
        window: WindowContext,
        target: UIAPassport,
        comment: Optional[str] = None,
    ) -> Step:
        """Создаёт шаг клика по элементу."""

        return Step(
            id=self._next_id(),
            action=StepAction.CLICK,
            window=window,
            target=target,
            comment=comment,
        )

    def build_type_step_with_param(
        self,
        window: WindowContext,
        target: UIAPassport,
        param_name: str,
        comment: Optional[str] = None,
    ) -> Step:
        """Создаёт шаг ввода значения параметра в элемент."""

        return Step(
            id=self._next_id(),
            action=StepAction.TYPE,
            window=window,
            target=target,
            value=f"${{{param_name}}}",
            comment=comment,
        )