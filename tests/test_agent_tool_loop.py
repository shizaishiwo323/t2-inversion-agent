import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from t2_agent.agent import AgentRuntimeContext, run_deepseek_agent_turn


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
