from sqlalchemy import (
    Column, String, Text, Boolean, Date, DateTime, Integer, Numeric,
    ForeignKey, CheckConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.db.base import Base

class AppUser(Base):
    __tablename__ = "app_user"
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Department(Base):
    __tablename__ = "department"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

class Location(Base):
    __tablename__ = "location"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    details = Column(Text, nullable=True)

class EquipmentCategory(Base):
    __tablename__ = "equipment_category"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

class MaintenanceTeam(Base):
    __tablename__ = "maintenance_team"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class MaintenanceTeamMember(Base):
    __tablename__ = "maintenance_team_member"
    team_id = Column(Integer, ForeignKey("maintenance_team.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String, nullable=True)

    team = relationship("MaintenanceTeam")
    user = relationship("AppUser")

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    serial_number = Column(String, nullable=False, unique=True)

    category_id = Column(Integer, ForeignKey("equipment_category.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("department.id"), nullable=True)
    owner_user_id = Column(Integer, ForeignKey("app_user.id"), nullable=True)

    purchase_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    warranty_vendor = Column(String, nullable=True)

    location_id = Column(Integer, ForeignKey("location.id"), nullable=True)

    maintenance_team_id = Column(Integer, ForeignKey("maintenance_team.id"), nullable=False)
    default_technician_id = Column(Integer, ForeignKey("app_user.id"), nullable=False)

    status = Column(String, nullable=False, default="active")  # active | unusable
    unusable_reason = Column(Text, nullable=True)
    unusable_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("(department_id IS NOT NULL) OR (owner_user_id IS NOT NULL)", name="equipment_owner_check"),
        Index("idx_equipment_team", "maintenance_team_id"),
    )

class RequestStage(Base):
    __tablename__ = "request_stage"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    sequence = Column(Integer, nullable=False, default=10)
    is_closed = Column(Boolean, nullable=False, default=False)
    is_scrap = Column(Boolean, nullable=False, default=False)

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_request"

    id = Column(Integer, primary_key=True)
    request_type = Column(String, nullable=False)  # corrective | preventive
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="RESTRICT"), nullable=False)

    equipment_category_id = Column(Integer, ForeignKey("equipment_category.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("maintenance_team.id"), nullable=False)

    requester_id = Column(Integer, ForeignKey("app_user.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("app_user.id"), nullable=True)

    stage_id = Column(Integer, ForeignKey("request_stage.id"), nullable=False)

    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)

    actual_duration_hours = Column(Numeric(10, 2), nullable=True)
    repaired_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("request_type IN ('corrective','preventive')", name="request_type_check"),
        Index("idx_req_equipment", "equipment_id"),
        Index("idx_req_team_stage", "team_id", "stage_id"),
        Index("idx_req_stage", "stage_id"),
        Index("idx_req_scheduled", "scheduled_start"),
    )

class MaintenanceRequestLog(Base):
    __tablename__ = "maintenance_request_log"
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("maintenance_request.id", ondelete="CASCADE"), nullable=False)
    changed_by = Column(Integer, ForeignKey("app_user.id"), nullable=True)
    field_name = Column(String, nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
