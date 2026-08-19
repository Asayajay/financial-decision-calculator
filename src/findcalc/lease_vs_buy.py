"""Lease-vs-buy car calculator.

Compares the total cost of financing and eventually owning a car against
leasing one, over a chosen ownership horizon. Every number in the result
traces back to a specific input, so nothing here is a black-box
recommendation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from findcalc.amortization import amortization_schedule, monthly_payment


@dataclass
class BuyInputs:
    vehicle_price: float
    down_payment: float
    loan_apr: float
    loan_term_months: int
    sales_tax_rate: float = 0.0
    annual_insurance: float = 0.0
    annual_maintenance: float = 0.0
    annual_registration_fee: float = 0.0
    annual_depreciation_rate: float = 0.15


@dataclass
class LeaseInputs:
    due_at_signing: float
    monthly_payment: float
    lease_term_months: int
    disposition_fee: float = 0.0
    mileage_overage_fee: float = 0.0
    annual_insurance: float = 0.0
    annual_maintenance: float = 0.0
    annual_registration_fee: float = 0.0


@dataclass
class BuyResult:
    amount_financed: float
    sales_tax_paid: float
    monthly_loan_payment: float
    total_loan_payments_through_horizon: float
    total_interest_through_horizon: float
    loan_balance_at_horizon: float
    estimated_resale_value_at_horizon: float
    net_equity_at_horizon: float
    total_insurance: float
    total_maintenance: float
    total_registration: float
    total_cash_outflow: float
    net_cost: float


@dataclass
class LeaseResult:
    num_lease_signings: int
    total_signing_fees: float
    total_monthly_payments: float
    total_disposition_fees: float
    total_mileage_overage_fees: float
    total_insurance: float
    total_maintenance: float
    total_registration: float
    total_cash_outflow: float
    net_cost: float


@dataclass
class LeaseVsBuyComparison:
    horizon_months: int
    buy: BuyResult
    lease: LeaseResult
    cheaper_option: str
    savings: float


def _require_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value!r}")


def _require_non_negative(value: float, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} must not be negative, got {value!r}")


def compute_buy(inputs: BuyInputs, horizon_months: int) -> BuyResult:
    _require_positive(inputs.vehicle_price, "vehicle_price")
    _require_non_negative(inputs.down_payment, "down_payment")
    _require_non_negative(inputs.loan_apr, "loan_apr")
    _require_positive(inputs.loan_term_months, "loan_term_months")
    _require_non_negative(inputs.sales_tax_rate, "sales_tax_rate")
    if not 0 <= inputs.annual_depreciation_rate < 1:
        raise ValueError("annual_depreciation_rate must be in [0, 1)")
    _require_positive(horizon_months, "horizon_months")

    sales_tax_paid = round(inputs.vehicle_price * inputs.sales_tax_rate, 2)
    amount_financed = max(
        inputs.vehicle_price + sales_tax_paid - inputs.down_payment, 0.0
    )

    schedule = amortization_schedule(
        amount_financed, inputs.loan_apr, inputs.loan_term_months
    )
    payment = monthly_payment(amount_financed, inputs.loan_apr, inputs.loan_term_months)

    months_paid = min(horizon_months, len(schedule))
    rows_through_horizon = schedule[:months_paid]
    total_loan_payments = round(sum(r.payment for r in rows_through_horizon), 2)
    total_interest = round(sum(r.interest_paid for r in rows_through_horizon), 2)
    loan_balance_at_horizon = (
        rows_through_horizon[-1].balance if rows_through_horizon else amount_financed
    )
    if horizon_months >= len(schedule):
        loan_balance_at_horizon = 0.0

    years_held = horizon_months / 12
    estimated_resale_value = round(
        inputs.vehicle_price * (1 - inputs.annual_depreciation_rate) ** years_held, 2
    )
    net_equity = round(estimated_resale_value - loan_balance_at_horizon, 2)

    total_insurance = round(inputs.annual_insurance * years_held, 2)
    total_maintenance = round(inputs.annual_maintenance * years_held, 2)
    total_registration = round(inputs.annual_registration_fee * years_held, 2)

    total_cash_outflow = round(
        inputs.down_payment
        + total_loan_payments
        + total_insurance
        + total_maintenance
        + total_registration,
        2,
    )
    net_cost = round(total_cash_outflow - net_equity, 2)

    return BuyResult(
        amount_financed=round(amount_financed, 2),
        sales_tax_paid=sales_tax_paid,
        monthly_loan_payment=round(payment, 2),
        total_loan_payments_through_horizon=total_loan_payments,
        total_interest_through_horizon=total_interest,
        loan_balance_at_horizon=round(loan_balance_at_horizon, 2),
        estimated_resale_value_at_horizon=estimated_resale_value,
        net_equity_at_horizon=net_equity,
        total_insurance=total_insurance,
        total_maintenance=total_maintenance,
        total_registration=total_registration,
        total_cash_outflow=total_cash_outflow,
        net_cost=net_cost,
    )


def compute_lease(inputs: LeaseInputs, horizon_months: int) -> LeaseResult:
    if inputs.lease_term_months <= 0:
        raise ValueError("lease_term_months must be positive")
    _require_non_negative(inputs.due_at_signing, "due_at_signing")
    _require_non_negative(inputs.monthly_payment, "monthly_payment")
    _require_non_negative(inputs.disposition_fee, "disposition_fee")
    _require_positive(horizon_months, "horizon_months")

    num_signings = math.ceil(horizon_months / inputs.lease_term_months)
    full_terms = horizon_months // inputs.lease_term_months
    remainder_months = horizon_months - full_terms * inputs.lease_term_months

    months_billed = full_terms * inputs.lease_term_months + remainder_months
    total_monthly_payments = round(inputs.monthly_payment * months_billed, 2)
    total_signing_fees = round(inputs.due_at_signing * num_signings, 2)

    # A disposition fee is charged at the end of each completed lease term;
    # a lease still in progress at the horizon doesn't trigger one yet.
    completed_terms = full_terms
    total_disposition_fees = round(inputs.disposition_fee * completed_terms, 2)
    total_mileage_overage_fees = round(inputs.mileage_overage_fee * num_signings, 2)

    years_held = horizon_months / 12
    total_insurance = round(inputs.annual_insurance * years_held, 2)
    total_maintenance = round(inputs.annual_maintenance * years_held, 2)
    total_registration = round(inputs.annual_registration_fee * years_held, 2)

    total_cash_outflow = round(
        total_signing_fees
        + total_monthly_payments
        + total_disposition_fees
        + total_mileage_overage_fees
        + total_insurance
        + total_maintenance
        + total_registration,
        2,
    )

    return LeaseResult(
        num_lease_signings=num_signings,
        total_signing_fees=total_signing_fees,
        total_monthly_payments=total_monthly_payments,
        total_disposition_fees=total_disposition_fees,
        total_mileage_overage_fees=total_mileage_overage_fees,
        total_insurance=total_insurance,
        total_maintenance=total_maintenance,
        total_registration=total_registration,
        total_cash_outflow=total_cash_outflow,
        net_cost=total_cash_outflow,
    )


def compare(
    buy_inputs: BuyInputs, lease_inputs: LeaseInputs, horizon_months: int
) -> LeaseVsBuyComparison:
    buy_result = compute_buy(buy_inputs, horizon_months)
    lease_result = compute_lease(lease_inputs, horizon_months)

    diff = round(buy_result.net_cost - lease_result.net_cost, 2)
    if diff > 0:
        cheaper = "lease"
    elif diff < 0:
        cheaper = "buy"
    else:
        cheaper = "tie"

    return LeaseVsBuyComparison(
        horizon_months=horizon_months,
        buy=buy_result,
        lease=lease_result,
        cheaper_option=cheaper,
        savings=abs(diff),
    )
