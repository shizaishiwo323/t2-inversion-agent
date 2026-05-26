# T2 Inversion Agent

## Project Purpose

This project builds a simplified AI agent for NMR T2 inversion workflows.
The agent should help users move from uploaded decay data to T2 inversion,
visualization, optional peak decomposition, and result interpretation.

The intended experience is conversational and guided. The agent should not
expect new users to already understand terms such as regularization factor,
L-curve, T2 spectrum, or Gaussian peak decomposition. It should explain each
choice in practical scientific language, ask only the questions needed to
finish the task, and then call the local T2 processing code to produce files
and figures.

This is a focused T2-processing agent, not a full geophysics simulation agent.
Ideas from `AI_for_Geophysics智能体会议纪要_整理版.md` provide the broader
agent-workflow philosophy, but the current project scope is limited to the
existing T2 inversion and spectrum-processing capabilities in `T2process`.

## Core User Workflow

The agent should guide the user through these stages:

1. Understand the user's goal.
   - T2 inversion only.
   - T2 inversion plus visualization.
   - T2 inversion plus Gaussian peak decomposition.
   - Visualization of existing inversion results.
   - Gaussian decomposition of an existing T2 spectrum.

2. Inspect the uploaded data.
   - Accept Excel workbooks as the primary input format.
   - Expect the first column to contain time values.
   - Expect one or more following columns to contain decay signal amplitudes.
   - Detect valid numeric rows even when time cells contain strings such as
     scientific notation or simple text with units.
   - Tell the user clearly if the table is empty, has no valid time column,
     has no valid signal column, or has too few valid data points.
   - When safe and unambiguous, normalize the data format internally instead
     of forcing the user to edit the table manually.

3. Ask for required scientific and processing choices.
   - Whether the time column is already in milliseconds or needs conversion
     from seconds to milliseconds.
   - Whether the signal should be trimmed from the global peak before
     inversion.
   - Whether to use fixed regularization or L-curve automatic selection.
   - T2 range and number of T2 bins, if the user needs non-default settings.
   - Number of Gaussian peaks, if peak decomposition is requested.
   - Output location and preferred result artifacts.

4. Run the local processing code.
   - Use the standardized Python package under `T2process/nmr_t2`.
   - Do not reimplement inversion, L-curve, plotting, or Gaussian fitting
     logic in the web layer when the package already provides it.

5. Explain results.
   - Summarize generated files.
   - Explain selected regularization values and whether L-curve selection was
     used.
   - Explain T2 peak positions, areas, and area fractions when Gaussian
     decomposition is performed.
   - Warn when data quality, point count, noise, or chosen peak count may make
     the interpretation unreliable.

## Local T2 Processing Capabilities

The available processing code is in `T2process/nmr_t2`.

### Fixed-Regularization NNLS Inversion

Main callable workflow:

- `nmr_t2.pipelines.run_nnls_workbook`

Purpose:

- Converts decay data into a T2 spectrum using NNLS inversion with a user-set
  regularization factor.

Important parameters:

- `regularization`: smoothing/regularization weight. Larger values generally
  make the T2 spectrum smoother but may merge real peaks. Smaller values can
  preserve sharper structure but may amplify noise.
- `t2_min_ms` and `t2_max_ms`: lower and upper T2 search bounds in ms.
- `num_bins`: number of logarithmic T2 bins.
- `trim_from_peak`: whether to start inversion from the global maximum.
- `time_to_ms_scale`: multiplier used to convert input time to milliseconds.

Default configuration:

- `num_bins = 200`
- `regularization = 1.0`
- `t2_min_ms = 1.0`
- `t2_max_ms = 10000.0`
- `min_points_after_trim = 10`

Generated artifacts:

- `*_nnls_spectrum.xlsx`
- `*_nnls_trimmed_decay.xlsx`
- `*_nnls_fit.xlsx`
- `*_nnls_summary.csv`
- `*_nnls_summary.xlsx`

### L-Curve Regularization Selection

Main callable workflow:

- `nmr_t2.pipelines.run_lcurve_workbook`

Purpose:

- Tests a range of regularization values and selects a preferred value using
  the L-curve reciprocal-slope criterion.

Use this mode when:

- The user does not know how to choose a regularization factor.
- The user wants a more defensible automatic choice.
- The user is doing exploratory inversion and wants diagnostic plots.

Explain to users:

- The regularization factor balances data fitting against smoothness.
- Very weak regularization may fit noise.
- Very strong regularization may hide real pore-size or relaxation components.
- L-curve selection searches for a compromise between these two effects.

Default configuration:

- `num_bins = 200`
- `t2_min_ms = 0.01`
- `t2_max_ms = 100000.0`
- `alpha_min = 1e-6`
- `alpha_max = 1e2`
- `alpha_count = 60`
- `slope_reciprocal_target = 0.25`
- `slope_reciprocal_valid_range = (0.1, 10.0)`
- `min_points_after_trim = 10`

