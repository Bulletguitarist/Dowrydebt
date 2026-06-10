from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime

class ReportCreate(BaseModel):
    state: str
    district: str
    year_of_marriage: Optional[int] = None
    relation_to_incident: Optional[str] = None
    pressure_types: List[str] = []
    estimated_burden: Optional[str] = None
    debt_amount: Optional[float] = 0
    ongoing_coercion: Optional[str] = None
    complaint_filed: Optional[str] = None
    additional_details: Optional[str] = None

    @validator("state")
    def state_not_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("State is required")
        return v.strip()

    @validator("district")
    def district_not_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("District is required")
        return v.strip()

    @validator("additional_details")
    def scrub_details(cls, v):
        if not v:
            return v
        # Basic PII scrubbing patterns
        import re
        v = re.sub(r'\b\d{10}\b', '[phone redacted]', v)
        v = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[email redacted]', v)
        v = re.sub(r'\b\d{12}\b', '[id redacted]', v)
        return v

class ReportResponse(BaseModel):
    submission_token: str
    message: str
    fraud_score: float
    flagged: bool

class ReportStatusUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None

class ReportOut(BaseModel):
    id: int
    submission_token: str
    state: str
    district: str
    year_of_marriage: Optional[int]
    relation_to_incident: Optional[str]
    pressure_types: List[str]
    estimated_burden: Optional[str]
    debt_amount: Optional[float]
    ongoing_coercion: Optional[str]
    complaint_filed: Optional[str]
    fraud_score: float
    status: str
    created_at: datetime
    admin_notes: Optional[str]

    class Config:
        from_attributes = True