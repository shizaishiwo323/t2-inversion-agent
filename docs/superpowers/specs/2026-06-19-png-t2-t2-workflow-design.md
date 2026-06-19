# PNG T2-T2 Workflow Design

## Goal

Add the recently validated PNG phase-map workflow to the existing T2 agent system: safe phase-color normalization, white-border cropping, physical-size-based pixel scaling, pyGIMLi triangular T2 simulation, L-curve T2 inversion, paired plotting, and a reduced T2-T2 map derived from the simulated T2 spectrum.

## Scope

This is an enhancement of the existing `run_2d_simulation_full_workflow` path, not a new parallel agent workflow. The PNG workflow remains 2D and uses pyGIMLi/Triangle for meshing. The T2-T2 output is a reduced diagnostic map generated from the recovered 1D T2 spectrum; it must be labeled as such and must not be presented as a strict arbitrary-PNG exchange PDE solve.

## Data Flow

For uploaded PNG phase maps, the agent should optionally normalize near red/yellow/white colors into exact project phase colors while preserving the original uploaded image. The normalized image is a derived artifact. The normalized image then goes through the existing white-border crop logic. Physical size parameters, such as `physical_size_x_um=300` and `physical_size_y_um=300`, are applied to the cropped red/yellow sample area, not the full screenshot canvas.

The cropped phase map enters the existing pyGIMLi triangular mesh and T2 decay solver. The generated standard decay workbook is sent through the existing L-curve or fixed NNLS inversion tools. If requested, a reduced T2-T2 stage builds a 2D synthetic signal from the 1D T2 distribution and inverts it into a map table and figure.

## Agent And UI Behavior

The tool schema should expose physical size, color normalization, and reduced T2-T2 options on `inspect_2d_geometry_input`, `run_2d_mesh_and_decay`, and `run_2d_simulation_full_workflow` where appropriate. The system prompt should guide the agent to use `physical_size_x_um` and `physical_size_y_um` when the user gives sample dimensions.

The right-side result panel should continue using `simulation_stages`. The reduced T2-T2 artifacts should be grouped under the existing `t2_t2` stage. Existing T2-only workflows, ideal-triangle workflows, standalone workbook inversion, Gaussian decomposition, and batch workbook processing should keep their current behavior.

## Error Handling

If a PNG contains unsupported colors, the agent may normalize colors only when `normalize_phase_colors` is enabled. The normalization must write a derived PNG and a summary of source color counts. If normalization is disabled and unsupported colors remain, the workflow should fail with the existing clear color error.

If physical size is absent, the workflow should keep the existing `pixel_size_um` or `pixel_size_x_um`/`pixel_size_y_um` behavior. If physical size is present, it should be computed after cropping and should override raw pixel-size defaults for PNG mode.

## Tests

Tests should cover safe color normalization, cropped-size-based physical scaling, reduced T2-T2 artifact generation, tool schema exposure, and full workflow stage metadata. Existing pyGIMLi-dependent tests may be skipped when pyGIMLi is unavailable.
