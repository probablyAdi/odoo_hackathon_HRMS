-- ============================================================
-- HRMS Database Schema (PostgreSQL)
-- ============================================================
-- Run this once against an empty database:
--   psql -U postgres -d hrms -f schema.sql
--
-- SQLAlchemy (app/models.py) will also create these tables
-- automatically on first run, but this file is kept as the
-- readable, reviewable source of truth for the DB design --
-- useful for the hackathon judges and for manual setup.
-- ============================================================

CREATE TYPE user_role       AS ENUM ('admin', 'employee');
CREATE TYPE attendance_status AS ENUM ('present', 'absent', 'half_day', 'leave');
CREATE TYPE leave_type      AS ENUM ('paid', 'sick', 'unpaid');
CREATE TYPE leave_status    AS ENUM ('pending', 'approved', 'rejected');

-- ------------------------------------------------------------
CREATE TABLE companies (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    code        VARCHAR(5)  NOT NULL,           -- e.g. "OI" for Odoo India, used in login-id generation
    logo_url    VARCHAR(300),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
CREATE TABLE users (
    id                   SERIAL PRIMARY KEY,
    login_id             VARCHAR(30)  NOT NULL UNIQUE,   -- auto-generated e.g. OIJODO20260001
    company_id           INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    first_name           VARCHAR(60) NOT NULL,
    last_name             VARCHAR(60) NOT NULL,
    email                VARCHAR(150) NOT NULL UNIQUE,
    phone                VARCHAR(20),
    password_hash        VARCHAR(255) NOT NULL,
    role                 user_role NOT NULL DEFAULT 'employee',
    is_email_verified    BOOLEAN NOT NULL DEFAULT FALSE,
    must_change_password BOOLEAN NOT NULL DEFAULT FALSE,
    profile_picture_url  VARCHAR(300),
    date_of_joining       DATE NOT NULL DEFAULT CURRENT_DATE,
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_company ON users(company_id);

-- ------------------------------------------------------------
-- Job / private details (1-to-1 with users, split out so the
-- "Private Info" tab in the profile page maps directly to a table)
CREATE TABLE employee_profiles (
    user_id           INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    job_position      VARCHAR(100),
    department        VARCHAR(100),
    manager_id        INTEGER REFERENCES users(id) ON DELETE SET NULL,
    location          VARCHAR(120),
    date_of_birth     DATE,
    residing_address  VARCHAR(255),
    nationality       VARCHAR(60),
    personal_email    VARCHAR(150),
    gender            VARCHAR(20),
    marital_status    VARCHAR(20),
    bank_name         VARCHAR(100),
    account_number    VARCHAR(40),
    ifsc_code         VARCHAR(20),
    pan_no            VARCHAR(20),
    uan_no            VARCHAR(20),
    about             TEXT,
    what_i_love       TEXT,
    hobbies           TEXT
);

CREATE TABLE employee_skills (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(80) NOT NULL
);

CREATE TABLE employee_certifications (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(120) NOT NULL
);

-- ------------------------------------------------------------
-- Salary structure: admin-defined wage + auto-computed components
CREATE TABLE salary_structures (
    user_id                 INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    monthly_wage            NUMERIC(12,2) NOT NULL DEFAULT 0,
    working_days_per_week   INTEGER NOT NULL DEFAULT 5,
    break_time_hours        NUMERIC(4,2) NOT NULL DEFAULT 1,
    basic_pct               NUMERIC(5,2) NOT NULL DEFAULT 50.00,
    hra_pct_of_basic        NUMERIC(5,2) NOT NULL DEFAULT 50.00,
    standard_allowance_pct  NUMERIC(5,2) NOT NULL DEFAULT 16.67,
    performance_bonus_pct   NUMERIC(5,2) NOT NULL DEFAULT 8.33,
    lta_pct                 NUMERIC(5,2) NOT NULL DEFAULT 8.33,
    pf_employee_pct         NUMERIC(5,2) NOT NULL DEFAULT 12.00,
    pf_employer_pct         NUMERIC(5,2) NOT NULL DEFAULT 12.00,
    professional_tax        NUMERIC(10,2) NOT NULL DEFAULT 200.00,
    updated_at              TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
CREATE TABLE attendance (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    work_date     DATE NOT NULL,
    check_in      TIMESTAMP,
    check_out     TIMESTAMP,
    status        attendance_status NOT NULL DEFAULT 'absent',
    work_hours    NUMERIC(5,2) DEFAULT 0,
    extra_hours   NUMERIC(5,2) DEFAULT 0,
    UNIQUE (user_id, work_date)
);

CREATE INDEX idx_attendance_date ON attendance(work_date);

-- ------------------------------------------------------------
CREATE TABLE leave_balances (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    leave_type   leave_type NOT NULL,
    total_days   NUMERIC(5,2) NOT NULL DEFAULT 0,
    used_days    NUMERIC(5,2) NOT NULL DEFAULT 0,
    UNIQUE (user_id, leave_type)
);

CREATE TABLE leave_requests (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    leave_type     leave_type NOT NULL,
    start_date     DATE NOT NULL,
    end_date       DATE NOT NULL,
    days_count     NUMERIC(5,2) NOT NULL,
    remarks        VARCHAR(300),
    attachment_url VARCHAR(300),
    status         leave_status NOT NULL DEFAULT 'pending',
    admin_comment  VARCHAR(300),
    decided_by     INTEGER REFERENCES users(id),
    decided_at     TIMESTAMP,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    CHECK (end_date >= start_date)
);

CREATE INDEX idx_leave_requests_user ON leave_requests(user_id);
CREATE INDEX idx_leave_requests_status ON leave_requests(status);
