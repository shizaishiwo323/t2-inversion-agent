# Streamlit Cloud Deployment

This app is designed for Streamlit Community Cloud.

## Local run

```bash
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

## Streamlit Community Cloud settings

When creating the app from Streamlit Community Cloud, use:

- Repository: `shizaishiwo323/t2-inversion-agent`
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python version: a supported Python 3 version, preferably Python 3.12

If you want the public app to have a default DeepSeek key, add it through
Streamlit Cloud **Advanced settings -> Secrets**. If you leave secrets empty,
the app still works, but each user must enter their own DeepSeek API key in the
web page.

## Notes

- Uploaded files and generated results are stored in the local `runs/` directory.
- On Streamlit Cloud this storage is temporary, so users should download the result zip.
- The agent uses DeepSeek function calling to choose whitelisted Python tools from `t2_agent.tools`; it does not execute arbitrary shell commands.
