"""Seed initial users for login tests."""
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import AppUser
from app.db.session import SessionLocal


def ensure_user(
    db, *, email: str, full_name: str, password: str, role: str, avatar_url: str | None = None
):
    existing = db.execute(select(AppUser).where(AppUser.email == email)).scalar_one_or_none()
    if existing:
        return existing
    user = AppUser(
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        role=role,
        avatar_url=avatar_url,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def run() -> None:
    db = SessionLocal()
    try:
        ensure_user(
            db,
            email="manager@demo.com",
            full_name="Demo Manager",
            password="demo",
            role="manager",
        )
        ensure_user(
            db,
            email="tech1@demo.com",
            full_name="Tech One",
            password="demo",
            role="technician",
        )
        ensure_user(
            db,
            email="user1@demo.com",
            full_name="Requester One",
            password="demo",
            role="user",
        )
        print("Seeded users.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
