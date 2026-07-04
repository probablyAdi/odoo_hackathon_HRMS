"""
Login ID format required by the spec:

    [Company Code (2 letters)] [First 2 letters of first name][First 2 letters
    of last name] [Year of joining] [4-digit serial number for that year]

Example: OIJODO20260001
    OI    -> Odoo India (company code)
    JO    -> first two letters of first name "John"
    DO    -> first two letters of last name "Doe"
    2026  -> year of joining
    0001  -> 1st person hired in 2026 at this company
"""
import re
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models


def make_company_code(company_name: str) -> str:
    """Derive a 2-letter code from a company name: initials of the first
    two words, or the first two letters if it's a single word."""
    words = re.findall(r"[A-Za-z]+", company_name)
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    if words:
        return words[0][:2].upper().ljust(2, "X")
    return "CO"


def generate_login_id(db: Session, company_code: str, first_name: str,
                       last_name: str, year: int) -> str:
    first_part = re.sub(r"[^A-Za-z]", "", first_name)[:2].upper().ljust(2, "X")
    last_part = re.sub(r"[^A-Za-z]", "", last_name)[:2].upper().ljust(2, "X")
    prefix = f"{company_code}{first_part}{last_part}{year}"

    # Find how many login_ids already start with this exact prefix this year,
    # to pick the next serial number. Serial is global-per-company-per-year,
    # not per name, matching "serial number of joining for that year".
    year_prefix = f"{company_code}%{year}"
    count = (
        db.query(func.count(models.User.id))
        .filter(models.User.login_id.like(f"{company_code}%{year}%"))
        .scalar()
    )
    serial = (count or 0) + 1
    login_id = f"{prefix}{serial:04d}"

    # Guard against an unlikely collision (e.g. serial reused after a delete)
    while db.query(models.User).filter(models.User.login_id == login_id).first():
        serial += 1
        login_id = f"{prefix}{serial:04d}"

    return login_id
