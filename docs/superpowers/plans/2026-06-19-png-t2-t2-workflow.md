# PNG T2-T2 Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the validated PNG phase-map T2 and reduced T2-T2 workflow into the existing T2 agent tools.

**Architecture:** Add focused helpers to `t2_agent/simulation_2d.py` for color normalization, physical-size scaling, and reduced T2-T2 generation. Expose them through `t2_agent/tools.py` and `t2_agent/agent.py` by enhancing the existing full workflow rather than adding a parallel command.

**Tech Stack:** Python 3.11, pyGIMLi, NumPy, SciPy NNLS, Pandas, Matplotlib, Streamlit tool-result staging.

---

### Task 1: PNG Normalization And Physical Scaling

**Files:**
- Modify: `t2_agent/simulation_2d.py`
- Test: `tests/test_simulation_2d.py`

- [x] Add a `normalize_png_phase_map` helper that maps every RGB pixel to nearest white/red/yellow, writes a derived PNG, and records source color counts.
- [x] Add preparation flow inside `run_png_mesh_decay` to optionally normalize, inspect, crop, and compute pixel size from `physical_size_x_um` and `physical_size_y_um`.
- [x] Update `run_png_mesh_decay` to accept optional `normalize_phase_colors`, `physical_size_x_um`, and `physical_size_y_um` through `Simulation2DParams`-adjacent arguments.
- [x] Write tests that use shallow antialias-like colors and assert that the derived PNG is exact red/yellow/white and the cropped size is used for pixel scaling.

### Task 2: Reduced T2-T2 Backend

**Files:**
- Modify: `t2_agent/simulation_2d.py`
- Test: `tests/test_simulation_2d.py`

- [x] Add reduced 2D NNLS solving locally so the project does not depend on the external `NMR模拟` directory.
- [x] Add `run_reduced_t2_t2_from_spectrum_workbook` that reads the first T2 spectrum sheet, builds the reduced T2-T2 signal, writes CSV/XLSX/PNG artifacts, and returns summary metadata.
- [x] Mark the result method as reduced and not strict exchange PDE.
- [x] Test artifact creation with a small synthetic T2 spectrum.

### Task 3: Tool Layer Integration

**Files:**
- Modify: `t2_agent/tools.py`
- Test: `tests/test_t2_agent.py`

- [x] Extend simulation tool routing to accept `physical_size_x_um`, `physical_size_y_um`, and `normalize_phase_colors`.
- [x] Add a tool wrapper for reduced T2-T2 generation.
- [x] Ensure `run_2d_mesh_and_decay` returns normalization, crop, and physical-scale summaries.
- [x] Test that color normalization and physical scaling are visible in the returned `AgentToolResult`.

### Task 4: Agent Full Workflow Integration

**Files:**
- Modify: `t2_agent/agent.py`
- Test: `tests/test_agent_tool_loop.py`

- [x] Extend tool schemas for `inspect_2d_geometry_input`, `run_2d_mesh_and_decay`, and `run_2d_simulation_full_workflow`.
- [x] Add `run_t2_t2` and T2-T2 parameters to full workflow execution after a spectrum exists.
- [x] Put reduced T2-T2 artifacts under `simulation_stages["t2_t2"]`.
- [x] Update system prompt wording so dimensions apply to the cropped sample area.
- [x] Test that a full workflow with `run_t2_t2=True` returns `t2_t2` stage metadata and keeps `simulation_decay_xlsx`.

### Task 5: UI Text And Verification

**Files:**
- Modify: `t2_agent/i18n.py`
- Test: `tests/test_streamlit_rendering.py`

- [x] Adjust PNG upload hint to mention safe color normalization and sample-size dimensions.
- [x] Ensure existing stage grouping displays reduced T2-T2 artifacts without special UI code.
- [x] Run focused tests with the verified `t2agent` Python:
  `C:\Users\imgw\.conda\envs\t2agent\python.exe -m pytest tests/test_simulation_2d.py tests/test_agent_tool_loop.py tests/test_t2_agent.py tests/test_streamlit_rendering.py -q`
