import logging
import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import analyze, report, statistics

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("nusaguard")
app = FastAPI(title="NusaGuard API", version="1.0.0", description="Analisis pesan ephemeral: isi pesan tidak dicatat dalam log atau histori analisis.")
origins = [item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if item.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-API-Key"])

@app.middleware("http")
async def metadata_logging(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    logger.info("method=%s path=%s status=%s duration_ms=%.1f", request.method, request.url.path, response.status_code, (time.perf_counter()-started)*1000)
    return response

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}

app.include_router(analyze.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(statistics.router, prefix="/api")
