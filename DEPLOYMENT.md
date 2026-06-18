# Public Deployment

This app includes a full pyGIMLi triangular-mesh 2D NMR simulation workflow.
For that workflow, deploy from GitHub to a public host that supports Docker or
conda environments. Pure pip-only Streamlit Community Cloud builds may not
install pyGIMLi reliably.

## Local run

```bash
conda env create -f environment.yml
conda activate t2agent
python scripts/check_t2agent_env.py
streamlit run streamlit_app.py
```

## Secrets

Set the DeepSeek key in Streamlit Cloud secrets:

```toml
DEEPSEEK_API_KEY = "your-new-key"
```

Do not commit `.streamlit/secrets.toml`.

The web page also includes a password input for users to provide their own
DeepSeek API key at runtime. Runtime input takes priority over Streamlit
Secrets and is not written to disk by the app.

## Entry point

Use this file as the Streamlit entry point:

```text
streamlit_app.py
```

## Recommended public Docker deployment

Use the repository `Dockerfile`. It creates the `t2agent` conda environment
from `environment.yml` and starts:

```bash
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Recommended GitHub-backed hosts:

- Hugging Face Spaces with Docker SDK.
- Render Web Service from Dockerfile.
- Railway Dockerfile deployment.
- Any VPS or container host that builds the repository Dockerfile.

After deployment, verify the public app by running a rule-geometry request:

```text
用默认规则几何跑完整二维 NMR 模拟，并做 T2 反演
```

The result should include geometry preview, pyGIMLi mesh image/BMS, mesh
quality CSV/histogram, simulated decay workbook, and an L-curve T2 spectrum.

## Streamlit Community Cloud note

If you still create an app from Streamlit Community Cloud, use:

- Repository: `shizaishiwo323/t2-inversion-agent`
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python version: a supported Python 3 version, preferably Python 3.12

This mode is suitable only if pyGIMLi installs successfully on the Cloud build
image. For the required pyGIMLi mesh workflow, Docker/conda deployment is the
supported public path.

If you want the public app to have a default DeepSeek key, add it through
Streamlit Cloud **Advanced settings -> Secrets**. If you leave secrets empty,
the app still works, but each user must enter their own DeepSeek API key in the
web page.

## Notes

- Uploaded files and generated results are stored in the local `runs/` directory.
- On Streamlit Cloud this storage is temporary, so users should download the result zip.
- The agent uses DeepSeek function calling to choose whitelisted Python tools from `t2_agent.tools`; it does not execute arbitrary shell commands.
