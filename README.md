# 🏢 HRMS Portal — Human Resource Management System

> A full-stack, multi-tenant HRMS built with **FastAPI** + **PostgreSQL** + **Vanilla JS**  
> Dark-mode, Linear-inspired UI with real-time attendance, leave management, and payroll.

---

## ✨ Features

| Module | Highlights |
|--------|-----------|
| **🔐 Auth** | JWT login/signup, company registration, auto-generated employee passwords, forced first-login password reset |
| **👥 Employee Directory** | Grid cards with live attendance dots (🟢 Present · ✈️ Leave · 🟡 Absent), search, admin onboarding |
| **📋 Attendance** | One-click Check In / Check Out with timestamps, admin-view daily logs for all employees |
| **🏖️ Time Off** | Balance trackers, interactive calendar, leave request with allocation calculator, admin approve/reject workflow |
| **💰 Payroll** | CTC-based salary breakdown (Basic, HRA, Allowances, LTA, PF, Professional Tax), auto-calculated net pay |
| **👤 Profile** | Resume (About, Skills, Certifications), Private Info (Bank, PAN, UAN), Salary Info (admin/self only), Security tab |
| **🏗️ Multi-Tenant** | Every query is scoped by `company_id` — multiple companies share one DB with zero data leakage |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, FastAPI, SQLAlchemy ORM, Alembic-ready |
| **Database** | PostgreSQL 14+ with ENUMs, indexes, and cascading FKs |
| **Auth** | JWT (python-jose) + bcrypt password hashing |
| **Frontend** | Vanilla HTML/CSS/JS — no frameworks, no build step |
| **Design** | Dark mode, glassmorphism panels, CSS variables, micro-animations |

---

## 📁 Project Structure

```
hrms/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── database.py          # DB session management
│   │   ├── security.py          # Password hashing (bcrypt)
│   │   ├── deps.py              # Auth dependencies (JWT)
│   │   ├── config.py            # Environment config
│   │   ├── routers/
│   │   │   ├── auth.py          # Login, Signup, Password change
│   │   │   ├── employees.py     # CRUD, profile, skills, certs
│   │   │   ├── attendance.py    # Check-in/out, admin logs
│   │   │   ├── timeoff.py       # Leave apply, approve, reject
│   │   │   └── payroll.py       # Salary structure & breakdown
│   │   └── utils/
│   │       ├── id_generator.py  # Login ID generator (ACM-JD-2026-001)
│   │       └── salary_calc.py   # CTC → component calculator
│   ├── schema.sql               # PostgreSQL DDL (tables, enums, indexes)
│   ├── seed.py                  # Demo data seeder
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html               # Sign In page
│   ├── signup.html              # Company registration
│   ├── dashboard.html           # Employee grid + check-in
│   ├── profile.html             # Multi-tab profile viewer
│   ├── attendance.html          # Attendance log history
│   ├── timeoff.html             # Leave balance, calendar, requests
│   ├── change-password.html     # First-login password reset
│   ├── css/style.css            # Full design system
│   └── js/
│       ├── api.js               # Fetch wrapper with JWT injection
│       └── shell.js             # Shared nav, sidebar, toast system
├── docs/
│   └── ARCHITECTURE.md          # Technical architecture doc
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **PostgreSQL 14+** (running locally)
- **pip** (Python package manager)

### 1. Clone the Repo
```bash
git clone https://github.com/probablyAdi/odoo_hackathon_HRMS.git
cd odoo_hackathon_HRMS
```

### 2. Set Up the Database
```bash
# Open psql or pgAdmin and create the database
createdb -U postgres hrms_db
```

### 3. Configure Environment
```bash
cd backend
copy .env.example .env
# Edit .env and set your PostgreSQL password:
# DB_PASSWORD=your_actual_password
```

### 4. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 5. Initialize Tables & Seed Data
```bash
# Tables are auto-created on first run via schema.sql
python seed.py
```

### 6. Start the Servers

**Backend** (Terminal 1):
```bash
cd backend
uvicorn app.main:app --reload
# API running at http://localhost:8000
```

**Frontend** (Terminal 2):
```bash
cd frontend
python -m http.server 5500
# UI running at http://localhost:5500
```

### 7. Login with Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `priya.admin@example.com` | `Passw0rd!` |
| **Employee** | `john.doe@example.com` | `Passw0rd!` |

---

## 📸 Pages Overview

| Page | Description |
|------|-------------|
| **Sign In** | Email + password with show/hide toggle |
| **Sign Up** | Register company with logo upload |
| **Dashboard** | Employee grid with live status dots, check-in systray |
| **Profile** | Resume, Private Info, Salary Info (admin), Security tabs |
| **Attendance** | Daily check-in/out logs with admin overview |
| **Time Off** | Balance cards, interactive calendar, request modal with allocation calc |

---

## 🔒 Multi-Tenancy

This app supports **multiple companies** on a single database. Every API query filters by `company_id`, ensuring:
- Company A's admin **cannot** see Company B's employees
- Attendance, leave, and payroll data are **fully isolated**
- Each signup creates a new company with its own data silo

---

## 📄 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/signup` | Register company + admin |
| `POST` | `/api/auth/login` | JWT login |
| `POST` | `/api/auth/change-password` | Update password |
| `GET` | `/api/employees` | List company employees |
| `GET` | `/api/employees/me` | My profile |
| `POST` | `/api/employees` | Admin: onboard new employee |
| `POST` | `/api/attendance/checkin` | Clock in |
| `POST` | `/api/attendance/checkout` | Clock out |
| `GET` | `/api/attendance/today` | Today's status |
| `POST` | `/api/timeoff/apply` | Submit leave request |
| `GET` | `/api/timeoff/balances` | My leave balances |
| `POST` | `/api/timeoff/{id}/decide` | Admin: approve/reject |
| `GET` | `/api/payroll/{id}` | Salary breakdown |

---

## 👥 Team

Built during the **Odoo Hackathon** 🚀

---

## 📝 License

This project is for educational and hackathon purposes.
