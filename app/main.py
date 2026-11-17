from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.api.auth import router as auth_router
from app.db.session import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Veterinary Clinic IS", version="0.8.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request, error):
    # Never echo passwords, raw JSON or arbitrary user input in error responses.
    malformed = any(item["type"] == "json_invalid" for item in error.errors())
    return JSONResponse(status_code=400 if malformed else 422, content={"detail": [
        {"loc": list(item["loc"]), "type": item["type"], "msg": "Жарамсыз дерек"}
        for item in error.errors()
    ]})


@app.get("/")
def root():
    return {"status": "ok", "system": "Veterinary Clinic IS", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
