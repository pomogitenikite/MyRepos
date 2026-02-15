import pytest

from smart_clicker.player import ScenarioPlayer


def test_play_specific_run(monkeypatch):
    scenario = {
        "format_version": 2,
        "name": "n",
        "params": ["p"],
        "runs": [{"id": "run_001", "values": {"p": "A"}}, {"id": "run_002", "values": {"p": "B"}}],
        "windows": {"win_001": {"selector": {"top_title_contains": "Test"}}},
        "blocks": [{"id": "block_001", "window_ref": "win_001", "steps": [{"id": "step_001", "action": "wait"}]}],
    }
    player = ScenarioPlayer()
    seen = []
    monkeypatch.setattr(player, "_desktop", lambda: object())
    monkeypatch.setattr(player, "_resolve_window", lambda desktop, selector: object())
    monkeypatch.setattr(player, "_run_step", lambda window, step, values: seen.append(values["p"]))

    player.play(scenario, run_id="run_002")
    assert seen == ["B"]


def test_play_specific_run_not_found():
    player = ScenarioPlayer()
    with pytest.raises(ValueError):
        player.play(
            {
                "format_version": 2,
                "name": "n",
                "params": [],
                "runs": [{"id": "run_001", "values": {}}],
                "windows": {},
                "blocks": [],
            },
            run_id="missing",
        )


def test_run_step_click_uses_left_button():
    player = ScenarioPlayer()

    class Target:
        def __init__(self):
            self.button = None

        def click_input(self, button=None):
            self.button = button

    target = Target()
    player._resolve_target = lambda window, step_target: target
    player._run_step(object(), {"action": "click", "target": {}}, {})
    assert target.button == "left"


def test_run_step_keys_uses_send_keys(monkeypatch):
    player = ScenarioPlayer()
    sent = []

    class Target:
        def set_focus(self):
            return None

    monkeypatch.setattr(player, "_send_keys", sent.append)
    player._resolve_target = lambda window, step_target: Target()
    player._run_step(object(), {"action": "keys", "keys": "{ENTER}", "target": {}}, {})
    assert sent == ["{ENTER}"]
