---
name: scientific-agent-builder
description: Use when building or extending a scientific computing AI agent that wraps existing domain code with guided parameter selection, tool calling, Streamlit UI, result interpretation, reports, artifacts, or deployment; especially for NMR, geophysics, inversion, simulation, meshing, preprocessing, and analysis workflows.
---

# Scientific Agent Builder

## Overview

Use this skill to turn existing scientific code into a guided, tool-calling AI workflow agent. The core pattern is: keep algorithms deterministic, wrap them as safe tools, let the LLM handle conversation and parameter guidance, then verify the whole loop through realistic browser and artifact tests.

## When To Use

Use for projects like:

- Extending a T2 inversion agent with NMR simulation, mesh generation, parameter sweeps, preprocessing, or result interpretation.
- Building a Streamlit scientific assistant where users describe goals and the agent chooses tools.
- Converting scripts/notebooks into reusable workflow tools without changing the scientific core.
- Adding new domain “sub-skills” such as data cleaning, grid/mesh setup, forward simulation, inversion, peak fitting, plotting, report generation, or uncertainty notes.

Do not use this for a one-off script where no conversational guidance, tool selection, artifact handling, or deployment is needed.

## Core Architecture

Separate responsibilities strictly:

- **LLM layer**: conversation, goal clarification, beginner-friendly parameter explanations, tool choice, final interpretation.
- **Tool layer**: small whitelisted Python functions with typed-ish inputs, deterministic outputs, and no arbitrary shell execution.
- **Scientific core**: existing domain algorithms; patch only compatibility bugs or narrow integration issues.
- **UI layer**: upload, chat, key configuration, progress trace, artifact preview, download zip, task reset.
- **Deployment layer**: Streamlit Cloud/GitHub settings, secrets, dependency pinning, public smoke test.

The LLM may call tools, but it must not execute arbitrary user-provided commands.

## Build Workflow

1. **Read the domain materials first**
   - Open project docs, meeting notes, notebooks, and existing code.
   - Identify what the current code can truly do and what is out of scope.
   - Write an explicit capability map: inputs, outputs, parameters, generated files, failure modes.

2. **Define capability modules**
   - Group domain workflows into sub-capabilities, for example:
     - `validate_data`
     - `repair_or_standardize_data`
     - `preprocess_signal`
     - `generate_mesh`
     - `run_forward_simulation`
     - `run_inversion`
     - `run_peak_decomposition`
     - `plot_results`
     - `interpret_results`
     - `generate_report`
   - Each capability should have one clear scientific purpose and return structured status, message, artifacts, summary, and error.

3. **Wrap tools around existing algorithms**
   - Prefer calling the existing package/pipeline functions.
   - Do not reimplement inversion, meshing, simulation, plotting, or fitting in the web layer if the project already has tested code.
   - Convert notebooks/scripts into importable functions only as much as needed.
   - Preserve raw uploads; write repaired/normalized files as derived artifacts.

4. **Design beginner guidance**
   - Explain parameters before asking users to choose them.
   - Recommend defaults when users are unsure.
   - Ask only key confirmation questions; move advanced controls into expert settings.
   - Phrase recommendations in terms of scientific tradeoffs.

Example:

```text
Regularization controls smoothness. Smaller values follow raw data more closely but can turn noise into fake peaks. Larger values smooth the spectrum but can hide small real peaks. If you do not know what to choose, I recommend L-curve because it searches for a compromise between fit error and smoothness.
```

5. **Create the agent loop**
   - Use provider function calling/tool calling where possible.
   - Start with a system prompt that states:
     - available tools and order constraints,
     - when to inspect/validate before running,
     - when to explain instead of call tools,
     - language requirements,
     - “do not claim tool execution unless a tool result exists.”
   - Keep a runtime context with current upload, standardized data, latest result files, all tool history, and report.

6. **Make artifacts first-class**
   - Every tool result should return generated paths.
   - The UI should preview common images and tables.
   - Chat rendering should resolve model references such as `![plot](decay_t2)` to generated artifacts.
   - The final zip should include artifacts from all turns in the current task.
   - Tell users that task memory/results are temporary unless downloaded.

7. **Build Streamlit as a workbench**
   - Left: chat, language switch, model selector, thinking/trace controls, API key input.
   - Right: upload, data diagnosis, parameter confirmations, results, figures, report, downloads.
   - Show an auditable tool trace, not hidden chain-of-thought.
   - On submit, immediately render the user’s message before the long-running agent call.
   - Provide a “new task” button that clears UI memory without batch-deleting files.

8. **Deploy safely**
   - Store provider keys in Streamlit Secrets or environment variables, never in source.
   - Allow page-level user API key override.
   - Commit `.streamlit/config.toml`, not `.streamlit/secrets.toml`.
   - Use GitHub public repo + `streamlit_app.py` entry for Streamlit Community Cloud.

## Tool Contract

Use a shared result shape for every tool:

```python
AgentToolResult(
    status="success" | "failed",
    message="human-readable summary",
    artifacts=["/path/to/file.png", "/path/to/table.xlsx"],
    summary={"structured": "values"},
    error=None | "machine/debug error",
)
```

Tool design rules:

- Return useful failures; do not raise raw stack traces into the chat when recoverable.
- Include enough summary fields for the LLM to explain results.
- Include figures in `artifacts`, not only tables.
- Do not silently overwrite important user files.
- If a compatibility bug appears in the scientific core, fix the narrow root cause and add a regression test.

## Tests To Add

Add tests before implementation changes when possible:

- **Agent tool loop**: fake model requests a tool; assert the correct tool runs and trace records call/result.
- **Beginner flow**: “I do not understand parameters” recommends automatic/default workflow.
- **Expert flow**: fixed parameter requests call the fixed-parameter tool.
- **Data repair**: nonstandard workbook layouts are diagnosed and normalized.
- **Artifact flow**: inversion/simulation tools return figures and tables.
- **Image rendering**: chat markdown image references resolve to generated artifacts.
- **Environment compatibility**: reproduce cloud dependency issues, such as removed NumPy APIs.
- **Deployment smoke**: public URL loads, key state is correct, console has no critical errors.

## Common Failure Modes

- **Agent only talks, does not act**: add real function calling and verify tools are invoked by tests.
- **Tool ran but user sees no result**: return artifacts and render them in both result panel and report/chat.
- **User input disappears during long runs**: append/render the user message before starting the blocking call.
- **LLM invents file paths or images**: resolve references against known artifacts; never trust arbitrary paths.
- **Cloud works differently than local**: pin/check dependencies and add regression tests for the exact failure.
- **Too many parameters shown**: ask for only key choices; keep expert parameters collapsed.
- **New capability breaks old workflow**: keep each capability behind a small tool wrapper and run full regression tests.

## Expansion Pattern

When adding a new sub-skill such as NMR simulation or mesh generation:

1. Read the domain code and write the capability boundary.
2. Create one or more whitelisted tool wrappers.
3. Add beginner explanations for the new parameters.
4. Add order constraints to the agent prompt, for example “mesh before simulation.”
5. Add artifacts and report sections.
6. Add tests for happy path, bad input, and result interpretation.
7. Browser-test the deployed workflow with a realistic user prompt.

