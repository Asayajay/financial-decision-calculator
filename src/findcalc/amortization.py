"""Loan amortization math shared by the lease-vs-buy and debt-vs-invest calculators."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AmortizationRow:
    month: int
    payment: float
    principal_paid: float
    interest_paid: float
    balance: float


def monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    """Standard fixed-payment loan formula.

    annual_rate is the nominal annual rate (e.g. 0.06 for 6%), compounded monthly.
    """
    if term_months <= 0:
        raise ValueError("term_months must be positive")
    if principal <= 0:
        return 0.0
    if annual_rate == 0:
        return principal / term_months

    r = annual_rate / 12
    return principal * (r * (1 + r) ** term_months) / ((1 + r) ** term_months - 1)


def amortization_schedule(
    principal: float,
    annual_rate: float,
    term_months: int,
    extra_payment: float = 0.0,
) -> list[AmortizationRow]:
    """Full month-by-month schedule.

    extra_payment is applied on top of the standard payment, straight to
    principal, each month, which is how "extra payment" almost always works
    in practice (no lender recalculates your required payment because you
    paid ahead). The schedule ends early if the balance reaches zero before
    term_months.
    """
    if principal <= 0:
        return []

    base_payment = monthly_payment(principal, annual_rate, term_months)
    r = annual_rate / 12
    balance = principal
    rows: list[AmortizationRow] = []
    month = 0

    while balance > 0.01 and month < term_months * 4:
        month += 1
        interest = balance * r
        principal_due = base_payment - interest
        payment_this_month = base_payment + extra_payment

        if principal_due + extra_payment >= balance:
            # Final payment: only pay off what's left.
            principal_paid = balance
            payment_this_month = principal_paid + interest
            balance = 0.0
        else:
            principal_paid = principal_due + extra_payment
            balance -= principal_paid

        rows.append(
            AmortizationRow(
                month=month,
                payment=round(payment_this_month, 2),
                principal_paid=round(principal_paid, 2),
                interest_paid=round(interest, 2),
                balance=round(max(balance, 0.0), 2),
            )
        )

    return rows


def remaining_balance_at(
    principal: float, annual_rate: float, term_months: int, month: int
) -> float:
    """Loan balance after `month` scheduled payments (no extra payments)."""
    schedule = amortization_schedule(principal, annual_rate, term_months)
    if month <= 0:
        return round(principal, 2)
    if month >= len(schedule):
        return 0.0
    return schedule[month - 1].balance


def future_value_of_series(monthly_amount: float, annual_rate: float, months: int) -> float:
    """Future value of investing a fixed amount every month, compounded monthly.

    Uses the standard ordinary-annuity future value formula. A zero or
    negative monthly_amount just runs the sum through with no growth applied
    incorrectly (handled via the closed-form formula either way).
    """
    if months <= 0:
        return 0.0
    r = annual_rate / 12
    if r == 0:
        return monthly_amount * months
    return monthly_amount * (((1 + r) ** months - 1) / r)
