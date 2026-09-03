import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Response
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.api.routes import admin, analyze, auth, content, report, statistics, user
from app.services.store import admin_domain, store
from app.services.request_context import request_agent, request_ip
from app.services.predictor import _pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("nusaguard")

@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.getenv("NUSAGUARD_WARM_MODEL", "true").casefold() == "true":
        started = time.perf_counter()
        source = "indobert" if _pipeline() is not None else "rules-fallback"
        logger.info("model_warmup source=%s duration_ms=%.1f", source, (time.perf_counter()-started)*1000)
    yield

app = FastAPI(title="NusaGuard API", version="1.0.0", description="Analisis pesan ephemeral: isi pesan tidak dicatat dalam log atau histori analisis.", lifespan=lifespan)
origins = [item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if item.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Content-Type", "Authorization"])
os.makedirs("uploads/education", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.middleware("http")
async def metadata_logging(request: Request, call_next):
    started = time.perf_counter()
    ip_token = request_ip.set(request.client.host if request.client else None)
    agent_token = request_agent.set(request.headers.get("user-agent"))
    try:
        exempt = request.url.path.startswith(("/api/admin", "/api/auth", "/health", "/uploads"))
        if not exempt and admin_domain.setting_enabled("system", "maintenance_mode", False):
            return JSONResponse({"detail": "NusaGuard sedang dalam pemeliharaan terjadwal."}, status_code=503)
        response = await call_next(request)
        logger.info("method=%s path=%s status=%s duration_ms=%.1f", request.method, request.url.path, response.status_code, (time.perf_counter()-started)*1000)
        return response
    finally:
        request_ip.reset(ip_token)
        request_agent.reset(agent_token)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}

@app.get("/health/ready", tags=["system"])
def readiness(response: Response):
    model_path = Path(os.getenv("NUSAGUARD_MODEL_PATH", Path(__file__).resolve().parents[1] / "model" / "indobert"))
    model_available = (model_path / "config.json").exists() or bool(os.getenv("NUSAGUARD_MODEL_REPO"))
    try:
        with store.engine.connect() as db: db.execute(text("SELECT 1")).scalar_one()
        database = True
    except Exception:
        database = False
    require_model = os.getenv("REQUIRE_INDOBERT", "false").casefold() == "true"
    ready = database and (model_available or not require_model)
    if not ready: response.status_code = 503
    return {"status":"ready" if ready else "not_ready","database":database,"indobert_configured":model_available,"indobert_required":require_model,"fallback_allowed":not require_model}

app.include_router(analyze.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(statistics.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(content.router, prefix="/api")
app.include_router(user.router, prefix="/api")


