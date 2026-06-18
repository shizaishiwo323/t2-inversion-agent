# 2D NMR Simulation Workflow Design

## Goal

Add a first-version 2D NMR simulation workflow to the existing T2 agent.
The workflow must support both standalone T2 inversion and a full 2D
simulation path:

```text
geometry input -> pyGIMLi mesh -> NMR/T2 decay solve -> T2 inversion -> visualization/report
```

The first version is explicitly limited to 2D simulation. 3D, T2-T2 maps,
D-T2 maps, CT segmentation, and dynamic multi-state workflows remain out of
scope for this implementation.

## Current Project Context

The current app is a Streamlit T2 inversion assistant. Its stable backend is a
whitelisted tool layer in `t2_agent/tools.py` and `t2_agent/agent.py`.
It already supports uploaded decay tables, schema repair, L-curve inversion,
fixed NNLS inversion, decay/T2 plotting, Gaussian decomposition, result
interpretation, and Markdown reports.

The referenced NMR simulation repository contains a useful 2D PNG workflow in
`advanced_tools/png_phase_nmr_decay.py`. That script already supports:

- red/yellow/white PNG phase maps;
- white outside-region handling;
- pyGIMLi/Triangle meshing through `--solver triangular`;
- mesh preview PNG;
- `.bms` mesh export;
- mesh quality CSV and histogram;
- T2 decay CSV and PNG;
- physical parameters such as diffusion, bulk T2, surface relaxivity, time step,
  and maximum simulation time.

The target repository also contains larger 3D and T2-T2/D-T2 workflows, but
they are not part of the first version.

## Recommended Architecture

Implement the simulation feature as a new package-level backend inside this
project, then expose it through the existing whitelisted Agent tool system.

Suggested structure:

```text
t2_agent/
  simulation_2d.py       # 2D phase-map, geometry, meshing, decay solve helpers
  tools.py               # new whitelisted simulation + full-workflow tools
  agent.py               # new function schemas and system prompt guidance
streamlit_app.py         # upload types and staged result rendering
tests/
  test_simulation_2d.py
  test_agent_tool_loop.py
  test_streamlit_rendering.py
```

The simulation backend should reuse and adapt the target repository logic
rather than call it as a fragile external script. The app should continue to
use the existing T2 inversion package under `T2process/nmr_t2` for inversion,
plotting, Gaussian decomposition, and result interpretation.

## Workflow Modes

### Mode 1: Standalone T2 Inversion

This remains the current workflow. Users can upload Excel, CSV, TXT, DAT, PEA,
or an existing T2 spectrum and ask for:

- T2 inversion only;
- inversion plus visualization;
- inversion plus Gaussian decomposition;
- visualization or Gaussian decomposition of existing results.

The Agent must keep recognizing this intent and must not force users into
simulation when they only need T2 inversion.

### Mode 2: Full 2D NMR Simulation

The full 2D workflow has two geometry input types:

1. Rule-based geometry.
2. Uploaded PNG phase map.

Both input types produce a standardized decay table, then call the existing T2
inversion tools.

The default inversion after simulation should be L-curve unless the user
explicitly provides a fixed regularization factor.

## PNG Phase-Map Input

PNG input should be documented and validated clearly:

- Red means liquid/water phase and is the solved pore domain.
- Yellow means solid matrix.
- White means outside/background.
- The first version accepts only this red/yellow/white convention.
- The app should reject empty images, images with no liquid pixels, and images
  whose colors are too ambiguous to classify safely.
- White margins around the sample should be cropped automatically before
  simulation.
- The original uploaded image must be preserved, and the cropped/classified
  image should be written as a derived artifact.

The user-facing copy should say "two-phase sample plus optional white outside
background" rather than promising general image segmentation. The agent can
explain that this is not CT segmentation and that the user must supply a
pre-segmented phase map.

## Rule-Based Geometry Input

The first rule-based geometry target should be conservative and close to the
referenced repository's existing triangle workflow:

- two 2D pore bodies;
- optional coupling through a throat;
- user-configurable large/small pore dimensions;
- user-configurable throat length and width when coupling is enabled;
- physical dimensions in micrometers;
- pyGIMLi/Triangle mesh generation only.

This is enough to test the complete pipeline while keeping the first release
understandable.

The UI and Agent should not expose multiple meshers. Mesh generation is fixed
to pyGIMLi for the first version.

## Simulation Parameters

Use beginner-safe defaults, but record them in every summary:

- diffusion coefficient in `um^2/ms`;
- bulk T2 in `ms`;
- solid surface relaxivity in `um/ms`;
- gas/outside relaxivity in `um/ms` for PNG boundaries where applicable;
- time step in `ms`;
- maximum simulation time in `ms`;
- mesh bulk size in `um`;
- mesh boundary size in `um`;
- mesh node safety limit.

The Agent should explain that these are physical modeling assumptions. It can
suggest defaults for testing, but it must not present default physical
parameters as sample-specific truth.

## Tool Design

Add small whitelisted tools rather than one opaque "do everything" command.
Recommended tools:

- `inspect_2d_geometry_input`
  - validates PNG or rule-based geometry parameters;
  - reports phase counts, cropped dimensions, geometry mode, and warnings.

