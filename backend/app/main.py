import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import Base, engine
from app.routers import auth, employees, attendance, timeoff, payroll

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hrms")

app = FastAPI(
    title="HRMS API",
    description="Human Resource Management System - hackathon backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- graceful error handling
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Turn pydantic's verbose error format into a flat, frontend-friendly list."""
    errors = [
        {"field": ".".join(str(p) for p in err["loc"][1:]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Please fix the highlighted fields.", "errors": errors},
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning("Integrity error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "That action conflicts with existing data (e.g. a duplicate email or ID)."},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong on our end. Please try again."},
    )


# ---------------------------------------------------------------- routers
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(timeoff.router)
app.include_router(payroll.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    # Creates tables if they don't exist yet (schema.sql is the reviewable
    # source of truth; this line makes `uvicorn app.main:app` work out of the box).
    Base.metadata.create_all(bind=engine)
