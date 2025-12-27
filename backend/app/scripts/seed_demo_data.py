"""Seed demo data for quick frontend testing (teams, equipment, requests)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import (
    AppUser,
    Department,
    Equipment,
    EquipmentCategory,
    MaintenanceRequest,
    MaintenanceTeam,
    MaintenanceTeamMember,
    RequestStage,
)
from app.db.session import SessionLocal


def ensure_user(db, *, email: str, full_name: str, password: str, role: str) -> AppUser:
    user = (
        db.execute(select(AppUser).where(AppUser.email == email)).scalar_one_or_none()
    )
    if user:
        return user
    user = AppUser(
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_stage_map(db) -> dict[str, RequestStage]:
    stages = {s.name.lower(): s for s in db.execute(select(RequestStage)).scalars().all()}
    required = [
        ("New", 10, False, False),
        ("In Progress", 20, False, False),
        ("Repaired", 30, True, False),
        ("Scrap", 40, True, True),
    ]
    for name, seq, closed, scrap in required:
        if name.lower() in stages:
            continue
        st = RequestStage(name=name, sequence=seq, is_closed=closed, is_scrap=scrap)
        db.add(st)
        db.flush()
        stages[name.lower()] = st
    db.commit()
    return stages


def ensure_simple(db, model, name_field: str, name: str):
    existing = (
        db.execute(select(model).where(getattr(model, name_field) == name)).scalar_one_or_none()
    )
    if existing:
        return existing
    obj = model(**{name_field: name})
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def ensure_team_member(db, team_id: int, user_id: int):
    exists = db.execute(
        select(MaintenanceTeamMember).where(
            MaintenanceTeamMember.team_id == team_id,
            MaintenanceTeamMember.user_id == user_id,
        )
    ).scalar_one_or_none()
    if exists:
        return
    db.add(MaintenanceTeamMember(team_id=team_id, user_id=user_id))
    db.commit()


def ensure_request(
    db,
    *,
    subject: str,
    req_type: str,
    stage_name: str,
    equipment: Equipment,
    requester_id: int,
    assigned_to_id: int | None,
    scheduled_start: datetime | None = None,
):
    existing = (
        db.execute(
            select(MaintenanceRequest).where(
                MaintenanceRequest.subject == subject,
                MaintenanceRequest.equipment_id == equipment.id,
            )
        ).scalar_one_or_none()
    )
    stages = ensure_stage_map(db)
    stage = stages[stage_name.lower()]

    if existing:
        return existing
    req = MaintenanceRequest(
        request_type=req_type,
        subject=subject,
        description=None,
        equipment_id=equipment.id,
        equipment_category_id=equipment.category_id,
        team_id=equipment.maintenance_team_id,
        requester_id=requester_id,
        assigned_to_id=assigned_to_id,
        stage_id=stage.id,
        scheduled_start=scheduled_start,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def run() -> None:
    db = SessionLocal()
    try:
        # Users
        manager = ensure_user(
            db, email="manager@demo.com", full_name="Demo Manager", password="demo", role="manager"
        )
        tech1 = ensure_user(
            db, email="tech1@demo.com", full_name="Tech One", password="demo", role="technician"
        )
        tech2 = ensure_user(
            db, email="tech2@demo.com", full_name="Tech Two", password="demo", role="technician"
        )
        requester = ensure_user(
            db, email="user1@demo.com", full_name="Requester One", password="demo", role="user"
        )

        # Lookup tables
        dept_prod = ensure_simple(db, Department, "name", "Production")
        dept_it = ensure_simple(db, Department, "name", "IT")
        cat_machine = ensure_simple(db, EquipmentCategory, "name", "Machine")
        cat_laptop = ensure_simple(db, EquipmentCategory, "name", "Laptop")

        # Teams
        mech = ensure_simple(db, MaintenanceTeam, "name", "Mechanics")
        it_team = ensure_simple(db, MaintenanceTeam, "name", "IT Support")
        ensure_team_member(db, mech.id, tech1.id)
        ensure_team_member(db, mech.id, tech2.id)
        ensure_team_member(db, it_team.id, tech2.id)

        # Equipment
        cnc = db.execute(
            select(Equipment).where(Equipment.serial_number == "CNC-001")
        ).scalar_one_or_none()
        if not cnc:
            cnc = Equipment(
                name="CNC Machine 01",
                serial_number="CNC-001",
                category_id=cat_machine.id,
                department_id=dept_prod.id,
                owner_user_id=manager.id,
                maintenance_team_id=mech.id,
                default_technician_id=tech1.id,
                status="active",
            )
            db.add(cnc)
            db.commit()
            db.refresh(cnc)

        laptop = db.execute(
            select(Equipment).where(Equipment.serial_number == "LT-44")
        ).scalar_one_or_none()
        if not laptop:
            laptop = Equipment(
                name="Laptop-IT-44",
                serial_number="LT-44",
                category_id=cat_laptop.id,
                department_id=dept_it.id,
                owner_user_id=requester.id,
                maintenance_team_id=it_team.id,
                default_technician_id=tech2.id,
                status="active",
            )
            db.add(laptop)
            db.commit()
            db.refresh(laptop)

        # Requests
        ensure_request(
            db,
            subject="Leaking oil",
            req_type="corrective",
            stage_name="New",
            equipment=cnc,
            requester_id=requester.id,
            assigned_to_id=None,
        )
        ensure_request(
            db,
            subject="Laptop annual check",
            req_type="preventive",
            stage_name="In Progress",
            equipment=laptop,
            requester_id=manager.id,
            assigned_to_id=tech2.id,
            scheduled_start=datetime.now(timezone.utc) - timedelta(days=2),
        )
        ensure_request(
            db,
            subject="Hydraulic pressure low",
            req_type="corrective",
            stage_name="Repaired",
            equipment=cnc,
            requester_id=requester.id,
            assigned_to_id=tech1.id,
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
