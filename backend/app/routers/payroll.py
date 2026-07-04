from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, require_admin
from app.utils.salary_calc import compute_payroll

router = APIRouter(prefix="/api/payroll", tags=["payroll"])


@router.get("/me", response_model=schemas.PayrollOut)
def my_payroll(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Read-only for employees, per spec: 'Payroll data is read-only for employees.'"""
    salary = current_user.salary
    if not salary:
        raise HTTPException(status_code=404, detail="Salary structure has not been set up yet.")
    return schemas.PayrollOut(**compute_payroll(salary))


@router.get("/{employee_id}", response_model=schemas.PayrollOut)
def get_employee_payroll(
    employee_id: int, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)
):
    user = db.query(models.User).filter(
        models.User.id == employee_id, models.User.company_id == admin.company_id
    ).first()
    if not user or not user.salary:
        raise HTTPException(status_code=404, detail="Employee or salary structure not found.")
    return schemas.PayrollOut(**compute_payroll(user.salary))


@router.put("/{employee_id}", response_model=schemas.PayrollOut)
def update_employee_payroll(
    employee_id: int,
    payload: schemas.SalaryStructureUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Admin defines the wage and component percentages; amounts are then
    always derived automatically -- never entered as raw numbers -- so the
    'components should not exceed wage' rule holds by construction."""
    user = db.query(models.User).filter(
        models.User.id == employee_id, models.User.company_id == admin.company_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found.")

    total_pct = payload.basic_pct + (payload.basic_pct * payload.hra_pct_of_basic / 100) \
        + payload.standard_allowance_pct + payload.performance_bonus_pct + payload.lta_pct
    if total_pct > 100:
        raise HTTPException(
            status_code=400,
            detail="Basic + HRA + Standard Allowance + Performance Bonus + LTA exceed 100% of wage. "
                   "Reduce one of the percentages so Fixed Allowance can cover the remainder.",
        )

    salary = user.salary or models.SalaryStructure(user_id=user.id)
    for field, value in payload.model_dump().items():
        setattr(salary, field, value)
    db.add(salary)
    db.commit()
    db.refresh(salary)
    return schemas.PayrollOut(**compute_payroll(salary))
