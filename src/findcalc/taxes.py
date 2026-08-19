"""Federal, FICA, and state tax math for a single filer's W-2 salary.

This is deliberately simple: one filing status (single), no itemizing, no
credits, no dependents. It's meant to make an apples-to-apples comparison
across locations, not to replace an actual tax return.
"""

from __future__ import annotations

from dataclasses import dataclass

from findcalc.data.federal_tax import (
    ADDITIONAL_MEDICARE_RATE,
    ADDITIONAL_MEDICARE_THRESHOLD_SINGLE,
    FEDERAL_BRACKETS_SINGLE,
    MEDICARE_RATE,
    SOCIAL_SECURITY_RATE,
    SOCIAL_SECURITY_WAGE_BASE_2025,
    STANDARD_DEDUCTION_SINGLE_2025,
)
from findcalc.data.state_tax import StateTaxModel, get_state_tax_model


def _progressive_tax(taxable_income: float, brackets: list[tuple[float, float]]) -> float:
    """Standard marginal-bracket tax: each rate only applies to the slice of
    income that falls inside that bracket, not the whole amount."""
    if taxable_income <= 0:
        return 0.0

    tax = 0.0
    for i, (floor, rate) in enumerate(brackets):
        next_floor = brackets[i + 1][0] if i + 1 < len(brackets) else None
        if taxable_income <= floor:
            break
        ceiling = min(taxable_income, next_floor) if next_floor is not None else taxable_income
        tax += (ceiling - floor) * rate
    return round(tax, 2)


def compute_federal_tax(gross_salary: float) -> float:
    taxable_income = max(gross_salary - STANDARD_DEDUCTION_SINGLE_2025, 0.0)
    return _progressive_tax(taxable_income, FEDERAL_BRACKETS_SINGLE)


def compute_fica(gross_salary: float) -> float:
    ss_taxable = min(gross_salary, SOCIAL_SECURITY_WAGE_BASE_2025)
    social_security = ss_taxable * SOCIAL_SECURITY_RATE

    medicare = gross_salary * MEDICARE_RATE
    if gross_salary > ADDITIONAL_MEDICARE_THRESHOLD_SINGLE:
        medicare += (gross_salary - ADDITIONAL_MEDICARE_THRESHOLD_SINGLE) * ADDITIONAL_MEDICARE_RATE

    return round(social_security + medicare, 2)


def compute_state_tax(gross_salary: float, state: str) -> float:
    model = get_state_tax_model(state)
    taxable_income = max(gross_salary - STANDARD_DEDUCTION_SINGLE_2025, 0.0)

    if model.kind == "none":
        return 0.0
    if model.kind == "flat":
        return round(taxable_income * model.flat_rate, 2)
    if model.kind == "graduated_2tier":
        return round(
            _progressive_tax(
                taxable_income, [(0, model.low_rate), (model.top_threshold, model.top_rate)]
            ),
            2,
        )
    raise ValueError(f"Unknown state tax model kind: {model.kind!r}")


@dataclass
class TakeHomeBreakdown:
    gross_salary: float
    federal_tax: float
    state_tax: float
    fica: float
    total_tax: float
    net_annual: float
    net_monthly: float
    effective_tax_rate: float


def compute_take_home(gross_salary: float, state: str) -> TakeHomeBreakdown:
    federal_tax = compute_federal_tax(gross_salary)
    state_tax = compute_state_tax(gross_salary, state)
    fica = compute_fica(gross_salary)
    total_tax = round(federal_tax + state_tax + fica, 2)
    net_annual = round(gross_salary - total_tax, 2)

    return TakeHomeBreakdown(
        gross_salary=gross_salary,
        federal_tax=federal_tax,
        state_tax=state_tax,
        fica=fica,
        total_tax=total_tax,
        net_annual=net_annual,
        net_monthly=round(net_annual / 12, 2),
        effective_tax_rate=round(total_tax / gross_salary, 4) if gross_salary else 0.0,
    )
