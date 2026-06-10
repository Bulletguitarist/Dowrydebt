from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc, cast, Date
from backend import models, schemas
from backend.models import Report, ReportStatus
import random, string
from datetime import datetime, timedelta
import json

# ── Token Generation ──────────────────────────────────────────

def generate_token():
    parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(3)]
    return f"DDW-{''.join(parts[:1])}-{''.join(parts[1:2])}-{''.join(parts[2:])}"

# ── Create Report ─────────────────────────────────────────────

def create_report(db: Session, report: schemas.ReportCreate, ip_hash: str, fraud_score: float):
    status = ReportStatus.flagged if fraud_score >= 0.45 else ReportStatus.pending
    db_report = Report(
        submission_token=generate_token(),
        state=report.state,
        district=report.district,
        year_of_marriage=report.year_of_marriage,
        relation_to_incident=report.relation_to_incident,
        pressure_types=report.pressure_types,
        estimated_burden=report.estimated_burden,
        debt_amount=report.debt_amount or 0,
        ongoing_coercion=report.ongoing_coercion,
        complaint_filed=report.complaint_filed,
        additional_details=report.additional_details,
        ip_hash=ip_hash,
        fraud_score=fraud_score,
        status=status,
        is_demo=False
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_report_by_token(db: Session, token: str):
    return db.query(Report).filter(Report.submission_token == token).first()

def get_report_by_id(db: Session, report_id: int):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r:
        return None
    return {
        "id": r.id, "submission_token": r.submission_token,
        "state": r.state, "district": r.district,
        "year_of_marriage": r.year_of_marriage,
        "relation_to_incident": r.relation_to_incident,
        "pressure_types": r.pressure_types or [],
        "estimated_burden": r.estimated_burden,
        "debt_amount": r.debt_amount,
        "ongoing_coercion": r.ongoing_coercion,
        "complaint_filed": r.complaint_filed,
        "additional_details": r.additional_details,
        "fraud_score": r.fraud_score,
        "status": r.status.value if r.status else "pending",
        "admin_notes": r.admin_notes,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }

# ── Dashboard Queries ─────────────────────────────────────────

def get_dashboard_summary(db: Session):
    total = db.query(func.count(Report.id)).filter(Report.status != ReportStatus.rejected).scalar() or 0
    districts = db.query(func.count(func.distinct(Report.district))).filter(Report.status != ReportStatus.rejected).scalar() or 0
    avg_debt = db.query(func.avg(Report.debt_amount)).filter(
        Report.debt_amount > 0, Report.status != ReportStatus.rejected
    ).scalar() or 0
    ongoing = db.query(func.count(Report.id)).filter(
        Report.ongoing_coercion.ilike('%yes%'),
        Report.status != ReportStatus.rejected
    ).scalar() or 0
    ongoing_pct = round((ongoing / total * 100) if total > 0 else 0, 1)

    return {
        "total_reports": total,
        "districts_covered": districts,
        "median_debt": round(avg_debt),
        "ongoing_coercion_pct": ongoing_pct,
    }

def get_state_breakdown(db: Session):
    rows = db.query(
        Report.state,
        func.count(Report.id).label("count"),
        func.avg(Report.debt_amount).label("avg_debt")
    ).filter(
        Report.status != ReportStatus.rejected
    ).group_by(Report.state).order_by(desc("count")).limit(15).all()

    return [{"state": r.state, "count": r.count, "avg_debt": round(r.avg_debt or 0)} for r in rows]

def get_district_data(db: Session):
    rows = db.query(
        Report.state,
        Report.district,
        func.count(Report.id).label("count"),
        func.avg(Report.debt_amount).label("avg_debt")
    ).filter(
        Report.status != ReportStatus.rejected
    ).group_by(Report.state, Report.district).order_by(desc("count")).limit(50).all()

    return [{"state": r.state, "district": r.district, "count": r.count, "avg_debt": round(r.avg_debt or 0)} for r in rows]

def get_pressure_type_breakdown(db: Session):
    reports = db.query(Report.pressure_types).filter(
        Report.status != ReportStatus.rejected,
        Report.pressure_types != None
    ).all()

    counts = {}
    for (pt,) in reports:
        if pt:
            for item in pt:
                counts[item] = counts.get(item, 0) + 1

    return sorted([{"type": k, "count": v} for k, v in counts.items()], key=lambda x: -x["count"])

def get_debt_distribution(db: Session):
    buckets = [
        ("Under ₹1L", 0, 100000),
        ("₹1–5L", 100000, 500000),
        ("₹5–10L", 500000, 1000000),
        ("₹10–25L", 1000000, 2500000),
        ("₹25–50L", 2500000, 5000000),
        ("Over ₹50L", 5000000, 999999999),
    ]
    result = []
    for label, lo, hi in buckets:
        count = db.query(func.count(Report.id)).filter(
            Report.debt_amount >= lo,
            Report.debt_amount < hi,
            Report.status != ReportStatus.rejected
        ).scalar() or 0
        result.append({"bucket": label, "count": count})
    return result

def get_monthly_trend(db: Session):
    rows = db.query(
        func.strftime('%Y-%m', Report.created_at).label("month"),
        func.count(Report.id).label("count")
    ).filter(
        Report.status != ReportStatus.rejected,
        Report.created_at >= datetime.utcnow() - timedelta(days=365)
    ).group_by("month").order_by("month").all()

    return [{"month": r.month, "count": r.count} for r in rows]

def get_map_data(db: Session):
    rows = db.query(
        Report.state,
        Report.district,
        func.count(Report.id).label("count"),
        func.avg(Report.debt_amount).label("avg_debt"),
        func.sum(func.cast(Report.ongoing_coercion.ilike('%yes%'), models.Report.id.__class__)).label("coercion_count")
    ).filter(
        Report.status != ReportStatus.rejected
    ).group_by(Report.state, Report.district).all()

    return [
        {
            "state": r.state,
            "district": r.district,
            "count": r.count,
            "avg_debt": round(r.avg_debt or 0),
            "risk_score": min(100, int((r.count / 10) * 40 + ((r.avg_debt or 0) / 1000000) * 60))
        }
        for r in rows
    ]

# ── Admin Queries ─────────────────────────────────────────────

def admin_get_reports(db: Session, page: int, per_page: int, status_filter: str = None):
    q = db.query(Report)
    if status_filter:
        q = q.filter(Report.status == status_filter)
    total = q.count()
    reports = q.order_by(desc(Report.created_at)).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "reports": [_serialize_report(r) for r in reports]
    }

