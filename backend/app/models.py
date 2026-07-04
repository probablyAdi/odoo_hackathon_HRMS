import enum
from datetime import date, datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Numeric,
    ForeignKey, Enum, Text, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    employee = "employee"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    half_day = "half_day"
    leave = "leave"


class LeaveType(str, enum.Enum):
    paid = "paid"
    sick = "sick"
    unpaid = "unpaid"


class LeaveStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    code = Column(String(5), nullable=False)
    logo_url = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="company")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    login_id = Column(String(30), unique=True, nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    first_name = Column(String(60), nullable=False)
    last_name = Column(String(60), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.employee)
    is_email_verified = Column(Boolean, default=False)
    must_change_password = Column(Boolean, default=False)
    profile_picture_url = Column(String(300))
    date_of_joining = Column(Date, default=date.today)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="users")
    profile = relationship("EmployeeProfile", back_populates="user", uselist=False,
                           cascade="all, delete-orphan",
                           foreign_keys="EmployeeProfile.user_id")
    salary = relationship("SalaryStructure", back_populates="user", uselist=False,
                           cascade="all, delete-orphan")
    skills = relationship("EmployeeSkill", cascade="all, delete-orphan")
    certifications = relationship("EmployeeCertification", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    job_position = Column(String(100))
    department = Column(String(100))
    manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    location = Column(String(120))
    date_of_birth = Column(Date)
    residing_address = Column(String(255))
    nationality = Column(String(60))
    personal_email = Column(String(150))
    gender = Column(String(20))
    marital_status = Column(String(20))
    bank_name = Column(String(100))
    account_number = Column(String(40))
    ifsc_code = Column(String(20))
    pan_no = Column(String(20))
    uan_no = Column(String(20))
    about = Column(Text)
    what_i_love = Column(Text)
    hobbies = Column(Text)

    user = relationship("User", back_populates="profile", foreign_keys=[user_id])


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(80), nullable=False)


class EmployeeCertification(Base):
    __tablename__ = "employee_certifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False)


class SalaryStructure(Base):
    __tablename__ = "salary_structures"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    monthly_wage = Column(Numeric(12, 2), default=0)
    working_days_per_week = Column(Integer, default=5)
    break_time_hours = Column(Numeric(4, 2), default=1)
    basic_pct = Column(Numeric(5, 2), default=50.00)
    hra_pct_of_basic = Column(Numeric(5, 2), default=50.00)
    standard_allowance_pct = Column(Numeric(5, 2), default=16.67)
    performance_bonus_pct = Column(Numeric(5, 2), default=8.33)
    lta_pct = Column(Numeric(5, 2), default=8.33)
    pf_employee_pct = Column(Numeric(5, 2), default=12.00)
    pf_employer_pct = Column(Numeric(5, 2), default=12.00)
    professional_tax = Column(Numeric(10, 2), default=200.00)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="salary")


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("user_id", "work_date", name="uq_attendance_user_date"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    work_date = Column(Date, nullable=False)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    status = Column(Enum(AttendanceStatus, name="attendance_status"), default=AttendanceStatus.absent, nullable=False)
    work_hours = Column(Numeric(5, 2), default=0)
    extra_hours = Column(Numeric(5, 2), default=0)


class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    __table_args__ = (UniqueConstraint("user_id", "leave_type", name="uq_leavebalance_user_type"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    leave_type = Column(Enum(LeaveType, name="leave_type"), nullable=False)
    total_days = Column(Numeric(5, 2), default=0)
    used_days = Column(Numeric(5, 2), default=0)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    __table_args__ = (CheckConstraint("end_date >= start_date", name="ck_leave_dates"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    leave_type = Column(Enum(LeaveType, name="leave_type"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_count = Column(Numeric(5, 2), nullable=False)
    remarks = Column(String(300))
    attachment_url = Column(String(300))
    status = Column(Enum(LeaveStatus, name="leave_status"), default=LeaveStatus.pending, nullable=False)
    admin_comment = Column(String(300))
    decided_by = Column(Integer, ForeignKey("users.id"))
    decided_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