Generated artifacts:

- `*_lcurve_spectrum.xlsx`
- `*_lcurve_metrics.xlsx`
- `*_lcurve_trimmed_decay.xlsx`
- `*_lcurve_summary.csv`
- `*_lcurve_summary.xlsx`
- L-curve diagnostic figures.

### Decay and T2 Spectrum Visualization

Main callable workflow:

- `nmr_t2.pipelines.run_plotting_workbook_pair`

Purpose:

- Generates paired figures showing raw decay data and the corresponding T2
  spectrum.

Input requirements:

- A raw decay workbook.
- A spectrum workbook produced by NNLS or L-curve inversion.

Generated artifacts:

- `*_decay_t2.png`

### Gaussian Peak Decomposition

Main callable workflow:

- `nmr_t2.pipelines.run_gaussian_decomposition_on_spectrum_workbook`

Purpose:

- Fits the T2 spectrum as a sum of Gaussian components in log10(T2) space.

Important parameters:

- `peak_count`: number of peaks/components to fit.
- `max_function_evals`: maximum fitting function evaluations.
- `max_iterations`: fallback optimizer iteration limit.

Default configuration:

- `peak_count = 3`
- `max_function_evals = 20000`
- `max_iterations = 2000`

Explain to users:

- Peak decomposition is an interpretation aid, not a guarantee that the sample
  truly has exactly that many physical pore populations.
- More peaks can fit complex spectra but may overfit noise.
- Fewer peaks are easier to interpret but may merge distinct relaxation
  components.
- If the user has no prior knowledge, suggest starting with 2 or 3 peaks and
  comparing fit quality and interpretability.

Generated artifacts:

- `*_gaussian_peak_table.xlsx`
- `*_gaussian_fit.xlsx`
- `*_gaussian_summary.csv`
- `*_gaussian_summary.xlsx`
- Gaussian decomposition figures.

## Agent Guidance Principles

The agent should behave like a scientific workflow assistant.

- First clarify the user's scientific goal, not just the button they want to
  press.
- Use defaults when the user is unsure, but state what the default means.
- Prefer L-curve regularization for beginner users unless they explicitly know
  the fixed regularization value they want.
- Ask for fixed regularization only when the user has prior runs, a reference
  method, or a reason to reproduce a specific setting.
- Ask about time units early because wrong time scaling changes the physical
  meaning of T2.
- Ask about trimming from the global peak, especially for simulated data with
  an initial rise before decay.
- Do not overwhelm the user with all parameters at once.
- After each run, give a short interpretation and list generated files.
- When results are uncertain, say why instead of presenting them as final
  scientific truth.

## Suggested Beginner Defaults

When the user is unsure:

- Use L-curve inversion.
- Use `time_to_ms_scale = 1.0` if time is already in ms.
- Use `time_to_ms_scale = 1000.0` if time is in seconds.
- Use `trim_from_peak = true` for simulation-style data that rises before
  decaying.
- Use `trim_from_peak = false` for clean experimental decay data that starts
  at the maximum.
- Use default T2 bounds unless the user knows the expected relaxation range.
- For Gaussian decomposition, start with `peak_count = 2` or `3` depending on
  the visible spectrum complexity.

## Web Application Expectations

The web app should provide:

- File upload for Excel data.
- Data preview and validation feedback.
- Model selection UI for the language agent.
- A guided parameter panel driven by the agent conversation.
- Controls for fixed NNLS, L-curve inversion, plotting, and Gaussian
  decomposition.
- Output file download links.
- Figure previews.
- Clear warnings when input format or parameters are unsuitable.

DeepSeek API credentials must be read from environment variables, not hardcoded
in source files or documentation.

Recommended environment variable:

- `DEEPSEEK_API_KEY`

The API base URL can be configured separately:

- `DEEPSEEK_BASE_URL=https://api.deepseek.com`

## Model Selection Expectations

The web app should let users choose among available DeepSeek-compatible modes
or aliases configured by the project, such as:

- A fast chat mode for ordinary guidance.
- A stronger reasoning mode for complex parameter decisions.
- A non-reasoning mode when the user wants faster, simpler interaction.

Model display names in the UI may be user-friendly, but backend code should map
them to explicit provider model IDs in one place.

## Data and File Safety

- Do not store API keys in the repository.
- Do not silently overwrite important user outputs unless the output directory
  is clearly run-specific or the user confirms replacement.
- Preserve raw uploaded data.
- Write normalized or repaired data as a new derived artifact.
- Keep enough provenance in summaries to reproduce the run.

## Repository Operating Rules

The following rules apply to all agents working in this repository:

- Do not batch-delete files or directories.
- Do not use `del /s`, `rd /s`, `rmdir /s`, `Remove-Item -Recurse`, or
  `rm -rf`.
- If a file must be deleted, delete only one explicit file path at a time.
- If many files need deletion, stop and ask the user to delete them manually.
- Unless otherwise specified, run Python using the conda `base` environment.

