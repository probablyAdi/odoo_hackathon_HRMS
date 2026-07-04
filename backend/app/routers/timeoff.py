from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, require_admin

router = APIRouter(prefix="/api/timeoff", tags=["timeoff"])


def _business_days(start, end) -> float:
    """Inclusive day count between two dates. Kept simple (calendar days,
    not excluding weekends) to match the wireframe's plain date-range picker;
    swap in a working-calendar lookup here if weekends should be excluded."""
    return (end - start).days + 1


@router.get("/balances", response_model=list[schemas.LeaveBalanceOut])
def my_balances(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    rows = db.query(models.LeaveBalance).filter(models.LeaveBalance.user_id == current_user.id).all()
    return [
        schemas.LeaveBalanceOut(
            leave_type=r.leave_type.value,
            total_days=float(r.total_days),
            used_days=float(r.used_days),
            available_days=float(r.total_days) - float(r.used_days),
        )
        for r in rows
    ]


@router.post("/apply", response_model=schemas.LeaveOut, status_code=201)
def apply_leave(
    payload: schemas.LeaveApply,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    days = _business_days(payload.start_date, payload.end_date)

    if payload.leave_type != "unpaid":
        balance = db.query(models.LeaveBalance).filter(
            models.LeaveBalance.user_id == current_user.id,
            models.LeaveBalance.leave_type == models.LeaveType(payload.leave_type),
        ).first()
        available = float(balance.total_days) - float(balance.used_days) if balance else 0
        if days > available:
            raise HTTPException(
                status_code=400,
                detail=f"You only have {available:g} day(s) of {payload.leave_type} leave available.",
            )

    overlap = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.user_id == current_user.id,
        models.LeaveRequest.status != models.LeaveStatus.rejected,
        models.LeaveRequest.start_date <= payload.end_date,
        models.LeaveRequest.end_date >= payload.start_date,
    ).first()
    if overlap:
        raise HTTPException(status_code=400, detail="You already have a leave request overlapping these dates.")

    request = models.LeaveRequest(
        user_id=current_user.id,
        leave_type=models.LeaveType(payload.leave_type),
        start_date=payload.start_date,
        end_date=payload.end_date,
        days_count=days,
        remarks=payload.remarks,
        attachment_url=payload.attachment_url,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return _to_out(request, current_user.full_name)


@router.get("/me", response_model=list[schemas.LeaveOut])
def my_leave_requests(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    rows = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.user_id == current_user.id
    ).order_by(models.LeaveRequest.created_at.desc()).all()
    return [_to_out(r, current_user.full_name) for r in rows]


@router.get("/all", response_model=list[schemas.LeaveOut])
def all_leave_requests(
    status_filter: str = None,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    q = (
        db.query(models.LeaveRequest)
        .join(models.User, models.User.id == models.LeaveRequest.user_id)
        .filter(models.User.company_id == admin.company_id)
    )
    if status_filter:
        q = q.filter(models.LeaveRequest.status == models.LeaveStatus(status_filter))
    rows = q.order_by(models.LeaveRequest.created_at.desc()).all()

    out = []
    for r in rows:
        name = db.query(models.User).filter(models.User.id == r.user_id).first().full_name
        out.append(_to_out(r, name))
    return out


@router.post("/{request_id}/decide", response_model=schemas.LeaveOut)
def decide_leave(
    request_id: int,
    payload: schemas.LeaveDecision,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    req = db.query(models.LeaveRequest).filter(models.LeaveRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found.")
    if req.status != models.LeaveStatus.pending:
        raise HTTPException(status_code=400, detail="This request has already been decided.")

    req.status = models.LeaveStatus(payload.decision)
    req.admin_comment = payload.admin_comment
    req.decided_by = admin.id
    req.decided_at = datetime.utcnow()

    if payload.decision == "approved" and req.leave_type != models.LeaveType.unpaid:
        balance = db.query(models.LeaveBalance).filter(
            models.LeaveBalance.user_id == req.user_id, models.LeaveBalance.leave_type == req.leave_type
        ).first()
        if balance:
            balance.used_days = float(balance.used_days) + float(req.days_count)

    db.commit()
    db.refresh(req)
    name = db.query(models.User).filter(models.User.id == req.user_id).first().full_name
    return _to_out(req, name)


def _to_out(r: models.LeaveRequest, name: str) -> schemas.LeaveOut:
    return schemas.LeaveOut(
        id=r.id,
        employee_name=name,
        leave_type=r.leave_type.value,
        start_date=r.start_date,
        end_date=r.end_date,
        days_count=float(r.days_count),
        remarks=r.remarks,
        status=r.status.value,
        admin_comment=r.admin_comment,
    )
