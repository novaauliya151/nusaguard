FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements-ml.txt

COPY app app
COPY scripts scripts
COPY model model
ENV NUSAGUARD_MODEL_PATH=/app/model/indobert
RUN mkdir -p /app/uploads/education /app/model/indobert \
    && useradd --create-home --uid 10001 nusaguard \
    && chown -R nusaguard:nusaguard /app
USER nusaguard
EXPOSE 7860
CMD ["sh", "-c", "python scripts/bootstrap_model.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
