FROM condaforge/miniforge3:latest

WORKDIR /app
ENV PYTHONNOUSERSITE=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8

COPY environment.yml requirements.txt /app/
RUN mamba env create -f /app/environment.yml && mamba clean -afy

COPY . /app

EXPOSE 8501

CMD ["conda", "run", "--no-capture-output", "-n", "t2agent", "streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"]
