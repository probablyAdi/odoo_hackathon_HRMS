import secrets
import string
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, require_admin
from app.security import hash_password
from app.utils.id_generator import generate_login_id

router = APIRouter(prefix="/api/employees", tags=["employees"])


def _today_status(db: Session, user_id: int) -> str:
    row = db.query(models.Attendance).filter(
        models.Attendance.user_id == user_id, models.Attendance.work_date == date.today()
    ).first()
    if not row:
        return "absent"
    if row.status == models.AttendanceStatus.leave:
        return "leave"
    if row.check_in and not row.check_out:
        return "present"
    if row.status == models.AttendanceStatus.present:
        return "present"
    return row.status.value


@router.get("", response_model=list[schemas.EmployeeCard])
def list_employees(
    search: str = "",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Employee directory cards. Every authenticated user can browse the
    directory (read-only names/roles); only Admin/HR can edit others."""
    q = db.query(models.User).filter(models.User.company_id == current_user.company_id)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter((models.User.first_name + " " + models.User.last_name).ilike(like))
    users = q.order_by(models.User.first_name).all()

    cards = []
    for u in users:
        cards.append(schemas.EmployeeCard(
            id=u.id,
            login_id=u.login_id,
            full_name=u.full_name,
            job_position=u.profile.job_position if u.profile else None,
            profile_picture_url=u.profile_picture_url,
            attendance_status_today=_today_status(db, u.id),
        ))
    return cards


def _build_profile_out(db: Session, user: models.User) -> schemas.ProfileOut:
    p = user.profile
    manager_name = None
    if p and p.manager_id:
        mgr = db.query(models.User).filter(models.User.id == p.manager_id).first()
        manager_name = mgr.full_name if mgr else None

    return schemas.ProfileOut(
        id=user.id,
        login_id=user.login_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
        role=user.role.value,
        profile_picture_url=user.profile_picture_url,
        date_of_joining=user.date_of_joining,
        job_position=p.job_position if p else None,
        department=p.department if p else None,
        manager_name=manager_name,
        location=p.location if p else None,
        date_of_birth=p.date_of_birth if p else None,
        residing_address=p.residing_address if p else None,
        nationality=p.nationality if p else None,
        personal_email=p.personal_email if p else None,
        gender=p.gender if p else None,
        marital_status=p.marital_status if p else None,
        bank_name=p.bank_name if p else None,
        account_number=p.account_number if p else None,
        ifsc_code=p.ifsc_code if p else None,
        pan_no=p.pan_no if p else None,
        uan_no=p.uan_no if p else None,
        about=p.about if p else None,
        what_i_love=p.what_i_love if p else None,
        hobbies=p.hobbies if p else None,
        skills=[s.name for s in user.skills],
        certifications=[c.name for c in user.certifications],
    )


@router.get("/me", response_model=schemas.ProfileOut)
def get_my_profile(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return _build_profile_out(db, current_user)


@router.get("/{employee_id}", response_model=schemas.ProfileOut)
def get_employee_profile(
    employee_id: int, db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """View-only profile lookup, used when an admin clicks an employee card."""
    user = db.query(models.User).filter(
        models.User.id == employee_id, models.User.company_id == current_user.company_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found.")
    if current_user.role != models.UserRole.admin and current_user.id != employee_id:
        raise HTTPException(status_code=403, detail="You can only view your own profile.")
    return _build_profile_out(db, user)


@router.put("/me", response_model=schemas.ProfileOut)
def update_my_profile(
    payload: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Employees can edit only a limited set of fields on themselves
    (address, phone, profile picture, personal details) -- not job/salary."""
    editable_self_fields = {
        "phone", "profile_picture_url", "residing_address", "date_of_birth",
        "nationality", "personal_email", "gender", "marital_status",
        "bank_name", "account_number", "ifsc_code", "pan_no", "uan_no",
        "about", "what_i_love", "hobbies",
    }
    _apply_profile_update(db, current_user, payload, editable_self_fields)
    return _build_profile_out(db, current_user)


@router.put("/{employee_id}", response_model=schemas.ProfileOut)
def admin_update_employee(
    employee_id: int,
    payload: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Admin can edit all fields for any employee in their company."""
    user = db.query(models.User).filter(
        models.User.id == employee_id, models.User.company_id == admin.company_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found.")
    all_fields = set(schemas.ProfileUpdate.model_fields.keys())
    _apply_profile_update(db, user, payload, all_fields)
    return _build_profile_out(db, user)


def _apply_profile_update(db, user, payload: schemas.ProfileUpdate, allowed_fields: set):
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field not in allowed_fields:
            continue
        if field in ("phone", "profile_picture_url"):
            setattr(user, field, value)
        else:
            setattr(user.profile, field, value)
    db.commit()


@router.post("/me/skills", response_model=list[str])
def add_skill(name: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Skill name cannot be empty.")
    db.add(models.EmployeeSkill(user_id=current_user.id, name=name))
    db.commit()
    db.refresh(current_user)
    return [s.name for s in current_user.skills]


@router.post("/me/certifications", response_model=list[str])
def add_certification(name: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Certification name cannot be empty.")
    db.add(models.EmployeeCertification(user_id=current_user.id, name=name))
    db.commit()
    db.refresh(current_user)
    return [c.name for c in current_user.certifications]


@router.post("", response_model=schemas.EmployeeCreatedOut, status_code=201)
def admin_create_employee(
    payload: schemas.EmployeeCreateRequest,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Admin/HR creates a new employee. A random temp password is generated
    and the account is flagged must_change_password, per the design note:
    'password should be auto generated for the first time by the system.'"""
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    company = db.query(models.Company).filter(models.Company.id == admin.company_id).first()
    year = date.today().year
    login_id = generate_login_id(db, company.code, payload.first_name, payload.last_name, year)

    temp_password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))

    user = models.User(
        login_id=login_id,
        company_id=company.id,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=payload.email.lower(),
        phone=payload.phone,
        password_hash=hash_password(temp_password),
        role=models.UserRole.admin if payload.role == "admin" else models.UserRole.employee,
        is_email_verified=False,
        must_change_password=True,
        date_of_joining=date.today(),
    )
    db.add(user)
    db.flush()
    db.add(models.EmployeeProfile(user_id=user.id))
    db.add(models.SalaryStructure(user_id=user.id))
    for lt, total in (
        (models.LeaveType.paid, 24), (models.LeaveType.sick, 7), (models.LeaveType.unpaid, 0)
    ):
        db.add(models.LeaveBalance(user_id=user.id, leave_type=lt, total_days=total))
    db.commit()
    db.refresh(user)

    # In production this temp password would be emailed, not returned in the
    # API response. Returned here so the hackathon demo can show it on-screen.
    return schemas.EmployeeCreatedOut(
        login_id=user.login_id,
        full_name=user.full_name,
        role=user.role.value,
        temp_password=temp_password,
    )
