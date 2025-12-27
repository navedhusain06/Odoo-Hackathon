from decimal import Decimal
from datetime import datetime
from typing import Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import (
    AppUser,
    Equipment,
    MaintenanceRequest,
    MaintenanceTeam,
    MaintenanceTeamMember,
    RequestStage,
)

router = APIRouter(prefix="/requests", tags=["requests"])

STAGE_NAMES = {
    "new": "New",
    "in_progress": "In Progress",
    "repaired": "Repaired",
    "scrap": "Scrap",
}

ALLOWED_TRANSITIONS = {
    "new": {"in_progress", "scrap"},
    "in_progress": {"repaired", "scrap"},
    "repaired": set(),
    "scrap": set(),
}


class RequestOut(BaseModel):
    id: int
    subject: str
    request_type: str
    stage: str
    equipment_id: int
    equipment_name: str
    team_id: int
    team_name: str
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    scheduled_start: Optional[str] = None

    class Config:
        orm_mode = True


class RequestCreate(BaseModel):
    subject: str
    description: Optional[str] = None
    request_type: str = Field(pattern="^(corrective|preventive)$")
    equipment_id: int
    scheduled_start: Optional[str] = None  # ISO date string


class StageUpdate(BaseModel):
    stage: str = Field(pattern="^(new|in_progress|repaired|scrap)$")
    actual_duration_hours: Optional[Decimal] = None


class AssignPayload(BaseModel):
    assigned_to_id: int


def _stage_map(db: Session) -> dict[str, RequestStage]:
    rows: Sequence[RequestStage] = db.execute(select(RequestStage)).scalars().all()
    by_name = {r.name.lower(): r for r in rows}
    # ensure required stages exist
    missing = [name for name, label in STAGE_NAMES.items() if name not in by_name]
    if missing:
        for name in missing:
            stage = RequestStage(
                name=STAGE_NAMES[name],
                sequence=10 if name == "new" else 20 if name == "in_progress" else 30,
                is_scrap=True if name == "scrap" else False,
                is_closed=True if name in {"repaired", "scrap"} else False,
            )
            db.add(stage)
            db.flush()
            by_name[name] = stage
        db.commit()
    return by_name


def _is_team_member(db: Session, team_id: int, user_id: int) -> bool:
    return (
        db.execute(
            select(MaintenanceTeamMember).where(
                MaintenanceTeamMember.team_id == team_id,
                MaintenanceTeamMember.user_id == user_id,
            )
        ).scalar_one_or_none()
        is not None
    )


@router.get("", response_model=list[RequestOut])
def list_requests(
    db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)
):
    # Visibility rules:
    # manager -> all
    # technician -> assigned_to = self OR (stage=new and team member)
    # user -> created by self (requester)
    stmt = (
        select(
            MaintenanceRequest.id,
            MaintenanceRequest.subject,
            MaintenanceRequest.request_type,
            MaintenanceRequest.stage_id,
            MaintenanceRequest.equipment_id,
            MaintenanceRequest.team_id,
            MaintenanceRequest.assigned_to_id,
            MaintenanceRequest.scheduled_start,
            Equipment.name.label("equipment_name"),
        )
        .join(Equipment, Equipment.id == MaintenanceRequest.equipment_id)
    )

    if current_user.role == "manager":
        pass
    elif current_user.role == "technician":
        # Allow assigned or new for their teams
        stmt = stmt.where(
            or_(
                MaintenanceRequest.assigned_to_id == current_user.id,
                and_(
                    MaintenanceRequest.stage_id.in_(
                        select(RequestStage.id).where(RequestStage.name == STAGE_NAMES["new"])
                    ),
                    MaintenanceRequest.team_id.in_(
                        select(MaintenanceTeamMember.team_id).where(
                            MaintenanceTeamMember.user_id == current_user.id
                        )
                    ),
                ),
            )
        )
    else:
        stmt = stmt.where(MaintenanceRequest.requester_id == current_user.id)

    # include team name and assigned name via separate fetch
    rows = db.execute(stmt).all()
    # map stage_id -> name
    stages = db.execute(select(RequestStage.id, RequestStage.name)).all()
    stage_lookup = {sid: sname for sid, sname in stages}

    # Get team names
    team_names = dict(db.execute(select(MaintenanceTeam.id, MaintenanceTeam.name)).all())

    # assigned names
    assigned_ids = [r.assigned_to_id for r in rows if r.assigned_to_id]
    assigned_map = {}
    if assigned_ids:
        assigned_map = dict(
            db.execute(
                select(AppUser.id, AppUser.full_name).where(AppUser.id.in_(assigned_ids))
            ).all()
        )

    result: list[RequestOut] = []
    for r in rows:
        result.append(
            RequestOut(
                id=r.id,
                subject=r.subject,
                request_type=r.request_type,
                stage=_normalize_stage_name(stage_lookup.get(r.stage_id, "")),
                equipment_id=r.equipment_id,
                equipment_name=r.equipment_name,
                team_id=r.team_id,
                team_name=team_names.get(r.team_id, ""),
                assigned_to_id=r.assigned_to_id,
                assigned_to_name=assigned_map.get(r.assigned_to_id),
                scheduled_start=r.scheduled_start.isoformat() if r.scheduled_start else None,
            )
        )
    return result


