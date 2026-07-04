from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator

# ---------------------------------------------------------------- auth
class SignupRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=150)
    logo_url: Optional[str] = None
    first_name: str = Field(..., min_length=1, max_length=60)
    last_name: str = Field(..., min_length=1, max_length=60)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)
    confirm_password: str
    role: str = Field(default="employee", pattern="^(employee|admin)$")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class EmployeeCreateRequest(BaseModel):
    """Used by Admin/HR to add a new employee to their own company (no
    company_name/password needed -- the server generates a temp password)."""
    first_name: str = Field(..., min_length=1, max_length=60)
    last_name: str = Field(..., min_length=1, max_length=60)
    email: EmailStr
    phone: Optional[str] = None
    role: str = Field(default="employee", pattern="^(employee|admin)$")


class LoginRequest(BaseModel):
    login: str  # login_id OR email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    login_id: str
    full_name: str
    must_change_password: bool
    company_name: str
    company_logo_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class EmployeeCreatedOut(BaseModel):
    login_id: str
    full_name: str
    role: str
    temp_password: str  # shown once at creation time; in production this would be emailed, not returned


# ---------------------------------------------------------------- employees
class EmployeeCard(BaseModel):
    id: int
    login_id: str
    full_name: str
    job_position: Optional[str] = None
    profile_picture_url: Optional[str] = None
    attendance_status_today: str  # present | leave | absent

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    phone: Optional[str] = None
    profile_picture_url: Optional[str] = None
    residing_address: Optional[str] = None
    job_position: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    personal_email: Optional[EmailStr] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    pan_no: Optional[str] = None
    uan_no: Optional[str] = None
    about: Optional[str] = None
    what_i_love: Optional[str] = None
    hobbies: Optional[str] = None


class ProfileOut(BaseModel):
    id: int
    login_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    role: str
    profile_picture_url: Optional[str] = None
    date_of_joining: date
    job_position: Optional[str] = None
    department: Optional[str] = None
    manager_name: Optional[str] = None
    location: Optional[str] = None
    date_of_birth: Optional[date] = None
    residing_address: Optional[str] = None
    nationality: Optional[str] = None
    personal_email: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    pan_no: Optional[str] = None
    uan_no: Optional[str] = None
    about: Optional[str] = None
    what_i_love: Optional[str] = None
    hobbies: Optional[str] = None
    skills: List[str] = []
    certifications: List[str] = []


# ---------------------------------------------------------------- attendance
class CheckInOut(BaseModel):
    pass


class AttendanceRow(BaseModel):
    work_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: str
    work_hours: float
    extra_hours: float
    employee_name: Optional[str] = None  # populated for admin list view


# ---------------------------------------------------------------- leave / time off
class LeaveApply(BaseModel):
    leave_type: str = Field(..., pattern="^(paid|sick|unpaid)$")
    start_date: date
    end_date: date
    remarks: Optional[str] = Field(None, max_length=300)
    attachment_url: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("End date cannot be before start date")
        return v


class LeaveDecision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    admin_comment: Optional[str] = Field(None, max_length=300)


class LeaveOut(BaseModel):
    id: int
    employee_name: Optional[str] = None
    leave_type: str
    start_date: date
    end_date: date
    days_count: float
    remarks: Optional[str] = None
    status: str
    admin_comment: Optional[str] = None


class LeaveBalanceOut(BaseModel):
    leave_type: str
    total_days: float
    used_days: float
    available_days: float


# ---------------------------------------------------------------- payroll
class SalaryStructureUpdate(BaseModel):
    monthly_wage: float = Field(..., ge=0)
    working_days_per_week: int = Field(5, ge=1, le=7)
    break_time_hours: float = Field(1, ge=0, le=8)
    basic_pct: float = Field(50.00, ge=0, le=100)
    hra_pct_of_basic: float = Field(50.00, ge=0, le=100)
    standard_allowance_pct: float = Field(16.67, ge=0, le=100)
    performance_bonus_pct: float = Field(8.33, ge=0, le=100)
    lta_pct: float = Field(8.33, ge=0, le=100)
    pf_employee_pct: float = Field(12.00, ge=0, le=100)
    pf_employer_pct: float = Field(12.00, ge=0, le=100)
    professional_tax: float = Field(200.00, ge=0)


class SalaryComponent(BaseModel):
    name: str
    amount: float
    percent_of_wage: float
    description: str


class PayrollOut(BaseModel):
    monthly_wage: float
    yearly_wage: float
    working_days_per_week: int
    break_time_hours: float
    components: List[SalaryComponent]
    pf_employee: float
    pf_employer: float
    professional_tax: float
    net_pay: float
    # Raw % rules, echoed back so the admin edit form can be pre-filled
    # with the values actually driving the computation above.
    basic_pct: float
    hra_pct_of_basic: float
    standard_allowance_pct: float
    performance_bonus_pct: float
    lta_pct: float
    pf_employee_pct: float
    pf_employer_pct: float
