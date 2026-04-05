FROM continuumio/miniconda3:latest

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install cadquery via conda (needs OCP from conda-forge, requires python <=3.12)
RUN conda install -y -c conda-forge python=3.12 cadquery=2.4.0 && conda clean -afy

# Install remaining Python deps via pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8501

HEALTHCHECK CMD ["curl", "-f", "http://localhost:8501/_stcore/health"]

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
