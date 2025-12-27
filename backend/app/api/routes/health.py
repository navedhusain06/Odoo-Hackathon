from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import SessionLocal

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/db")
def health_db():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"db": "ok"}
