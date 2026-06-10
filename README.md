<div align="center">

<br />

```
██████╗  ██████╗ ██╗    ██╗██████╗ ██╗   ██╗██████╗ ███████╗██████╗ ████████╗
██╔══██╗██╔═══██╗██║    ██║██╔══██╗╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗╚══██╔══╝
██║  ██║██║   ██║██║ █╗ ██║██████╔╝ ╚████╔╝ ██║  ██║█████╗  ██████╔╝   ██║   
██║  ██║██║   ██║██║███╗██║██╔══██╗  ╚██╔╝  ██║  ██║██╔══╝  ██╔══██╗   ██║   
██████╔╝╚██████╔╝╚███╔███╔╝██║  ██║   ██║   ██████╔╝███████╗██████╔╝   ██║   
╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚══════╝╚═════╝    ╚═╝   
                          W A T C H
```

### *"Koi toh dekh raha hai."*
**India's first anonymous, district-level evidence repository for dowry-related financial abuse.**

<br />

[![Live](https://img.shields.io/badge/🔴%20LIVE-dowrydebt.onrender.com-C4384E?style=for-the-badge)](https://dowrydebt.onrender.com)
&nbsp;
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
&nbsp;
[![Python](https://img.shields.io/badge/Python%203.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
&nbsp;
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
&nbsp;

<br />

> **[🌐 Live Demo](https://dowrydebt.onrender.com)** &nbsp;·&nbsp; **[📊 Dashboard](https://dowrydebt.onrender.com/#dashboard)** &nbsp;·&nbsp; **[📋 Submit Report](https://dowrydebt.onrender.com/#report)** &nbsp;·&nbsp; **[🔌 API Docs](https://dowrydebt.onrender.com/docs)**

<br />

---

</div>

## 💔 The Problem Nobody Is Measuring

Every year in India, families take loans, sell ancestral land, and mortgage homes to meet dowry demands.

This debt follows them for **decades**.

It is never recorded as dowry-related in **any official dataset**.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   4.5 CRORE cases pending in Indian courts                      │
│   ₹0 in official district-level dowry debt data                 │
│   735 districts in India - 0 have a financial abuse map         │
│   1961 - year Dowry Prohibition Act was passed                  │
│   2026 - year enforcement data still doesn't exist              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Courts lack evidence. Policymakers lack maps. NGOs lack numbers.

**DowryDebt Watch creates the data that should have existed for 60 years.**

---

## ✨ What It Does

```
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│                      │    │                      │    │                      │
│  🔒 SUBMIT           │───▶│  🤖 AI CLEANS        │───▶│  📊 BECOMES          │
│  ANONYMOUSLY         │    │  THE DATA            │    │  EVIDENCE            │
│                      │    │                      │    │                      │
│  No name. No phone.  │    │  Fraud detection.    │    │  District maps.      │
│  No email. Ever.     │    │  PII scrubbing.      │    │  Court-ready data.   │
│                      │    │  Duplicate flagging. │    │  NGO toolkits.       │
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘
```

| Feature | What it means |
|--------|--------------|
| 🔒 **Zero-identity reporting** | No name, phone, or email. PII auto-scrubbed from text |
| 🤖 **AI Fraud Detection** | ML scoring flags duplicates and implausible submissions |
| 🗺️ **Live District Dashboard** | Real-time D3.js maps, charts, state-level breakdowns |
| ⚖️ **Legal Resource Hub** | PWDVA 2005, NCW, NALSA — everything in one place |
| 🏛️ **Admin Moderation Panel** | Verify, reject, review — with fraud queue |
| 🔌 **Evidence API** | Structured, citable data for researchers & courts |

---

## 🗺️ The Gap This Fills

| What exists today | What DowryDebt Watch adds |
|-------------------|--------------------------|
| NCRB: only registered FIRs | Pre-FIR financial burden data |
| Court records: individual cases | District-level pattern evidence |
| NGO reports: qualitative stories | Quantitative, structured, citable |
| National aggregates only | 735-district granularity |
| Annual publication, outdated | Real-time, live dashboard |
| English-only, expert-facing | Built for families and survivors |

---

## 🏗️ Architecture

```
dowrydebt/
│
├── 📄 index.html                 # Entire frontend - vanilla JS + D3.js
│                                 # No framework. No build step. Pure speed.
│
├── 📦 requirements.txt           # Python dependencies
├── 🐍 .python-version            # Pinned to 3.11.9
│
└── 🗂️ backend/
    ├── main.py                   # FastAPI — routes, CORS, lifespan
    ├── models.py                 # SQLAlchemy ORM models
    ├── schemas.py                # Pydantic request/response validation
    ├── crud.py                   # DB operations + analytics queries
    ├── fraud.py                  # 🤖 Fraud detection engine
    └── database.py               # SQLite (local) ↔ PostgreSQL (prod)
```

---

## 🚀 Run Locally

```bash
# Clone
git clone https://github.com/Bulletguitarist/Dowrydebt.git
cd Dowrydebt

# Setup
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install
pip install -r requirements.txt

# Launch
uvicorn backend.main:app --reload --port 8000

# Open → http://localhost:8000
```

---

## 🔌 API Reference

```
Base URL: https://dowrydebt.onrender.com
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/reports/submit` | Submit anonymous report |
| `GET` | `/api/dashboard/summary` | KPIs — total, districts, debt avg, coercion % |
| `GET` | `/api/dashboard/by-state` | State-wise aggregated breakdown |
| `GET` | `/api/dashboard/monthly-trend` | 12-month submission trend |
| `GET` | `/api/dashboard/map-data` | District coords + intensity for D3 map |
| `GET` | `/api/admin/reports` | 🔐 Paginated report list |
| `PATCH` | `/api/admin/reports/{id}/status` | 🔐 Verify or reject a report |

📖 **Interactive docs:** [`/docs`](https://dowrydebt.onrender.com/docs)

---

## 🛡️ Privacy By Design

```
What we NEVER collect          What we DO collect
──────────────────────         ─────────────────────────────
✗ Name                         ✓ State + District (only)
✗ Phone number                 ✓ Debt amount range
✗ Email address                ✓ Type of financial pressure
✗ Street address               ✓ Year of incident
✗ Aadhaar / ID                 ✓ Whether complaint was filed
✗ Raw IP address               ✓ Hashed IP (fraud only, never stored raw)
```

- Regex PII scrubber auto-removes any phone/email/Aadhaar in text fields
- Aggregation floor: districts with < 3 reports suppressed from public dashboard
- No cookies. No trackers. No analytics. No ads. Ever.

---

## 🧠 AI / ML Components

```python
# Fraud Detection Engine (backend/fraud.py)

def score_submission(report, db, ip_hash):
    score = 0
    
    # Velocity check - too many from same IP
    if recent_submissions_from_ip(ip_hash, db) > THRESHOLD:
        score += 40
    
    # Implausibility check - debt > 10x state median
    if report.debt_amount > state_median(report.state, db) * 10:
        score += 25
    
    # Duplicate pattern detection
    if is_duplicate_pattern(report, db):
        score += 35
    
    return "flagged" if score > 60 else "pending"
```

---

## 🗓️ Roadmap

- [ ] Hindi + regional language form (Marathi, Tamil, Bengali)
- [ ] WhatsApp-based submission for feature phone users
- [ ] NGO verified partner API access
- [ ] Court-ready PDF evidence export
- [ ] SMS surge alerts for high-risk districts
- [ ] Integration with NCW and NALSA databases
- [ ] Offline PWA mode for low-connectivity areas

---

## Built by

THE BRATS - Ashvini Goswami & Jyotirmoy Mahapatra

> The Dowry Prohibition Act was passed in **1961**.
> It is **2026**.
> The enforcement data has never existed.
> 
> DowryDebt Watch creates it - one anonymous submission at a time.

---

<div align="center">

<br />

**DowryDebt Watch**

*District-level evidence, made visible.*

[dowrydebt.onrender.com](https://dowrydebt.onrender.com)

<br />

*Built with rage, care, and FastAPI.*

</div>
