from smart_clicker.recorder import ScenarioBuilder
from smart_clicker.scenario import default_scenario, register_params, render_template


def test_register_params_from_template():
    scenario = default_scenario("demo")
    register_params(scenario, "Hello ${param_001} and ${param_002}")
    register_params(scenario, "Again ${param_001}")
    assert scenario["params"] == ["param_001", "param_002"]


def test_render_template():
    text = render_template("${a}-${b}-${missing}", {"a": "X", "b": 2})
    assert text == "X-2-${missing}"


def test_builder_groups_blocks_by_window_and_undo():
    builder = ScenarioBuilder("demo")
    target = {"name": "btn", "control_type": "Button"}
    builder.add_step("WIN1", "Class1", "click", target)
    builder.add_step("WIN1", "Class1", "click", target)
    builder.add_step("WIN2", "Class2", "type", target, value="${param_001}")

    assert len(builder.scenario["blocks"]) == 2
    assert builder.scenario["params"] == ["param_001"]
    assert len(builder.scenario["blocks"][0]["steps"]) == 2

    builder.undo()
    assert len(builder.scenario["blocks"]) == 1
