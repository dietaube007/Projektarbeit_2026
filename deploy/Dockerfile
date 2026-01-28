# Multi-Stage Build für kleinere Image-Größe
# Stage 1: Build-Stage für torch/transformers
FROM python:3.11-slim as builder

WORKDIR /build

# System dependencies nur für Build (können später entfernt werden)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installiere torch CPU-only (spart ~2-3GB vs. vollständiges torch)
# torch CPU-only ist deutlich kleiner als torch mit CUDA
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Installiere andere Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir \
    flet==0.28.3 \
    pillow>=10.0.0 \
    python-dotenv>=1.0.0 \
    supabase>=2.0.0 \
    transformers>=4.30.0 \
    numpy>=1.24.0

# Stage 2: Final-Stage - nur Runtime-Dependencies
FROM python:3.11-slim

WORKDIR /app

# Nur minimale System-Dependencies für Runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Kopiere Python-Pakete aus Builder-Stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Kopiere App-Code
COPY . .

# Create upload directory
RUN mkdir -p image_uploads

# Expose port
EXPOSE 8080

# Run app
CMD ["python", "main.py"]
