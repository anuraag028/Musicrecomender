import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from backend.app.config import settings, redact_secrets
from backend.app.database import engine, Base, SessionLocal
from backend.app.logging_config import record_log
from backend.app.services.catalogue_service import CatalogueService

# Import routers
from backend.app.routes import health, users, music, interactions, recommendations, diagnostics, twsma

@asynccontextmanager
async def lifespan(app: FastAPI):
    record_log("INFO", "Initializing database tables and seed state...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        CatalogueService.ensure_demo_users(db)
        record_log("INFO", "Demo users initialized successfully.")
    except Exception as e:
        record_log("ERROR", f"Error during startup initialization: {str(e)}")
    finally:
        db.close()
    yield
    record_log("INFO", "Application shutting down.")

app = FastAPI(
    title="Social-Aware Hybrid Music Recommendation System",
    description="Combines Content-Based, Collaborative, Trend, and Text/Social Media Analytics (TWSMA) with strict data integrity and numeric explainability.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID & Performance Logging Middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:10]}"
    start_time = time.time()
    
    try:
        response: Response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        if request.url.path != "/api/health":
            record_log(
                level="INFO" if response.status_code < 400 else "WARNING",
                message=f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
        return response
    except (StarletteHTTPException, RequestValidationError):
        # Let FastAPI's default handlers handle these
        raise
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        record_log(
            level="ERROR",
            message=f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=500,
            duration_ms=duration_ms
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred.", "request_id": request_id}
        )

# Include routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(music.router)
app.include_router(interactions.router)
app.include_router(recommendations.router)
app.include_router(diagnostics.router)
app.include_router(twsma.router)

@app.get("/")
def root():
    return {
        "name": "Social-Aware Hybrid Music Recommendation System API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }
