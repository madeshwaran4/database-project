import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.config import settings
from app.core.middleware import SecurityHeadersMiddleware, RateLimiterMiddleware
from app.db.pool import init_db_pool, close_db_pool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("securevote")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up %s v%s...", settings.APP_NAME, settings.APP_VERSION)
    init_db_pool()
    yield
    # Shutdown
    logger.info("Shutting down %s...", settings.APP_NAME)
    close_db_pool()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SecureVote - High-integrity duplicate-vote prevention system.",
    lifespan=lifespan,
)

# Custom Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimiterMiddleware, max_requests=settings.RATE_LIMIT_PER_MINUTE)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the election administrator."},
    )


# Register routes
app.include_router(api_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_url": "/health",
    }
