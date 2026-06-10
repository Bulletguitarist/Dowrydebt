from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import uvicorn
from contextlib import asynccontextmanager
from backend.database import engine, Base, get_db
from sqlalchemy.orm import Session
from backend import models, schemas, crud, fraud
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    # Seed demo data
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        from backend.crud import seed_demo_data
        #seed_demo_data(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="DowryDebt Watch API",
    description="India's dowry financial abuse evidence platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "dowrywatch2024"

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ─── PUBLIC ROUTES ───────────────────────────────────────────

@app.post("/api/reports", response_model=schemas.ReportResponse)
async def submit_report(report: schemas.ReportCreate, request: Request, db: Session = Depends(get_db)):
    """Submit anonymous dowry abuse report"""
    ip_hash = fraud.hash_ip(request.client.host)
    
    # Run fraud detection
    fraud_result = fraud.analyze_report(report, ip_hash, db)
    
    if fraud_result["action"] == "block":
        raise HTTPException(status_code=429, detail=fraud_result["reason"])
    
    db_report = crud.create_report(db, report, ip_hash, fraud_result["fraud_score"])
    
    return schemas.ReportResponse(
        submission_token=db_report.submission_token,
        message="Report submitted securely. Your identity is fully protected.",
        fraud_score=fraud_result["fraud_score"],
        flagged=fraud_result["action"] == "flag"
    )

@app.get("/api/dashboard/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Public dashboard summary stats"""
    return crud.get_dashboard_summary(db)

@app.get("/api/dashboard/states")
async def get_state_breakdown(db: Session = Depends(get_db)):
    return crud.get_state_breakdown(db)

@app.get("/api/dashboard/districts")
async def get_district_data(db: Session = Depends(get_db)):
    return crud.get_district_data(db)

@app.get("/api/dashboard/pressure-types")
async def get_pressure_types(db: Session = Depends(get_db)):
    return crud.get_pressure_type_breakdown(db)

@app.get("/api/dashboard/debt-distribution")
async def get_debt_distribution(db: Session = Depends(get_db)):
    return crud.get_debt_distribution(db)

@app.get("/api/dashboard/monthly-trend")
async def get_monthly_trend(db: Session = Depends(get_db)):
    return crud.get_monthly_trend(db)

@app.get("/api/dashboard/map-data")
async def get_map_data(db: Session = Depends(get_db)):
    """District-level data for choropleth map"""
    return crud.get_map_data(db)

@app.get("/api/report/status/{token}")
async def check_report_status(token: str, db: Session = Depends(get_db)):
    report = crud.get_report_by_token(db, token)
    if not report:
        raise HTTPException(status_code=404, detail="Token not found")
    return {"token": token, "submitted_at": report.created_at, "state": report.state, "counted": True}

# ─── ADMIN ROUTES ─────────────────────────────────────────────

@app.get("/api/admin/reports")
async def admin_list_reports(
    page: int = 1, 
    per_page: int = 20,
    status_filter: str = None,
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    return crud.admin_get_reports(db, page, per_page, status_filter)

@app.get("/api/admin/reports/{report_id}")
async def admin_get_report(report_id: int, db: Session = Depends(get_db), admin: str = Depends(verify_admin)):
    report = crud.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@app.patch("/api/admin/reports/{report_id}/status")
async def admin_update_status(
    report_id: int, 
    update: schemas.ReportStatusUpdate,
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    return crud.update_report_status(db, report_id, update.status, update.admin_notes)

@app.get("/api/admin/fraud-queue")
async def admin_fraud_queue(db: Session = Depends(get_db), admin: str = Depends(verify_admin)):
    return crud.get_flagged_reports(db)

@app.get("/api/admin/stats")
async def admin_stats(db: Session = Depends(get_db), admin: str = Depends(verify_admin)):
    return crud.get_admin_stats(db)

# ─── SERVE FRONTEND ───────────────────────────────────────────

import os
root_path = os.path.join(os.path.dirname(__file__), "..")

@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse(os.path.join(root_path, "index.html"))

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend_catch(full_path: str):
    return FileResponse(os.path.join(root_path, "index.html"))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)