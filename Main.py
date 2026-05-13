from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from App.Database import engine, Base
from App.Models import User, Student, AuditLog, Course
from App.Routes import Auth, Students, Monitoring, Courses
from App.Utils.Logger import logger
import time
import os

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Student Management System",
    version="1.0.0",
    description=(
        "A secure backend API for managing university students. "
        "Supports JWT authentication, role-based access control (Admin / Student), "
        "Redis caching, structured logging, and a live monitoring dashboard."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every incoming request and collect metrics for the dashboard."""
    start_time = time.time()
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000, 2)

    endpoint = request.url.path
    log_line = f"{request.method} {endpoint} -> {response.status_code} ({duration}ms)"

    logger.info(log_line)

    # Update in-memory metrics used by /monitoring/dashboard
    Monitoring.metrics["endpoint_counts"][endpoint] = (
        Monitoring.metrics["endpoint_counts"].get(endpoint, 0) + 1
    )
    Monitoring.metrics["total_requests"] += 1
    Monitoring.metrics["response_times"].append(duration)

    # Keep only last 1 000 response-time samples
    if len(Monitoring.metrics["response_times"]) > 1000:
        Monitoring.metrics["response_times"] = Monitoring.metrics["response_times"][-1000:]

    if response.status_code >= 400:
        Monitoring.metrics["errors"] += 1

    Monitoring.metrics["recent_logs"].append(log_line)
    if len(Monitoring.metrics["recent_logs"]) > 100:
        Monitoring.metrics["recent_logs"] = Monitoring.metrics["recent_logs"][-100:]

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler that logs unhandled exceptions and returns a safe 500."""
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Register all routers
app.include_router(Auth.router)
app.include_router(Students.router)
app.include_router(Courses.router)
app.include_router(Monitoring.router)

# Serve the frontend SPA if the directory exists
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")


@app.get("/", tags=["Root"])
def root():
    """API entry point — lists key URLs."""
    return {
        "message": "Student Management API is running",
        "docs": "/docs",
        "redoc": "/redoc",
        "dashboard": "/monitoring/dashboard",
        "health": "/monitoring/health",
    }