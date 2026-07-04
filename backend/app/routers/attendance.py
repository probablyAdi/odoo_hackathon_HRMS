from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, require_admin

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


def _get_or_create_today(db: Session, user_id: int) -> models.Attendance:
    row = db.query(models.Attendance).filter(
        models.Attendance.user_id == user_id, models.Attendance.work_date == date.today()
    ).first()
    if not row:
        row = models.Attendance(user_id=user_id, work_date=date.today(), status=models.AttendanceStatus.absent)
        db.add(row)
        db.flush()
    return row


@router.post("/check-in")
def check_in(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    row = _get_or_create_today(db, current_user.id)
    if row.check_in:
        raise HTTPException(status_code=400, detail="You have already checked in today.")
    row.check_in = datetime.utcnow()
    row.status = models.AttendanceStatus.present
    db.commit()
    return {"message": "Checked in successfully.", "check_in": row.check_in}


@router.post("/check-out")
def check_out(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    row = db.query(models.Attendance).filter(
        models.Attendance.user_id == current_user.id, models.Attendance.work_date == date.today()
    ).first()
    if not row or not row.check_in:
        raise HTTPException(status_code=400, detail="You must check in before checking out.")
    if row.check_out:
        raise HTTPException(status_code=400, detail="You have already checked out today.")

    row.check_out = datetime.utcnow()
    total_seconds = (row.check_out - row.check_in).total_seconds()
    hours = max(total_seconds / 3600, 0)
    standard_day = 8.0
    row.work_hours = round(min(hours, standard_day), 2)
    row.extra_hours = round(max(hours - standard_day, 0), 2)
    if hours < standard_day / 2:
        row.status = models.AttendanceStatus.half_day
    db.commit()
    return {"message": "Checked out successfully.", "check_out": row.check_out, "work_hours": row.work_hours}


@router.get("/me", response_model=list[schemas.AttendanceRow])
def my_attendance(
    month: int = Query(default=None, ge=1, le=12),
    year: int = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    today = date.today()
    month = month or today.month
    year = year or today.year
    rows = db.query(models.Attendance).filter(
        models.Attendance.user_id == current_user.id,
        models.Attendance.work_date >= date(year, month, 1),
        models.Attendance.work_date < (date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)),
    ).order_by(models.Attendance.work_date).all()

    return [_to_row(r) for r in rows]


@router.get("/all", response_model=list[schemas.AttendanceRow])
def all_attendance_today(
    work_date: date = Query(default=None),
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Admin/HR view: everyone's attendance for a given day (defaults to today)."""
    target = work_date or date.today()
    rows = (
        db.query(models.Attendance)
        .join(models.User, models.User.id == models.Attendance.user_id)
        .filter(models.User.company_id == admin.company_id, models.Attendance.work_date == target)
        .all()
    )
    out = []
    for r in rows:
        row = _to_row(r)
        row.employee_name = r.user_id and _employee_name(db, r.user_id)
        out.append(row)
    return out


def _employee_name(db, user_id):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    return u.full_name if u else None


def _to_row(r: models.Attendance) -> schemas.AttendanceRow:
    return schemas.AttendanceRow(
        work_date=r.work_date,
        check_in=r.check_in,
        check_out=r.check_out,
        status=r.status.value,
        work_hours=float(r.work_hours or 0),
        extra_hours=float(r.extra_hours or 0),
    )
