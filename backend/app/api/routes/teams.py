from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import AppUser, MaintenanceTeam, MaintenanceTeamMember

router = APIRouter(prefix="/teams", tags=["teams"])


class TeamOut(BaseModel):
    id: int
    name: str
    members: list[dict]


class TeamCreate(BaseModel):
    name: str


class MemberPayload(BaseModel):
    user_id: int


@router.get("", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    teams = db.execute(select(MaintenanceTeam)).scalars().all()
    result: list[TeamOut] = []
    for t in teams:
        members = db.execute(
            select(MaintenanceTeamMember.user_id, AppUser.full_name)
            .join(AppUser, AppUser.id == MaintenanceTeamMember.user_id)
            .where(MaintenanceTeamMember.team_id == t.id)
        ).all()
        result.append(
            TeamOut(
                id=t.id,
                name=t.name,
                members=[{"id": uid, "name": name} for uid, name in members],
            )
        )
    return result


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Not allowed")
    existing = db.execute(select(MaintenanceTeam).where(MaintenanceTeam.name == payload.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Team exists")
    team = MaintenanceTeam(name=payload.name)
    db.add(team)
    db.commit()
    db.refresh(team)
    return TeamOut(id=team.id, name=team.name, members=[])


@router.post("/{team_id}/members", status_code=status.HTTP_204_NO_CONTENT)
def add_member(
    team_id: int,
    payload: MemberPayload,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Not allowed")
    team = db.get(MaintenanceTeam, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    exists = db.execute(
        select(MaintenanceTeamMember).where(
            MaintenanceTeamMember.team_id == team_id,
            MaintenanceTeamMember.user_id == payload.user_id,
        )
    ).scalar_one_or_none()
    if exists:
        return
    db.add(MaintenanceTeamMember(team_id=team_id, user_id=payload.user_id))
    db.commit()


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Not allowed")
    membership = db.execute(
        select(MaintenanceTeamMember).where(
            MaintenanceTeamMember.team_id == team_id,
            MaintenanceTeamMember.user_id == user_id,
        )
    ).scalar_one_or_none()
    if membership:
        db.delete(membership)
        db.commit()
