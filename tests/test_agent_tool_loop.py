import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from t2_agent.agent import AgentRuntimeContext, build_tool_specs, execute_agent_tool, run_deepseek_agent_turn
from t2_agent.models import AgentToolResult


def _message(content=None, tool_calls=None):
    return SimpleNamespace(
        content=content,
        tool_calls=tool_calls,
        model_dump=lambda: {
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {"name": call.function.name, "arguments": call.function.arguments},
                }
                for call in (tool_calls or [])
            ],
        },
    )


def _tool_call(name, arguments):
    return SimpleNamespace(
        id=f"call_{name}",
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


class FakeCompletions:
    def __init__(self, messages):
        self._messages = messages
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        message = self._messages.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeClient:
    def __init__(self, messages):
        self.chat = SimpleNamespace(completions=FakeCompletions(messages))


def test_run_lcurve_tool_schema_exposes_alpha_search_range():
    specs = build_tool_specs()
    run_lcurve_spec = next(item for item in specs if item["function"]["name"] == "run_lcurve")
    properties = run_lcurve_spec["function"]["parameters"]["properties"]

    assert "alpha_min" in properties
    assert "alpha_max" in properties
    assert "smoothing factor" in properties["alpha_min"]["description"]
    assert "smoothing factor" in properties["alpha_max"]["description"]


def test_agent_tool_schema_exposes_2d_simulation_tools():
    specs = build_tool_specs()
    names = {item["function"]["name"] for item in specs}

    assert "inspect_2d_geometry_input" in names
    assert "run_2d_mesh_and_decay" in names
    assert "run_2d_simulation_full_workflow" in names


def test_execute_2d_mesh_and_decay_updates_context(tmp_path, monkeypatch):
    png_path = tmp_path / "phase.png"
    png_path.write_bytes(b"fake")
    decay_path = tmp_path / "decay.xlsx"
    decay_path.write_bytes(b"fake-xlsx")
    context = AgentRuntimeContext(workspace=tmp_path / "workspace", uploaded_path=png_path)

    def fake_run_png_mesh_decay(input_path, output_dir, params):
        return {
            "status": "success",
            "standard_decay_xlsx": str(decay_path),
            "mesh_png": str(tmp_path / "mesh.png"),
            "curve_png": str(tmp_path / "decay.png"),
            "simulation_stages": {
                "mesh": [str(tmp_path / "mesh.png")],
                "decay": [str(tmp_path / "decay.png"), str(decay_path)],
            },
        }

    monkeypatch.setattr("t2_agent.tools.run_png_mesh_decay", fake_run_png_mesh_decay)

    result = execute_agent_tool("run_2d_mesh_and_decay", {"geometry_mode": "png"}, context)

    assert result.status == "success"
    assert context.repaired_path == decay_path
    assert context.simulation_decay_path == decay_path
    assert result.summary["simulation_stages"]["decay"][-1] == str(decay_path)


def test_full_2d_simulation_workflow_reuses_existing_inversion_tools(tmp_path, monkeypatch):
    png_path = tmp_path / "phase.png"
    png_path.write_bytes(b"fake")
    decay_path = tmp_path / "simulation_decay.xlsx"
    spectrum_path = tmp_path / "simulation_spectrum.xlsx"
    context = AgentRuntimeContext(workspace=tmp_path / "workspace", uploaded_path=png_path)
    captured = {}

    def fake_run_2d_mesh_and_decay(input_path, output_dir, params, language="中文"):
        captured["simulation_input"] = input_path
        captured["simulation_output"] = output_dir
        return AgentToolResult(
            "success",
            "simulated",
            artifacts=[str(tmp_path / "mesh.png"), str(decay_path)],
            summary={
                "standard_decay_xlsx": str(decay_path),
                "simulation_stages": {
                    "mesh": [str(tmp_path / "mesh.png")],
                    "decay": [str(decay_path)],
                },
            },
        )

    def fake_run_lcurve(input_workbook, output_dir, params, language="中文"):
        captured["inversion_input"] = input_workbook
        captured["inversion_params"] = params
        return AgentToolResult(
            "success",
            "inverted",
            artifacts=[str(spectrum_path)],
            summary={"spectrum_xlsx": str(spectrum_path)},
        )

    def fake_run_gaussian_peaks(input_workbook, output_dir, params, language="中文"):
        captured["gaussian_input"] = input_workbook
        captured["gaussian_params"] = params
        return AgentToolResult("success", "peaks", artifacts=[str(tmp_path / "peaks.xlsx")])

    monkeypatch.setattr("t2_agent.agent.run_2d_mesh_and_decay", fake_run_2d_mesh_and_decay)
    monkeypatch.setattr("t2_agent.agent.run_lcurve", fake_run_lcurve)
    monkeypatch.setattr("t2_agent.agent.run_gaussian_peaks", fake_run_gaussian_peaks)

    result = execute_agent_tool(
        "run_2d_simulation_full_workflow",
        {"geometry_mode": "png", "alpha_count": 9, "run_gaussian": True, "peak_count": 2},
        context,
    )

    assert result.status == "success"
    assert captured["simulation_input"] == png_path
    assert captured["inversion_input"] == decay_path
    assert captured["inversion_params"]["alpha_count"] == 9
    assert captured["gaussian_input"] == spectrum_path
    assert captured["gaussian_params"]["peak_count"] == 2
    assert context.simulation_decay_path == decay_path
    assert context.repaired_path == decay_path
    assert context.spectrum_path == spectrum_path
    assert result.summary["simulation_decay_xlsx"] == str(decay_path)


def test_execute_run_lcurve_forwards_alpha_search_range(tmp_path, monkeypatch):
    captured = {}

    def fake_run_lcurve(input_workbook, output_dir, params, language="中文"):
        captured["input_workbook"] = input_workbook
        captured["output_dir"] = output_dir
        captured["params"] = params
        return AgentToolResult("success", "ok", summary={"spectrum_xlsx": str(tmp_path / "spectrum.xlsx")})

    monkeypatch.setattr("t2_agent.agent.run_lcurve", fake_run_lcurve)
    context = AgentRuntimeContext(workspace=tmp_path, repaired_path=tmp_path / "standardized.xlsx")

    result = execute_agent_tool(
        "run_lcurve",
        {"alpha_min": 0.01, "alpha_max": 10000.0, "alpha_count": 80, "num_bins": 90},
        context,
    )

    assert result.status == "success"
    assert captured["params"]["alpha_min"] == 0.01
    assert captured["params"]["alpha_max"] == 10000.0
    assert captured["params"]["alpha_count"] == 80
    assert captured["params"]["num_bins"] == 90


def test_agent_loop_executes_ai_requested_validation_tool_for_bad_workbook(tmp_path):
    bad_workbook = tmp_path / "bad.xlsx"
    pd.DataFrame({"time": ["abc", "def"], "signal": ["x", "y"]}).to_excel(bad_workbook, index=False)
    context = AgentRuntimeContext(workspace=tmp_path, uploaded_path=bad_workbook)

    fake_client = FakeClient(
        [
            _message(tool_calls=[_tool_call("inspect_workbook_schema", {}), _tool_call("validate_workbook", {})]),
            _message(content="我已经检查过数据：第一列没有有效时间/T2，不能继续反演。"),
        ]
    )

    trace_events = []
    result = run_deepseek_agent_turn(
        api_key="test-key",
        model="deepseek-v4-flash",
        thinking_enabled=False,
        user_message="请帮我检查这个数据能不能做反演",
        context=context,
        prior_messages=[],
        client=fake_client,
        on_trace=trace_events.append,
    )

    assert result.assistant_message.startswith("我已经检查过数据")
    assert result.tool_results[0].status == "success"
    assert result.tool_results[1].status == "failed"
    assert result.tool_results[1].error == "no_valid_time"
    tool_events = [event for event in result.trace if event["kind"].startswith("tool_")]
    assert tool_events[0]["kind"] == "tool_call"
    assert tool_events[0]["tool_name"] == "inspect_workbook_schema"
    assert tool_events[1]["kind"] == "tool_result"
    assert "工作簿结构" in tool_events[1]["message"]
    assert any(event["kind"] == "tool_call" for event in trace_events)
    assert any(event["kind"] == "tool_result" for event in trace_events)
    assert context.validation is not None
    assert fake_client.chat.completions.calls[0]["tools"]


def test_agent_loop_can_request_english_response_language(tmp_path):
    source = Path(__file__).resolve().parents[1] / "T2process" / "Example data" / "SimulationDecay.xlsx"
    context = AgentRuntimeContext(workspace=tmp_path, uploaded_path=source)
    fake_client = FakeClient([_message(content="I can explain the available T2 tools.")])

    run_deepseek_agent_turn(
        api_key="test-key",
        model="deepseek-v4-flash",
        thinking_enabled=False,
        user_message="What can you do?",
        context=context,
        prior_messages=[],
        client=fake_client,
        response_language="English",
    )

    system_message = fake_client.chat.completions.calls[0]["messages"][0]["content"]
    assert "Reply in English" in system_message
    assert "Available T2 skills/tools" in system_message


def test_agent_loop_refreshes_existing_system_prompt_when_language_changes(tmp_path):
    context = AgentRuntimeContext(workspace=tmp_path)
    prior_messages = [
        {"role": "system", "content": "用户可见语言：中文。请用中文回复。"},
        {"role": "assistant", "content": "中文回复"},
    ]
    fake_client = FakeClient([_message(content="English reply")])

    run_deepseek_agent_turn(
        api_key="test-key",
        model="deepseek-v4-flash",
        thinking_enabled=False,
        user_message="What can you do?",
        context=context,
        prior_messages=prior_messages,
        client=fake_client,
        response_language="English",
    )

    system_message = fake_client.chat.completions.calls[0]["messages"][0]["content"]
    assert "Reply in English" in system_message
    assert "请用中文回复" not in system_message


def test_agent_loop_executes_repair_and_lcurve_when_ai_requests_tools(tmp_path):
    source = Path(__file__).resolve().parents[1] / "T2process" / "Example data" / "SimulationDecay.xlsx"
    context = AgentRuntimeContext(workspace=tmp_path, uploaded_path=source)

    fake_client = FakeClient(
        [
            _message(
                tool_calls=[
                    _tool_call("inspect_workbook_schema", {}),
                    _tool_call("validate_workbook", {}),
                    _tool_call("repair_workbook", {}),
                    _tool_call("run_lcurve", {"num_bins": 60, "alpha_count": 12}),
                ]
            ),
            _message(content="我已完成数据检查、标准化和 L-curve 反演。"),
        ]
    )

    result = run_deepseek_agent_turn(
        api_key="test-key",
        model="deepseek-v4-flash",
        thinking_enabled=False,
        user_message="我不懂参数，请你帮我自动做T2反演",
        context=context,
        prior_messages=[],
        client=fake_client,
    )

    assert "L-curve" in result.assistant_message
    assert context.validation is not None
    assert context.repaired_path is not None
    assert context.spectrum_path is not None
    assert any(tool_result.status == "success" for tool_result in result.tool_results)
    assert len(context.tool_history) == 4
    assert any(path.endswith("__standardized.xlsx") for item in context.tool_history for path in item.artifacts)
    assert any(path.endswith("_spectrum.xlsx") for item in context.tool_history for path in item.artifacts)


def test_agent_loop_uses_uploaded_spectrum_for_gaussian_and_blocks_inversion(tmp_path):
    spectrum = tmp_path / "uploaded_t2_spectrum.xlsx"
    t2_ms = np.logspace(-1, 3, 80)
    amplitude = np.exp(-((np.log10(t2_ms) - 1.0) ** 2) / 0.18)
    pd.DataFrame({"t2_ms": t2_ms, "amplitude": amplitude}).to_excel(spectrum, index=False)
    context = AgentRuntimeContext(workspace=tmp_path / "workspace", uploaded_path=spectrum)

    fake_client = FakeClient(
        [
            _message(
                tool_calls=[
                    _tool_call("inspect_workbook_schema", {}),
                    _tool_call("validate_workbook", {}),
                    _tool_call("repair_workbook", {}),
                    _tool_call("run_lcurve", {"num_bins": 40, "alpha_count": 8}),
                    _tool_call("run_gaussian_peaks", {"peak_count": 2}),
                ]
            ),
            _message(content="这是已有 T2 谱，我已跳过反演并完成 Gaussian 分峰。"),
        ]
    )

    result = run_deepseek_agent_turn(
        api_key="test-key",
        model="deepseek-v4-flash",
        thinking_enabled=False,
        user_message="这是T2谱表，只做分峰",
        context=context,
        prior_messages=[],
        client=fake_client,
    )

    assert "跳过反演" in result.assistant_message
    assert context.validation is not None
    assert context.validation.summary["data_kind"] == "spectrum"
    assert context.spectrum_path == spectrum
    assert result.tool_results[2].status == "failed"
    assert result.tool_results[2].error == "spectrum_input_not_decay"
    assert result.tool_results[3].status == "failed"
    assert result.tool_results[3].error == "spectrum_input_not_decay"
    assert result.tool_results[4].status == "success", result.tool_results[4].error
    assert any(path.endswith("_gaussian_summary.csv") for path in result.tool_results[4].artifacts)


def test_agent_loop_does_not_auto_invert_when_user_asks_only_for_peaks(tmp_path):
    time_ms = np.linspace(0.1, 80.0, 80)
    decay = tmp_path / "decay.xlsx"
    pd.DataFrame({"Time": time_ms, "Peak": np.exp(-time_ms / 25.0) * 1000.0}).to_excel(decay, index=False)
    context = AgentRuntimeContext(workspace=tmp_path / "workspace", uploaded_path=decay)

    fake_client = FakeClient(
        [
            _message(
                tool_calls=[
                    _tool_call("inspect_workbook_schema", {}),
                    _tool_call("validate_workbook", {}),
                    _tool_call("repair_workbook", {}),
                    _tool_call("run_lcurve", {"num_bins": 40, "alpha_count": 8}),
                    _tool_call("run_gaussian_peaks", {"peak_count": 3}),
                ]
            ),
            _message(content="你要求只做分峰，但当前没有可用 T2 谱表，所以我不会自动反演。"),
        ]
    )

    result = run_deepseek_agent_turn(
        api_key="test-key",
        model="deepseek-v4-flash",
        thinking_enabled=False,
        user_message="只做分峰，分三个峰",
        context=context,
        prior_messages=[],
        client=fake_client,
    )

    assert "不会自动反演" in result.assistant_message
    assert result.tool_results[2].status == "failed"
    assert result.tool_results[2].error == "gaussian_only_requires_spectrum"
    assert result.tool_results[3].status == "failed"
    assert result.tool_results[3].error == "gaussian_only_requires_spectrum"
    assert result.tool_results[4].status == "failed"
    assert result.tool_results[4].error == "missing_spectrum"
    assert context.spectrum_path is None


def test_agent_loop_interprets_existing_results_when_user_asks(tmp_path):
    source = Path(__file__).resolve().parents[1] / "T2process" / "Example data" / "SimulationDecay.xlsx"
    context = AgentRuntimeContext(workspace=tmp_path, uploaded_path=source)

    setup_client = FakeClient(
        [
            _message(
                tool_calls=[
                    _tool_call("inspect_workbook_schema", {}),
                    _tool_call("validate_workbook", {}),
                    _tool_call("repair_workbook", {}),
                    _tool_call("run_lcurve", {"num_bins": 60, "alpha_count": 12}),
                ]
            ),
            _message(content="已完成反演。"),
        ]
    )
    run_deepseek_agent_turn(
        api_key="test-key",
        model="deepseek-v4-flash",
        thinking_enabled=False,
        user_message="先帮我自动反演",
        context=context,
        prior_messages=[],
        client=setup_client,
    )

    interpretation_client = FakeClient(
        [
            _message(tool_calls=[_tool_call("interpret_results", {})]),
            _message(content="我读取了结果，主峰位置和最佳平滑因子如下。"),
        ]
    )
    result = run_deepseek_agent_turn(
        api_key="test-key",
        model="deepseek-v4-flash",
        thinking_enabled=False,
        user_message="帮我解释一下这个结果，看看说明什么",
        context=context,
        prior_messages=[],
        client=interpretation_client,
    )

    assert "主峰" in result.assistant_message
    assert result.tool_results[0].status == "success"
    assert "main_peak_t2_ms" in result.tool_results[0].summary


def test_agent_loop_can_batch_process_all_uploaded_files(tmp_path):
    time_ms = np.linspace(0.1, 80.0, 80)
    file_a = tmp_path / "sample_a.xlsx"
    file_b = tmp_path / "sample_b.xlsx"
    pd.DataFrame({"Time": time_ms, "Peak": np.exp(-time_ms / 25.0) * 1000.0}).to_excel(file_a, index=False)
    pd.DataFrame({"Time": time_ms, "Peak": np.exp(-time_ms / 35.0) * 900.0}).to_excel(file_b, index=False)
    context = AgentRuntimeContext(workspace=tmp_path / "workspace", uploaded_path=file_a, uploaded_paths=[file_a, file_b])

    fake_client = FakeClient(
        [
            _message(
                tool_calls=[
                    _tool_call(
                        "process_uploaded_files_batch",
                        {"num_bins": 40, "alpha_count": 8, "run_gaussian": False},
                    )
                ]
            ),
            _message(content="批量处理完成。"),
        ]
    )

    result = run_deepseek_agent_turn(
        api_key="test-key",
        model="deepseek-v4-flash",
        thinking_enabled=False,
        user_message="请批量处理所有上传文件并生成报告",
        context=context,
        prior_messages=[],
        client=fake_client,
    )

    assert result.assistant_message == "批量处理完成。"
    assert result.tool_results[0].status == "success", result.tool_results[0].error
    assert result.tool_results[0].summary["file_count"] == 2
    assert result.tool_results[0].summary["successful_file_count"] == 2
    assert any("batch_results" in path and "sample_a.xlsx" in path for path in result.tool_results[0].artifacts)
    assert any("batch_results" in path and "sample_b.xlsx" in path for path in result.tool_results[0].artifacts)