- `run_2d_mesh_and_decay`
  - builds pyGIMLi triangular mesh;
  - saves mesh preview, `.bms`, quality table, quality histogram;
  - solves the NMR/T2 decay;
  - saves decay CSV, decay PNG, and a standardized decay Excel workbook.

- `run_2d_simulation_full_workflow`
  - convenience tool for the Agent when the user asks for the whole flow;
  - internally calls inspection, mesh/decay, existing L-curve or fixed NNLS,
    optional Gaussian decomposition, interpretation, and report generation.

The existing individual T2 tools should remain available so the Agent can still
handle standalone T2 tasks.

## Artifact Contract

Each simulation run should use a run-specific output directory. Do not silently
overwrite previous runs. At minimum, each full run should produce:

- preserved input file or geometry JSON;
- cropped/classified phase preview for PNG input;
- mesh preview PNG;
- pyGIMLi `.bms` mesh;
- mesh quality CSV;
- mesh quality histogram PNG;
- decay CSV;
- decay PNG;
- standardized decay Excel workbook with `time_ms` and `signal`;
- T2 inversion spectrum workbook;
- paired decay/T2 figure;
- L-curve diagnostics or fixed-NNLS summary;
- optional Gaussian peak outputs;
- Markdown report;
- JSON summary containing all key parameters and artifact paths.

The summary should distinguish:

- geometry and image assumptions;
- mesh settings;
- physical parameters;
- inversion parameters;
- generated artifacts;
- warnings and reliability notes.

## Streamlit UI Design

Keep the left column as the Agent conversation and the right column as data and
results, but update the right column to support staged simulation sections:

1. Current input and validation.
2. Geometry/phase preview.
3. Mesh outputs.
4. Decay simulation outputs.
5. T2 inversion outputs.
6. Gaussian/report outputs.

The existing `render_result` behavior already shows image artifacts from tool
results. Extend it so simulation summaries are grouped by stage, rather than
only appearing as a flat list.

The uploader should accept PNG in addition to the existing table formats.
When a PNG is active, upload hints should mention the required red/yellow/white
phase convention and the fact that the file will not run until the user asks
the Agent to simulate.

## Agent Behavior

Update the system prompt so the Agent knows it is now an NMR simulation and T2
inversion assistant, not only a T2 inversion assistant.

The Agent should classify user intent into:

- standalone T2 inversion;
- full 2D simulation from PNG;
- full 2D simulation from rule geometry;
- full simulation plus Gaussian decomposition;
- simulation test/demo run;
- existing T2 spectrum interpretation or decomposition.

The Agent should ask only the missing questions needed to run safely:

- For PNG: confirm physical pixel size or physical width/height if not obvious.
- For rule geometry: confirm coupling and key dimensions if the user does not
  accept defaults.
- For physical modeling: use defaults for a test run, but state that these are
  test defaults.
- For inversion: use L-curve by default unless the user provides fixed
  regularization.

The Agent should report intermediate progress in scientific language:

- mesh generated and quality checked;
- decay curve solved;
- T2 inversion completed;
- Gaussian peaks interpreted if requested.

## Error Handling

PNG validation should fail clearly when:

- the file is missing or not a valid PNG;
- there are no red/liquid pixels;
- there are no yellow/solid pixels when solid boundaries are expected;
- the image is too large and would exceed the mesh node guard;
- pyGIMLi is missing;
- meshing returns no triangular cells;
- the decay curve has too few valid points for inversion.

Failures should preserve any earlier-stage artifacts. For example, if inversion
fails after meshing, the mesh preview and decay outputs should still show in
the right results column.

## Testing Strategy

Use focused tests that prove the new workflow without requiring a large
production simulation:

- create a tiny synthetic red/yellow/white PNG fixture in a temp directory;
- validate that white borders are cropped and phase counts are reported;
- run a small triangular mesh/decay smoke test when pyGIMLi is available;
- skip pyGIMLi-dependent tests gracefully when pyGIMLi is not installed;
- verify decay CSV is converted into a standard Excel workbook;
- verify full workflow calls existing L-curve or fixed NNLS using that workbook;
- verify Agent tool schemas expose the new simulation tools;
- verify PNG uploads are accepted by Streamlit;
- verify zip packaging preserves simulation stage folders.

Existing T2 tests should continue to pass, proving standalone inversion is not
regressed.

## Dependencies

The first implementation will need the following additional runtime
dependencies:

- `Pillow` for PNG reading;
- `scikit-image` for contour extraction if reusing the target PNG workflow;
- `pygimli` for pyGIMLi/Triangle meshing.

If `pygimli` is difficult to install in Streamlit Community Cloud, the app
should report a clear environment error rather than falling back to a different
mesher. The user explicitly requested pyGIMLi only for this flow.

## Open Decisions

These do not block the first design, but should be confirmed before broad use:

- exact default physical dimensions for PNG input when no pixel size is given;
- whether red/yellow mapping should become configurable in a future release;
- whether rule geometry should start with only the two-triangle benchmark or
  also include rectangles/circles in the first release;
- whether Gaussian decomposition should be automatic after every simulation or
  only when requested.

For the first version, use the simplest defaults:

- PNG physical scale must be provided by the user or defaults to `1 um/pixel`
  with a visible warning;
- red/yellow/white mapping is fixed;
- rule geometry starts with the coupled/uncoupled two-pore benchmark;
- Gaussian decomposition is optional and request-driven.
