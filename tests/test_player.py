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
