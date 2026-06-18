# T2 Inversion Agent

A Streamlit-based AI workflow assistant for NMR T2 inversion. The app combines
DeepSeek-guided conversation with a whitelisted local Python tool layer for
data diagnosis, workbook repair, T2 inversion, visualization, Gaussian peak
decomposition, result interpretation, and report generation.

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
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Set a local DeepSeek key in `.streamlit/secrets.toml` or enter it in the web
page:

```toml
DEEPSEEK_API_KEY = "your-key"
```

Do not commit `.streamlit/secrets.toml`.

## Streamlit Community Cloud

Deploy with:

- Main file path: `streamlit_app.py`
- Dependencies: `requirements.txt`
- Config: `.streamlit/config.toml`

If no Cloud secret is configured, users can still provide their own DeepSeek
API key in the page.

## Safety Boundary

DeepSeek only chooses among whitelisted Python tools. It does not execute
arbitrary shell commands from user input.
