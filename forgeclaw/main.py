from contextlib import asynccontextmanager

from fastapi import FastAPI

from forgeclaw.api.routes import router
from forgeclaw.core.settings import settings
from forgeclaw.storage.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database(settings.database_path)
    yield


app = FastAPI(
    title="ForgeClaw",
    description="A self-hosted multi-agent debate and coding workspace.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "forgeclaw"}
