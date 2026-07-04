"""
Salary component computation, mirroring the wireframe's "Salary Info" tab.

Rule (from the design notes):
  Basic               = basic_pct% of monthly wage
  HRA                 = hra_pct_of_basic% of Basic
  Standard Allowance  = standard_allowance_pct% of monthly wage
  Performance Bonus   = performance_bonus_pct% of monthly wage
  Leave Travel Allow. = lta_pct% of monthly wage
  Fixed Allowance     = wage - sum(all the above components)   <- balancing figure

  PF (employee/employer) = pct% of Basic (not of gross wage)
  Professional Tax       = flat amount, deducted from gross

The total of all salary components must never exceed the defined wage --
Fixed Allowance is deliberately the remainder so this always holds.
"""
from app import models


def compute_payroll(salary: models.SalaryStructure) -> dict:
    wage = float(salary.monthly_wage or 0)

    basic = round(wage * float(salary.basic_pct) / 100, 2)
    hra = round(basic * float(salary.hra_pct_of_basic) / 100, 2)
    standard_allowance = round(wage * float(salary.standard_allowance_pct) / 100, 2)
    performance_bonus = round(wage * float(salary.performance_bonus_pct) / 100, 2)
    lta = round(wage * float(salary.lta_pct) / 100, 2)

    running_total = basic + hra + standard_allowance + performance_bonus + lta
    fixed_allowance = round(max(wage - running_total, 0), 2)

    def pct_of_wage(amount):
        return round((amount / wage) * 100, 2) if wage else 0.0

    components = [
        {"name": "Basic Salary", "amount": basic, "percent_of_wage": pct_of_wage(basic),
         "description": "Base pay computed on the monthly wage."},
        {"name": "House Rent Allowance", "amount": hra, "percent_of_wage": pct_of_wage(hra),
         "description": f"{float(salary.hra_pct_of_basic):.2f}% of Basic Salary."},
        {"name": "Standard Allowance", "amount": standard_allowance,
         "percent_of_wage": pct_of_wage(standard_allowance),
         "description": "Fixed portion of wage provided as a standard allowance."},
        {"name": "Performance Bonus", "amount": performance_bonus,
         "percent_of_wage": pct_of_wage(performance_bonus),
         "description": "Variable pay based on a % of Basic Salary."},
        {"name": "Leave Travel Allowance", "amount": lta, "percent_of_wage": pct_of_wage(lta),
         "description": "Covers employee travel expenses."},
        {"name": "Fixed Allowance", "amount": fixed_allowance,
         "percent_of_wage": pct_of_wage(fixed_allowance),
         "description": "Remainder of wage after all other components."},
    ]

    pf_employee = round(basic * float(salary.pf_employee_pct) / 100, 2)
    pf_employer = round(basic * float(salary.pf_employer_pct) / 100, 2)
    professional_tax = float(salary.professional_tax or 0)

    net_pay = round(wage - pf_employee - professional_tax, 2)

    return {
        "monthly_wage": wage,
        "yearly_wage": round(wage * 12, 2),
        "working_days_per_week": salary.working_days_per_week,
        "break_time_hours": float(salary.break_time_hours or 0),
        "components": components,
        "pf_employee": pf_employee,
        "pf_employer": pf_employer,
        "professional_tax": professional_tax,
        "net_pay": net_pay,
        "basic_pct": float(salary.basic_pct),
        "hra_pct_of_basic": float(salary.hra_pct_of_basic),
        "standard_allowance_pct": float(salary.standard_allowance_pct),
        "performance_bonus_pct": float(salary.performance_bonus_pct),
        "lta_pct": float(salary.lta_pct),
        "pf_employee_pct": float(salary.pf_employee_pct),
        "pf_employer_pct": float(salary.pf_employer_pct),
    }
