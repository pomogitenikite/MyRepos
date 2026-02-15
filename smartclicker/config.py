from pathlib import Path

SCENARIOS_DIR: Path = Path(__file__).resolve().parent / "scenarios"
DEFAULT_SCENARIO_FILENAME: str = "scenario.yaml"
DEFAULT_LOG_FILENAME: str = "recorder.log"

HOTKEY_RECORD_CLICK: str = "F2"
HOTKEY_RECORD_TYPE: str = "F3"
HOTKEY_WAIT_FOR_WINDOW: str = "Shift+F8"
HOTKEY_STOP_RECORDING: str = "F10"
