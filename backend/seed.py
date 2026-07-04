"""
Populate the database with one demo company, one admin, and three employees
so you have something to click through immediately.

Usage:
    cd backend
    python seed.py
"""
from datetime import date

from app.database import SessionLocal, Base, engine
from app import models
from app.security import hash_password
from app.utils.id_generator import make_company_code, generate_login_id

Base.metadata.create_all(bind=engine)
db = SessionLocal()

COMPANY_NAME = "Odoo India"

def get_or_create_company():
    company = db.query(models.Company).filter(models.Company.name == COMPANY_NAME).first()
    if not company:
        company = models.Company(name=COMPANY_NAME, code=make_company_code(COMPANY_NAME))
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


def create_user(company, first, last, email, role, wage, password="Passw0rd!"):
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        print(f"  - {email} already exists, skipping")
        return existing

    login_id = generate_login_id(db, company.code, first, last, date.today().year)
    user = models.User(
        login_id=login_id, company_id=company.id, first_name=first, last_name=last,
        email=email, phone="9000000000", password_hash=hash_password(password),
        role=models.UserRole(role), is_email_verified=True, date_of_joining=date.today(),
    )
    db.add(user)
    db.flush()
    db.add(models.EmployeeProfile(
        user_id=user.id, job_position="HR Manager" if role == "admin" else "Software Engineer",
        department="Human Resources" if role == "admin" else "Engineering",
        location="Kolkata, IN",
    ))
    db.add(models.SalaryStructure(user_id=user.id, monthly_wage=wage))
    for lt, total in ((models.LeaveType.paid, 24), (models.LeaveType.sick, 7), (models.LeaveType.unpaid, 0)):
        db.add(models.LeaveBalance(user_id=user.id, leave_type=lt, total_days=total))
    db.commit()
    print(f"  - created {login_id} / {email} / password: {password}")
    return user


if __name__ == "__main__":
    print("Seeding demo data...")
    company = get_or_create_company()
    create_user(company, "Priya", "Sharma", "priya.admin@example.com", "admin", 80000)
    create_user(company, "John", "Doe", "john.doe@example.com", "employee", 50000)
    create_user(company, "Anita", "Roy", "anita.roy@example.com", "employee", 45000)
    create_user(company, "Rahul", "Verma", "rahul.verma@example.com", "employee", 60000)
    print("Done. Log in with any email above and password 'Passw0rd!'.")