def _normalize_stage_name(name: str) -> str:
    lowered = name.lower()
    if lowered in ("new", "in progress", "in_progress", "in-progress"):
        return "in_progress" if "progress" in lowered else "new"
    if lowered.startswith("repaired"):
        return "repaired"
    if lowered.startswith("scrap"):
        return "scrap"
    return lowered


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: RequestCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    stages = _stage_map(db)
    equipment = db.execute(
        select(Equipment).where(Equipment.id == payload.equipment_id)
    ).scalar_one_or_none()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    assigned_to_id: Optional[int] = None
    if equipment.default_technician_id and _is_team_member(
        db, equipment.maintenance_team_id, equipment.default_technician_id
    ):
        assigned_to_id = equipment.default_technician_id

    scheduled_dt = None
    if payload.scheduled_start:
        try:
            scheduled_dt = datetime.fromisoformat(payload.scheduled_start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid scheduled_start")

    req = MaintenanceRequest(
        request_type=payload.request_type,
        subject=payload.subject,
        description=payload.description,
        equipment_id=equipment.id,
        equipment_category_id=equipment.category_id,
        team_id=equipment.maintenance_team_id,
        requester_id=current_user.id,
        assigned_to_id=assigned_to_id,
        stage_id=stages["new"].id,
        scheduled_start=scheduled_dt,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    team_name = db.execute(
        select(MaintenanceTeamMember.team.name)
        .join(MaintenanceTeamMember.team)
        .where(MaintenanceTeamMember.team_id == req.team_id)
    ).scalar_one_or_none()
    assigned_name = None
    if req.assigned_to_id:
        assigned_name = db.execute(
            select(AppUser.full_name).where(AppUser.id == req.assigned_to_id)
        ).scalar_one_or_none()

    return RequestOut(
        id=req.id,
        subject=req.subject,
        request_type=req.request_type,
        stage="new",
        equipment_id=req.equipment_id,
        equipment_name=equipment.name,
        team_id=req.team_id,
        team_name=team_name or "",
        assigned_to_id=req.assigned_to_id,
        assigned_to_name=assigned_name,
        scheduled_start=req.scheduled_start.isoformat() if req.scheduled_start else None,
    )


@router.patch("/{request_id}/assign", response_model=RequestOut)
def assign_request(
    request_id: int,
    payload: AssignPayload,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    stages = _stage_map(db)
    req = db.execute(
        select(MaintenanceRequest).where(MaintenanceRequest.id == request_id)
    ).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    # RBAC
    if current_user.role == "user":
        raise HTTPException(status_code=403, detail="Not allowed")
    if current_user.role == "technician" and not _is_team_member(
        db, req.team_id, current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not allowed")

    # assignee must be team member
    if not _is_team_member(db, req.team_id, payload.assigned_to_id):
        raise HTTPException(status_code=400, detail="Assignee not in team")

    req.assigned_to_id = payload.assigned_to_id
    # move to in_progress if currently new
    current_stage = _normalize_stage_name(
        db.execute(select(RequestStage.name).where(RequestStage.id == req.stage_id)).scalar_one()
    )
    if current_stage == "new":
        req.stage_id = stages["in_progress"].id

    db.commit()
    db.refresh(req)

    equipment = db.get(Equipment, req.equipment_id)
    assigned_name = db.execute(
        select(AppUser.full_name).where(AppUser.id == req.assigned_to_id)
    ).scalar_one_or_none()
    team_name = db.execute(
        select(MaintenanceTeam.name).where(MaintenanceTeam.id == req.team_id)
    ).scalar_one_or_none()

    return RequestOut(
        id=req.id,
        subject=req.subject,
        request_type=req.request_type,
        stage=_normalize_stage_name(
            db.execute(select(RequestStage.name).where(RequestStage.id == req.stage_id)).scalar_one()
        ),
        equipment_id=req.equipment_id,
        equipment_name=equipment.name if equipment else "",
        team_id=req.team_id,
        team_name=team_name or "",
        assigned_to_id=req.assigned_to_id,
        assigned_to_name=assigned_name,
        scheduled_start=req.scheduled_start.isoformat() if req.scheduled_start else None,
    )


@router.patch("/{request_id}/stage", response_model=RequestOut)
def update_stage(
    request_id: int,
    payload: StageUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    stages = _stage_map(db)
    req = db.execute(
        select(MaintenanceRequest).where(MaintenanceRequest.id == request_id)
    ).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    # resolve current/target
    current_stage = _normalize_stage_name(
        db.execute(select(RequestStage.name).where(RequestStage.id == req.stage_id)).scalar_one()
    )
    target_stage = payload.stage
    if target_stage not in ALLOWED_TRANSITIONS.get(current_stage, set()) and not (
        target_stage == "scrap"
    ):
        raise HTTPException(status_code=400, detail="Invalid transition")

    # RBAC: manager all; tech must be member of team; user cannot change stage
    if current_user.role == "technician" and not _is_team_member(
        db, req.team_id, current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not allowed")
    if current_user.role == "user":
        raise HTTPException(status_code=403, detail="Not allowed")

    # repaired requires duration
    if target_stage == "repaired" and payload.actual_duration_hours is None:
        raise HTTPException(status_code=400, detail="Duration required for repaired")

    # in_progress requires assignment to team member
    if target_stage == "in_progress":
        if not req.assigned_to_id:
            req.assigned_to_id = current_user.id
        if not _is_team_member(db, req.team_id, req.assigned_to_id):
            raise HTTPException(status_code=400, detail="Assignee not in team")

    # scrap side-effect
    if target_stage == "scrap":
        equipment = db.get(Equipment, req.equipment_id)
        if equipment:
            equipment.status = "unusable"
            equipment.unusable_reason = f"Request {req.id} moved to scrap"

    req.stage_id = stages[target_stage].id
    if target_stage == "repaired":
        req.actual_duration_hours = payload.actual_duration_hours
    db.commit()
    db.refresh(req)

    equipment = db.get(Equipment, req.equipment_id)
    assigned_name = None
    if req.assigned_to_id:
        assigned_name = db.execute(
            select(AppUser.full_name).where(AppUser.id == req.assigned_to_id)
        ).scalar_one_or_none()

    team_name = db.execute(
        select(MaintenanceTeamMember.team.name)
        .join(MaintenanceTeamMember.team)
        .where(MaintenanceTeamMember.team_id == req.team_id)
    ).scalar_one_or_none()

    return RequestOut(
        id=req.id,
        subject=req.subject,
        request_type=req.request_type,
        stage=target_stage,
        equipment_id=req.equipment_id,
        equipment_name=equipment.name if equipment else "",
        team_id=req.team_id,
        team_name=team_name or "",
        assigned_to_id=req.assigned_to_id,
        assigned_to_name=assigned_name,
        scheduled_start=req.scheduled_start.isoformat() if req.scheduled_start else None,
    )


@router.get("/calendar", response_model=list[RequestOut])
def calendar(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    try:
        start_dt = datetime.fromisoformat(start) if start else None
        end_dt = datetime.fromisoformat(end) if end else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date range")

    stages = _stage_map(db)
    stmt = (
        select(
            MaintenanceRequest,
            Equipment.name.label("equipment_name"),
            MaintenanceTeam.name.label("team_name"),
            RequestStage.name.label("stage_name"),
            AppUser.full_name.label("assigned_name"),
        )
        .join(Equipment, Equipment.id == MaintenanceRequest.equipment_id)
        .join(MaintenanceTeam, MaintenanceTeam.id == MaintenanceRequest.team_id)
        .join(RequestStage, RequestStage.id == MaintenanceRequest.stage_id)
        .outerjoin(AppUser, AppUser.id == MaintenanceRequest.assigned_to_id)
        .where(MaintenanceRequest.request_type == "preventive")
    )

    if start_dt:
        stmt = stmt.where(MaintenanceRequest.scheduled_start >= start_dt)
    if end_dt:
        stmt = stmt.where(MaintenanceRequest.scheduled_start <= end_dt)

    # visibility same as list
    if current_user.role == "manager":
        pass
    elif current_user.role == "technician":
        stmt = stmt.where(
            or_(
                MaintenanceRequest.assigned_to_id == current_user.id,
                and_(
                    MaintenanceRequest.stage_id == stages["new"].id,
                    MaintenanceRequest.team_id.in_(
                        select(MaintenanceTeamMember.team_id).where(
                            MaintenanceTeamMember.user_id == current_user.id
                        )
                    ),
                ),
            )
        )
    else:
        stmt = stmt.where(MaintenanceRequest.requester_id == current_user.id)

    rows = db.execute(stmt).all()
    result: list[RequestOut] = []
    for req, equip_name, team_name, stage_name, assigned_name in rows:
        result.append(
            RequestOut(
                id=req.id,
                subject=req.subject,
                request_type=req.request_type,
                stage=_normalize_stage_name(stage_name),
                equipment_id=req.equipment_id,
                equipment_name=equip_name,
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