def get_flagged_reports(db: Session):
    reports = db.query(Report).filter(
        Report.status == ReportStatus.flagged
    ).order_by(desc(Report.fraud_score)).limit(50).all()
    return [_serialize_report(r) for r in reports]

def update_report_status(db: Session, report_id: int, status: str, admin_notes: str = None):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return None
    report.status = ReportStatus(status)
    if admin_notes:
        report.admin_notes = admin_notes
    db.commit()
    return _serialize_report(report)

def get_admin_stats(db: Session):
    total = db.query(func.count(Report.id)).scalar() or 0
    pending = db.query(func.count(Report.id)).filter(Report.status == ReportStatus.pending).scalar() or 0
    flagged = db.query(func.count(Report.id)).filter(Report.status == ReportStatus.flagged).scalar() or 0
    verified = db.query(func.count(Report.id)).filter(Report.status == ReportStatus.verified).scalar() or 0
    rejected = db.query(func.count(Report.id)).filter(Report.status == ReportStatus.rejected).scalar() or 0
    avg_fraud = db.query(func.avg(Report.fraud_score)).scalar() or 0
    today = db.query(func.count(Report.id)).filter(
        func.date(Report.created_at) == func.current_date()
    ).scalar() or 0

    return {
        "total": total, "pending": pending, "flagged": flagged,
        "verified": verified, "rejected": rejected,
        "avg_fraud_score": round(avg_fraud, 3), "today": today
    }

def _serialize_report(r: Report) -> dict:
    return {
        "id": r.id, "submission_token": r.submission_token,
        "state": r.state, "district": r.district,
        "year_of_marriage": r.year_of_marriage,
        "relation_to_incident": r.relation_to_incident,
        "pressure_types": r.pressure_types or [],
        "estimated_burden": r.estimated_burden,
        "debt_amount": r.debt_amount,
        "ongoing_coercion": r.ongoing_coercion,
        "complaint_filed": r.complaint_filed,
        "fraud_score": r.fraud_score,
        "status": r.status.value if r.status else "pending",
        "admin_notes": r.admin_notes,
        "is_demo": r.is_demo,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }

# ── Demo Data Seeder ──────────────────────────────────────────

STATES_DISTRICTS = {
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi", "Meerut", "Bareilly", "Allahabad", "Gorakhpur", "Aligarh", "Moradabad"],
    "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga", "Purnia", "Nalanda", "Begusarai", "Siwan", "Chapra"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer", "Bikaner", "Alwar", "Bharatpur", "Sikar", "Pali"],
    "Haryana": ["Gurgaon", "Faridabad", "Hisar", "Rohtak", "Panipat", "Ambala", "Karnal", "Sonipat", "Bhiwani", "Sirsa"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain", "Sagar", "Rewa", "Satna", "Chhindwara", "Morena"],
    "Maharashtra": ["Pune", "Nagpur", "Nashik", "Aurangabad", "Thane", "Solapur", "Kolhapur", "Nanded", "Sangli", "Satara"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar", "Gandhinagar", "Anand", "Mehsana", "Patan"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Asansol", "Malda", "Murshidabad", "Burdwan", "Nadia", "Siliguri", "Haldia"],
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool", "Kakinada", "Rajahmundry", "Tirupati", "Kadapa", "Anantapur"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubli", "Mangaluru", "Belagavi", "Ballari", "Davanagere", "Shivamogga", "Tumkur", "Vijayapura"],
}

