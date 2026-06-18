# NMR Simulation and T2 Inversion Agent

A Streamlit-based AI workflow assistant for NMR 2D simulation and T2 inversion.
The app combines DeepSeek-guided conversation with a whitelisted local Python
tool layer for PNG/rule-geometry simulation, pyGIMLi triangular meshing, T2
decay solving, data diagnosis, workbook repair, T2 inversion, visualization,
Gaussian peak decomposition, result interpretation, and report generation.

## What It Does

- Guides beginner users through T2 inversion choices in plain language.
- Detects flexible Excel layouts instead of assuming the first column is time.
- Repairs safe nonstandard workbooks into `time_ms + signal` format.
- Runs L-curve inversion when users do not know the smoothing factor.
- Runs fixed-regularization NNLS when users provide a smoothing factor.
- Generates plots, Gaussian peak fits, interpretation notes, reports, and a
  zip download for all outputs created during a task.
- Runs a first-version 2D NMR simulation workflow from rule geometry or PNG
  phase maps into the existing T2 inversion tools.
- Supports Chinese and English UI switching.

## 2D NMR Simulation Workflow

The app can also run a first-version 2D NMR simulation workflow:

```text
rule geometry or red/yellow/white PNG -> pyGIMLi triangular mesh -> T2 decay solve -> T2 inversion
```

PNG phase maps must use:

- red for liquid/water pore space;
- yellow for solid matrix;
- white for outside/background.

White borders are cropped automatically. The first version supports 2D only
and does not perform CT segmentation, 3D simulation, T2-T2, or D-T2.

## Local Run

```bash
conda env create -f environment.yml
conda activate t2agent
python scripts/check_t2agent_env.py
streamlit run streamlit_app.py
```

The full 2D simulation workflow requires `pygimli` and uses the pyGIMLi
triangular mesh path. Do not use `base` unless `python
scripts/check_t2agent_env.py` confirms that all required packages are present.

Set a local DeepSeek key in `.streamlit/secrets.toml` or enter it in the web
page:

```toml
DEEPSEEK_API_KEY = "your-key"
```

Do not commit `.streamlit/secrets.toml`.

## Public Deployment

The pyGIMLi mesh workflow is best deployed from GitHub to a container-capable
public host such as Hugging Face Spaces Docker, Render, Railway, or another
Docker platform. This repository includes:

- `environment.yml` for the `t2agent` conda environment.
- `Dockerfile` for public deployment with the same conda environment.
- `scripts/check_t2agent_env.py` for dependency verification.

Pure pip-only hosts may fail to install pyGIMLi. For full public operation,
use the Dockerfile rather than a plain Streamlit Community Cloud build. If no
Cloud secret is configured, users can still provide their own DeepSeek API key
in the page.

## Safety Boundary

DeepSeek only chooses among whitelisted Python tools. It does not execute
arbitrary shell commands from user input.
