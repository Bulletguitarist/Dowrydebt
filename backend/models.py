from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, Enum as SAEnum
from sqlalchemy.sql import func
from backend.database import Base
import enum

class ReportStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    flagged = "flagged"
    rejected = "rejected"

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    submission_token = Column(String(20), unique=True, index=True)

    # Location (district-level only, never exact)
    state = Column(String(60), nullable=False, index=True)
    district = Column(String(80), nullable=False, index=True)

    # Marriage details
    year_of_marriage = Column(Integer)
    relation_to_incident = Column(String(80))

    # Financial data
    pressure_types = Column(JSON, default=[])  # list of strings
    estimated_burden = Column(String(40))
    debt_amount = Column(Float, default=0)       # in INR
    ongoing_coercion = Column(String(80))
    complaint_filed = Column(String(80))

    # Free text (scrubbed by fraud detector)
    additional_details = Column(Text)

    # Fraud detection
    ip_hash = Column(String(64))
    fraud_score = Column(Float, default=0.0)   # 0.0 = clean, 1.0 = definite fraud
    status = Column(SAEnum(ReportStatus), default=ReportStatus.pending, index=True)
    admin_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Derived fields for demo seeding
    is_demo = Column(Boolean, default=False)