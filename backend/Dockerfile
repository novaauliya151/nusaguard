FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements-ml.txt

COPY app app
COPY scripts scripts
COPY model model

ENV PORT=8000
ENV NUSAGUARD_MODEL_PATH=/app/model/indobert
ENV NUSAGUARD_MODEL_REPO=indobenchmark/indobert-base-p1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
