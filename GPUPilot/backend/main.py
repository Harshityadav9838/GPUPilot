import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from api.routes import router
from gpu.detector import detect_gpu

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("GPUPilot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing GPUPilot Backend...")
    provider = detect_gpu()
    info = provider.get_info()
    logger.info(f"Active Provider: {info.provider_type} (Vendor: {info.vendor}, Demo: {info.is_demo})")
    yield
    logger.info("Shutting down GPUPilot Backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Universal AI GPU Performance Engineer Backend",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_PREFIX)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main.py:app", host=settings.HOST, port=settings.PORT, reload=True)
