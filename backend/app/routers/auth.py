from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models, schemas
from app.security import hash_password, verify_password, create_access_token
from app.utils.id_generator import make_company_code, generate_login_id
from app.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.SignupRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    # Reuse the company if it already exists (case-insensitive), else create it.
    company = (
        db.query(models.Company)
        .filter(func_lower_eq(models.Company.name, payload.company_name))
        .first()
    )
    if not company:
        company = models.Company(
            name=payload.company_name,
            code=make_company_code(payload.company_name),
            logo_url=payload.logo_url
        )
        db.add(company)
        db.flush()  # get company.id without committing

    year = date.today().year
    login_id = generate_login_id(db, company.code, payload.first_name, payload.last_name, year)

    user = models.User(
        login_id=login_id,
        company_id=company.id,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=payload.email.lower(),
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=models.UserRole.admin if payload.role == "admin" else models.UserRole.employee,
        is_email_verified=False,  # prototype: verification email is not actually sent, see README
        date_of_joining=date.today(),
    )
    db.add(user)
    db.flush()

    db.add(models.EmployeeProfile(user_id=user.id))
    db.add(models.SalaryStructure(user_id=user.id))
    for lt, total in (
        (models.LeaveType.paid, 24),
        (models.LeaveType.sick, 7),
        (models.LeaveType.unpaid, 0),
    ):
        db.add(models.LeaveBalance(user_id=user.id, leave_type=lt, total_days=total))

    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return schemas.TokenResponse(
        access_token=token,
        role=user.role.value,
        login_id=user.login_id,
        full_name=user.full_name,
        must_change_password=user.must_change_password,
        company_name=company.name,
        company_logo_url=company.logo_url,
    )


def func_lower_eq(column, value):
    from sqlalchemy import func
    return func.lower(column) == value.strip().lower()


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(models.User)
        .filter(or_(models.User.login_id == payload.login, models.User.email == payload.login.lower()))
        .first()
    )
    # Same generic error for "no such user" and "wrong password" -- don't leak which one.
    invalid = HTTPException(status_code=401, detail="Incorrect login ID/email or password.")
    if not user or not verify_password(payload.password, user.password_hash):
        raise invalid
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated. Contact HR.")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return schemas.TokenResponse(
        access_token=token,
        role=user.role.value,
        login_id=user.login_id,
        full_name=user.full_name,
        must_change_password=user.must_change_password,
        company_name=user.company.name,
        company_logo_url=user.company.logo_url,
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    current_user.password_hash = hash_password(payload.new_password)
    current_user.must_change_password = False
    db.commit()
