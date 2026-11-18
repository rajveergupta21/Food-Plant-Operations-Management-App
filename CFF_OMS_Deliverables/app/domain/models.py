from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    QC_INSPECTOR = "QC_INSPECTOR"
    OPERATOR = "OPERATOR"

class BatchStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_QC = "PENDING_QC"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False, default=RoleEnum.OPERATOR.value)

class ProductionLine(Base):
    __tablename__ = "production_lines"
    id = Column(Integer, primary_key=True)
    line_code = Column(String(20), unique=True, nullable=False) # LINE_1, LINE_2, LINE_3
    description = Column(String(120))

class Batch(Base):
    __tablename__ = "batches"
    id = Column(Integer, primary_key=True, index=True)
    canonical_batch_key = Column(String(64), unique=True, nullable=False)
    legacy_batch_no = Column(String(32), index=True, nullable=False)
    line_id = Column(Integer, ForeignKey("production_lines.id"), nullable=False)
    shift = Column(String(10), nullable=False) # DAY or NIGHT
    production_start = Column(DateTime, nullable=False)
    production_end = Column(DateTime, nullable=False)
    total_input_kg = Column(Float, nullable=False)
    gross_output_kg = Column(Float, nullable=False)
    scrap_wastage_kg = Column(Float, nullable=False, default=0.0)
    status = Column(String(24), default=BatchStatus.DRAFT.value, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    quality_test = relationship("QualityTest", back_populates="batch", uselist=False)
    line = relationship("ProductionLine")

class QualityTest(Base):
    __tablename__ = "quality_tests"
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), unique=True, nullable=False)
    tested_at = Column(DateTime, nullable=False)
    moisture_pct = Column(Float, nullable=True)
    core_temp_c = Column(Float, nullable=False)
    rejected_output_kg = Column(Float, nullable=False, default=0.0)
    is_late_entry = Column(Boolean, default=False)
    result = Column(String(32), nullable=False)

    batch = relationship("Batch", back_populates="quality_test")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entity_name = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=False)
    action = Column(String(32), nullable=False)
    old_data = Column(JSON, nullable=True)
    new_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)