PRESSURE_TYPES = [
    "Cash demands before marriage",
    "Jewellery / gold demands",
    "Vehicle / property demands",
    "Post-marriage cash demands",
    "Loans taken by bride's family",
    "Land / asset sold",
    "Threats if demands not met",
    "Ongoing post-marriage pressure"
]

BURDEN_OPTIONS = ["Under ₹1 lakh", "₹1–5 lakh", "₹5–10 lakh", "₹10–25 lakh", "₹25–50 lakh", "Over ₹50 lakh"]
DEBT_RANGES = [(0, 100000), (100000, 500000), (500000, 1000000), (1000000, 2500000), (2500000, 5000000), (5000000, 10000000)]

def seed_demo_data(db: Session):
    existing = db.query(func.count(Report.id)).scalar()
    if existing and existing > 0:
        return  # Already seeded

    print("Seeding demo data...")
    random.seed(42)

    # Weight by state (UP, Bihar, Rajasthan get more reports)
    state_weights = {
        "Uttar Pradesh": 0.28, "Bihar": 0.18, "Rajasthan": 0.14,
        "Haryana": 0.10, "Madhya Pradesh": 0.09, "Maharashtra": 0.07,
        "Gujarat": 0.05, "West Bengal": 0.05, "Andhra Pradesh": 0.02, "Karnataka": 0.02
    }

    reports_to_create = 850
    states = list(state_weights.keys())
    weights = list(state_weights.values())

    for i in range(reports_to_create):
        state = random.choices(states, weights=weights)[0]
        district = random.choice(STATES_DISTRICTS[state])

        # Generate realistic date spread over 18 months
        days_ago = random.randint(0, 540)
        # More recent months have more data (growing awareness)
        if random.random() < 0.6:
            days_ago = random.randint(0, 180)
        created = datetime.utcnow() - timedelta(days=days_ago)

        debt_bucket_idx = random.choices(range(6), weights=[0.08, 0.22, 0.28, 0.24, 0.12, 0.06])[0]
        debt_lo, debt_hi = DEBT_RANGES[debt_bucket_idx]
        debt = random.randint(debt_lo, debt_hi) if debt_lo > 0 else 0

        num_pressure = random.randint(1, 5)
        pressure = random.sample(PRESSURE_TYPES, num_pressure)

        ongoing = random.choices(
            ["Yes — demands continue after marriage", "No — resolved after marriage", "No — but family still repaying loans", "Don't know"],
            weights=[0.45, 0.2, 0.25, 0.1]
        )[0]

        complaint = random.choices(
            ["No — feared retaliation", "No — social pressure", "No — didn't know process", "Yes — police / FIR", "Yes — NGO / helpline", "Attempted but discouraged"],
            weights=[0.35, 0.3, 0.2, 0.05, 0.05, 0.05]
        )[0]

        relation = random.choices(
            ["Affected woman (self)", "Parent of affected woman", "Sibling of affected woman", "Extended family", "Social worker / NGO"],
            weights=[0.40, 0.30, 0.15, 0.10, 0.05]
        )[0]

        fraud_score = random.choices([
            random.uniform(0.0, 0.1),
            random.uniform(0.1, 0.3),
            random.uniform(0.45, 0.65),
            random.uniform(0.85, 1.0)
        ], weights=[0.70, 0.15, 0.10, 0.05])[0]

        if fraud_score >= 0.85:
            status = ReportStatus.flagged
        elif fraud_score >= 0.45:
            status = random.choice([ReportStatus.flagged, ReportStatus.pending])
        elif random.random() < 0.3:
            status = ReportStatus.verified
        else:
            status = ReportStatus.pending

        report = Report(
            submission_token=generate_token(),
            state=state,
            district=district,
            year_of_marriage=random.randint(2015, 2024),
            relation_to_incident=relation,
            pressure_types=pressure,
            estimated_burden=BURDEN_OPTIONS[debt_bucket_idx],
            debt_amount=float(debt),
            ongoing_coercion=ongoing,
            complaint_filed=complaint,
            additional_details=None,
            ip_hash=f"demo_hash_{random.randint(1,200)}",
            fraud_score=round(fraud_score, 3),
            status=status,
            is_demo=True,
            created_at=created,
        )
        db.add(report)

    db.commit()
    print(f"Seeded {reports_to_create} demo reports.")