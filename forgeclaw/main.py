from contextlib import asynccontextmanager
import logging
import re
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from forgeclaw.api.developer_routes import router as developer_router
from forgeclaw.api.routes import router
from forgeclaw.core.logging import configure_logging
from forgeclaw.core.settings import settings
from forgeclaw.storage.database import initialize_database

configure_logging()
logger = logging.getLogger("forgeclaw.http")
WEB_INDEX = Path(__file__).resolve().parent / "web" / "index.html"


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database(settings.database_path)
    logger.info("application_started", extra={"event": "application_started"})
    yield
    logger.info("application_stopped", extra={"event": "application_stopped"})


app = FastAPI(title="ForgeClaw", description="A self-hosted multi-agent debate and coding workspace.",
              version="0.4.0", lifespan=lifespan, docs_url="/docs", redoc_url=None)


@app.middleware("http")
async def request_observability(request: Request, call_next):
    supplied_id = request.headers.get("x-request-id", "").strip()[:128]
    request_id = supplied_id if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", supplied_id) else str(uuid4())
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "no-cache"
        return response
    except Exception:
        logger.exception("request_failed", extra={"event": "request_failed", "request_id": request_id,
            "method": request.method, "path": request.url.path, "status_code": 500,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": request_id},
                            headers={"X-Request-ID": request_id, "X-Content-Type-Options": "nosniff",
                                     "X-Frame-Options": "DENY"})
    finally:
        logger.info("request_complete", extra={"event": "request_complete", "request_id": request_id,
            "method": request.method, "path": request.url.path, "status_code": status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2)})


app.include_router(router)
app.include_router(developer_router)


@app.get("/", include_in_schema=False)
def root():
    return {"service": "forgeclaw", "ui": "/ui", "docs": "/docs", "health": "/health"}


@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def control_room():
    if not WEB_INDEX.is_file():
        logger.error("control_room_asset_missing", extra={"event": "asset_missing"})
        return HTMLResponse("Control Room UI asset is missing. Reinstall ForgeClaw package.", status_code=500)
    return HTMLResponse(WEB_INDEX.read_text(encoding="utf-8"))


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "forgeclaw"}


@app.get("/ready", tags=["system"])
def readiness() -> dict[str, str]:
    from forgeclaw.storage.database import check_database
    check_database(settings.database_path)
    return {"status": "ready", "service": "forgeclaw"}
