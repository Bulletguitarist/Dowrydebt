"""
AI-powered fraud detection for DowryDebt Watch
Analyzes reports for duplicate submissions, implausible data, and spam patterns.
"""

import hashlib
import re
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models

FRAUD_RULES = {
    "ip_rate_limit_hour": 5,      # max submissions from same IP per hour
    "ip_rate_limit_day": 15,      # max per day
    "min_debt_plausible": 0,
    "max_debt_plausible": 100_000_000,  # 10 crore
    "suspicious_keywords": [
        "test", "testing", "fake", "dummy", "sample", "lorem", "asdf",
        "qwerty", "aaaa", "1234", "abcd", "xyz"
    ],
    "block_threshold": 0.85,
    "flag_threshold": 0.45,
}

def hash_ip(ip: str) -> str:
    """One-way hash of IP for rate limiting without storing raw IP"""
    salt = "dowrywatch_2024_salt"
    return hashlib.sha256(f"{salt}{ip}".encode()).hexdigest()

def analyze_report(report, ip_hash: str, db: Session) -> dict:
    """
    Returns fraud analysis result:
    - fraud_score: 0.0 (clean) to 1.0 (definite fraud)
    - action: 'allow' | 'flag' | 'block'
    - reason: human-readable explanation
    """
    signals = []
    score = 0.0

    # ── Signal 1: IP Rate Limiting ────────────────────────────
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    one_day_ago = datetime.utcnow() - timedelta(days=1)

    hourly_count = db.query(func.count(models.Report.id)).filter(
        models.Report.ip_hash == ip_hash,
        models.Report.created_at >= one_hour_ago
    ).scalar() or 0

    daily_count = db.query(func.count(models.Report.id)).filter(
        models.Report.ip_hash == ip_hash,
        models.Report.created_at >= one_day_ago
    ).scalar() or 0

    if hourly_count >= FRAUD_RULES["ip_rate_limit_hour"]:
        score += 0.9
        signals.append(f"IP rate limit: {hourly_count} submissions in last hour")
    elif hourly_count >= 3:
        score += 0.3
        signals.append(f"Elevated IP rate: {hourly_count} in last hour")

    if daily_count >= FRAUD_RULES["ip_rate_limit_day"]:
        score += 0.5
        signals.append(f"Daily IP limit exceeded: {daily_count} submissions")

    # ── Signal 2: Duplicate Detection ─────────────────────────
    recent_from_ip = db.query(models.Report).filter(
        models.Report.ip_hash == ip_hash,
        models.Report.state == report.state,
        models.Report.district == report.district,
        models.Report.created_at >= one_day_ago
    ).count()

    if recent_from_ip >= 2:
        score += 0.5
        signals.append("Duplicate: same district from same IP today")

    # ── Signal 3: Implausible Financial Data ──────────────────
    if report.debt_amount and report.debt_amount > 0:
        if report.debt_amount > FRAUD_RULES["max_debt_plausible"]:
            score += 0.4
            signals.append(f"Implausible debt: ₹{report.debt_amount:,.0f}")
        elif report.debt_amount > 50_000_000:  # 5 crore — suspicious but possible
            score += 0.15
            signals.append("Unusually high debt amount")

    # ── Signal 4: Suspicious Text Content ─────────────────────
    if report.additional_details:
        text_lower = report.additional_details.lower()
        found_keywords = [kw for kw in FRAUD_RULES["suspicious_keywords"] if kw in text_lower]
        if len(found_keywords) >= 3:
            score += 0.6
            signals.append(f"Suspicious keywords detected: {found_keywords[:3]}")
        elif len(found_keywords) >= 1:
            score += 0.15
            signals.append(f"Some suspicious terms in text")

        # Very short meaningless text
        if len(report.additional_details.strip()) < 10 and len(report.additional_details.strip()) > 0:
            score += 0.1

    # ── Signal 5: Missing Critical Data Pattern ───────────────
    if not report.pressure_types or len(report.pressure_types) == 0:
        score += 0.05

    # All fields empty except required ones = likely bot
    filled_optional = sum([
        bool(report.year_of_marriage),
        bool(report.relation_to_incident),
        bool(report.estimated_burden),
        bool(report.ongoing_coercion),
        bool(report.complaint_filed),
    ])
    if filled_optional == 0:
        score += 0.1
        signals.append("No optional fields filled — possible bot")

    # ── Signal 6: District/State Consistency ─────────────────
    known_districts = _get_known_districts()
    state_key = report.state.lower().strip()
    district_lower = report.district.lower().strip()
    if state_key in known_districts:
        valid_districts = known_districts[state_key]
        if district_lower not in valid_districts:
            # Partial match check
            partial_match = any(district_lower in d or d in district_lower for d in valid_districts)
            if not partial_match:
                score += 0.2
                signals.append(f"District '{report.district}' not recognized in {report.state}")

    # Cap score at 1.0
    score = min(score, 1.0)

    # Determine action
    if score >= FRAUD_RULES["block_threshold"]:
        action = "block"
        reason = "Submission blocked due to high fraud risk: " + "; ".join(signals[:2])
    elif score >= FRAUD_RULES["flag_threshold"]:
        action = "flag"
        reason = "Submission flagged for review: " + "; ".join(signals[:2])
    else:
        action = "allow"
        reason = "Clean submission"

    return {
        "fraud_score": round(score, 3),
        "action": action,
        "reason": reason,
        "signals": signals
    }

def _get_known_districts() -> dict:
    return {
        "uttar pradesh": ["lucknow", "kanpur", "agra", "varanasi", "allahabad", "prayagraj",
                          "meerut", "bareilly", "aligarh", "moradabad", "ghaziabad", "noida",
                          "gorakhpur", "faizabad", "ayodhya", "mathura", "etawah", "jhansi",
                          "sitapur", "hardoi", "unnao", "rae bareli", "sultanpur", "azamgarh"],
        "bihar": ["patna", "gaya", "muzaffarpur", "bhagalpur", "darbhanga", "purnia",
                  "araria", "begusarai", "nalanda", "nawada", "rohtas", "siwan",
                  "chapra", "saran", "vaishali", "sitamarhi", "madhubani"],
        "rajasthan": ["jaipur", "jodhpur", "udaipur", "kota", "ajmer", "bikaner",
                      "alwar", "bharatpur", "sikar", "pali", "barmer", "jaisalmer",
                      "churu", "hanumangarh", "nagaur", "jhunjhunu", "tonk"],
        "haryana": ["gurgaon", "gurugram", "faridabad", "hisar", "rohtak", "panipat",
                    "ambala", "karnal", "sonipat", "bhiwani", "sirsa", "rewari",
                    "jhajjar", "kaithal", "kurukshetra", "yamunanagar"],
        "maharashtra": ["mumbai", "pune", "nagpur", "nashik", "aurangabad", "thane",
                        "solapur", "kolhapur", "nanded", "sangli", "satara", "jalgaon",
                        "latur", "ahmednagar", "raigad", "ratnagiri"],
        "madhya pradesh": ["bhopal", "indore", "jabalpur", "gwalior", "ujjain", "sagar",
                           "rewa", "satna", "chhindwara", "morena", "vidisha", "betul"],
        "gujarat": ["ahmedabad", "surat", "vadodara", "rajkot", "bhavnagar", "jamnagar",
                    "gandhinagar", "anand", "mehsana", "patan", "banaskantha"],
        "west bengal": ["kolkata", "howrah", "durgapur", "asansol", "siliguri", "malda",
                        "murshidabad", "burdwan", "nadia", "north 24 parganas"],
    }