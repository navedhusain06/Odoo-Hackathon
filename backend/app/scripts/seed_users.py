"""Seed initial users for login tests."""
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import AppUser, RequestStage
from app.db.session import SessionLocal


def ensure_stages(db) -> None:
    existing = {
        s.name.lower(): s
        for s in db.execute(select(RequestStage)).scalars().all()
    }
    stages = [
        ("New", 10, False, False),
        ("In Progress", 20, False, False),
        ("Repaired", 30, True, False),
        ("Scrap", 40, True, True),
    ]
    created = False
    for name, seq, is_closed, is_scrap in stages:
        if name.lower() in existing:
            continue
        db.add(
            RequestStage(
                name=name,
                sequence=seq,
                is_closed=is_closed,
                is_scrap=is_scrap,
            )
        )
        created = True
    if created:
        db.commit()


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
        ensure_stages(db)
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
