import asyncio
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import async_engine, async_session_factory
from app.services.replenishment import AutoReplenishmentService


async def periodic_replenishment_worker():
    """Background polling task running on configured intervals."""
    while True:
        try:
            await asyncio.sleep(settings.AUTO_REPLENISH_INTERVAL_SECONDS)
            async with async_session_factory() as session:
                service = AutoReplenishmentService(session)
                await service.run_replenishment_scan()
        except asyncio.CancelledError:
            break
        except Exception:
            # Prevent unexpected database disconnections from terminating the event loop
            await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = None
    if settings.AUTO_REPLENISH_ENABLED and settings.AUTO_REPLENISH_INTERVAL_SECONDS > 0:
        worker_task = asyncio.create_task(periodic_replenishment_worker())

    yield

    if worker_task:
        worker_task.cancel()
        with suppress(asyncio.CancelledError):
            await worker_task

    await async_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}
