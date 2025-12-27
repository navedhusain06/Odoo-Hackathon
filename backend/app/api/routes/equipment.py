from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from app.api.deps import get_current_user, get_db
from app.db.models import (
    AppUser,
    Department,
    Equipment,
    EquipmentCategory,
    MaintenanceRequest,
    MaintenanceTeam,
    RequestStage,
)
from app.api.routes.requests import RequestOut, _normalize_stage_name

router = APIRouter(prefix="/equipment", tags=["equipment"])


class EquipmentOut(BaseModel):
    id: int
    name: str
    serial_number: str
    department: Optional[str] = None
    owner: Optional[str] = None
    category: Optional[str] = None
    team_id: int
    team: str
    default_technician_id: Optional[int] = None
    default_technician: Optional[str] = None
    maintenance_open_count: int

    class Config:
        orm_mode = True


@router.get("", response_model=list[EquipmentOut])
def list_equipment(
    department_id: Optional[int] = Query(None),
    owner_user_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Count open requests (not closed)
    open_stage_ids = select(RequestStage.id).where(RequestStage.is_closed.is_(False))
    open_counts = (
        select(
            MaintenanceRequest.equipment_id.label("eq_id"),
            func.count().label("open_count"),
        )
        .where(MaintenanceRequest.stage_id.in_(open_stage_ids))
        .group_by(MaintenanceRequest.equipment_id)
        .subquery()
    )

    owner_alias = aliased(AppUser)
    tech_alias = aliased(AppUser)

    stmt = (
        select(
            Equipment,
            Department.name.label("dept_name"),
            EquipmentCategory.name.label("cat_name"),
            MaintenanceTeam.name.label("team_name"),
            owner_alias.full_name.label("owner_name"),
            func.coalesce(open_counts.c.open_count, 0).label("open_count"),
            tech_alias.full_name.label("default_tech_name"),
        )
        .join(EquipmentCategory, EquipmentCategory.id == Equipment.category_id)
        .join(MaintenanceTeam, MaintenanceTeam.id == Equipment.maintenance_team_id)
        .outerjoin(Department, Department.id == Equipment.department_id)
        .outerjoin(owner_alias, owner_alias.id == Equipment.owner_user_id)
        .outerjoin(tech_alias, tech_alias.id == Equipment.default_technician_id)
        .outerjoin(open_counts, open_counts.c.eq_id == Equipment.id)
    )

    if department_id:
        stmt = stmt.where(Equipment.department_id == department_id)
    if owner_user_id:
        stmt = stmt.where(Equipment.owner_user_id == owner_user_id)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Equipment.name).like(like),
                func.lower(Equipment.serial_number).like(like),
            )
        )

    rows = db.execute(stmt).all()
    result: list[EquipmentOut] = []
    for eq, dept_name, cat_name, team_name, owner_name, open_count, default_tech_name in rows:
        result.append(
            EquipmentOut(
                id=eq.id,
                name=eq.name,
                serial_number=eq.serial_number,
                department=dept_name,
                owner=owner_name,
                category=cat_name,
                team_id=eq.maintenance_team_id,
                team=team_name,
                default_technician_id=eq.default_technician_id,
                default_technician=default_tech_name,
                maintenance_open_count=open_count or 0,
            )
        )
    return result


@router.get("/{equipment_id}")
def equipment_detail(
    equipment_id: int, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)
):
    eq = db.get(Equipment, equipment_id)
    if not eq:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": eq.id,
        "name": eq.name,
        "serial_number": eq.serial_number,
        "department_id": eq.department_id,
        "owner_user_id": eq.owner_user_id,
        "category_id": eq.category_id,
        "maintenance_team_id": eq.maintenance_team_id,
        "default_technician_id": eq.default_technician_id,
        "status": eq.status,
    }


@router.get("/{equipment_id}/requests/count")
def equipment_request_count(
    equipment_id: int, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)
):
    open_stage_ids = select(RequestStage.id).where(RequestStage.is_closed.is_(False))
    count = db.execute(
        select(func.count()).where(
            MaintenanceRequest.equipment_id == equipment_id,
            MaintenanceRequest.stage_id.in_(open_stage_ids),
        )
    ).scalar_one()
    return {"equipment_id": equipment_id, "open_requests": count}


@router.get("/{equipment_id}/requests", response_model=list[RequestOut])
def equipment_requests(
    equipment_id: int, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)
):
    # reuse visibility like list_requests for simplicity: manager -> all; tech -> assigned or new in their teams; user -> requester
    # Here we just return all for manager/tech; for user filter by requester
    stmt = (
        select(
            MaintenanceRequest,
            RequestStage.name.label("stage_name"),
            Equipment.name.label("equipment_name"),
            MaintenanceTeam.name.label("team_name"),
            AppUser.full_name.label("assigned_name"),
        )
        .join(Equipment, Equipment.id == MaintenanceRequest.equipment_id)
        .join(RequestStage, RequestStage.id == MaintenanceRequest.stage_id)
        .join(MaintenanceTeam, MaintenanceTeam.id == MaintenanceRequest.team_id)
        .outerjoin(AppUser, AppUser.id == MaintenanceRequest.assigned_to_id)
        .where(MaintenanceRequest.equipment_id == equipment_id)
    )

    if current_user.role == "user":
        stmt = stmt.where(MaintenanceRequest.requester_id == current_user.id)

    rows = db.execute(stmt).all()
    result: list[RequestOut] = []
    for req, stage_name, equipment_name, team_name, assigned_name in rows:
        result.append(
            RequestOut(
                id=req.id,
                subject=req.subject,
                request_type=req.request_type,
                stage=_normalize_stage_name(stage_name),
                equipment_id=req.equipment_id,
                equipment_name=equipment_name,
                team_id=req.team_id,
                team_name=team_name,
                assigned_to_id=req.assigned_to_id,
                assigned_to_name=assigned_name,
                scheduled_start=req.scheduled_start.isoformat()
                if req.scheduled_start
                else None,
            )
        )
    return result
