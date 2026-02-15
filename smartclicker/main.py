from __future__ import annotations

import argparse
from pathlib import Path

import config
from player.loader import load_scenario
from player.player_core import Player
from recorder.hotkeys import HotkeyListener
from recorder.recorder_core import RecorderCore
from recorder.serializer import save_scenario


def _parse_params(items: list[str] | None) -> dict[str, str]:
    """
    Парсит повторяемые аргументы вида: --param key=value
    """
    params: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"Неверный параметр '{item}'. Ожидается формат key=value.")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Неверный параметр '{item}': пустое имя.")
        params[key] = value
    return params


def cmd_record(args: argparse.Namespace) -> Path:
    scenario_name: str = args.name or "scenario_1"

    core = RecorderCore(scenario_name=scenario_name)
    listener = HotkeyListener(core)

    scenario = listener.run()
    saved_path = save_scenario(scenario, config.SCENARIOS_DIR)
    print(f"Сценарий сохранён: {saved_path}")
    return Path(saved_path)


def cmd_play(args: argparse.Namespace) -> None:
    scenario = load_scenario(Path(args.scenario))

    # Если пользователь начал задавать launch через CLI — требуем оба
    if (args.title and not args.app_path) or (args.app_path and not args.title):
        raise ValueError("Для автозапуска нужны оба параметра: --title и --app-path")

    if args.title and args.app_path:
        scenario["launch"] = {
            "window_title_contains": args.title,
            "app_path": args.app_path,
            "args": args.arg,
            **({"timeout_ms": args.timeout_ms} if args.timeout_ms else {}),
        }

    params = _parse_params(args.param)

    if not params:
        for name in scenario.get("params", []) or []:
            params[name] = f"value_for_{name}"
        if scenario.get("params"):
            print("[INFO] Параметры не заданы — использую заглушки:", params)

    player = Player(params=params)
    player.run(scenario)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="smartclicker", description="Recorder + Player (MVP)")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_rec = sub.add_parser("record", help="Записать сценарий (F2/F3/Shift+F8/F10)")
    p_rec.add_argument("--name", default="scenario_1", help="Имя сценария (без .yaml)")
    p_rec.set_defaults(_handler=cmd_record)

    p_play = sub.add_parser("play", help="Проиграть сценарий из YAML")
    p_play.add_argument("scenario", help="Путь к YAML сценария")
    p_play.add_argument(
        "--param",
        action="append",
        help="Параметр вида name=value (можно повторять)",
    )
    p_play.add_argument("--title", dest="title", help="Подстрока заголовка окна для attach/wait")
    p_play.add_argument("--app-path", dest="app_path", help="Путь или команда запуска приложения")
    p_play.add_argument("--arg", dest="arg", action="append", help="Аргумент запуска приложения (можно несколько)")
    p_play.add_argument("--timeout-ms", dest="timeout_ms", type=int, help="Таймаут ожидания окна, мс")
    p_play.set_defaults(_handler=cmd_play)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = getattr(args, "_handler", None)
    print(handler)
    if handler is None:
        parser.error("Не выбран режим (record/play).")
    handler(args)


if __name__ == "__main__":
    main()
