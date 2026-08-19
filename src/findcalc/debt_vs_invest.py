"""Debt-payoff-vs-invest calculator.

The classic question: if you have extra cash each month, should it go
toward paying off a debt faster, or into an investment account? The honest
answer is "it depends on the interest rate versus the expected return," so
this module runs both schedules month by month and shows the actual
crossover instead of a rule of thumb.
"""

from __future__ import annotations

from dataclasses import dataclass

from findcalc.amortization import fixed_payment_schedule, future_value_of_variable_series


@dataclass
class DebtVsInvestInputs:
    debt_balance: float
    debt_apr: float
    minimum_payment: float
    extra_amount: float
    expected_annual_return: float


@dataclass
class ScenarioResult:
    name: str
    debt_payoff_month: int
    total_interest_paid: float
    investment_contributions: list[float]
    investment_value_at_horizon: float
    remaining_debt_at_horizon: float
    net_worth_at_horizon: float


@dataclass
class DebtVsInvestComparison:
    horizon_months: int
    pay_off_debt_first: ScenarioResult
    invest_now: ScenarioResult
    better_option: str
    net_worth_difference: float
    breakeven_return_rate: float


def _scenario(
    name: str,
    debt_balance: float,
    debt_apr: float,
    debt_payment: float,
    invest_before_payoff: float,
    invest_after_payoff: float,
    expected_annual_return: float,
    horizon_months: int,
) -> ScenarioResult:
    schedule = fixed_payment_schedule(debt_balance, debt_apr, debt_payment)
    payoff_month = len(schedule)
    total_interest = round(sum(row.interest_paid for row in schedule), 2)

    remaining_debt_at_horizon = 0.0
    if payoff_month > horizon_months:
        remaining_debt_at_horizon = schedule[horizon_months - 1].balance if horizon_months > 0 else debt_balance

    contributions = []
    for month in range(1, horizon_months + 1):
        if month <= payoff_month:
            contributions.append(invest_before_payoff)
        else:
            contributions.append(invest_after_payoff)

    investment_value = round(
        future_value_of_variable_series(contributions, expected_annual_return), 2
    )
    net_worth = round(investment_value - remaining_debt_at_horizon, 2)

    return ScenarioResult(
        name=name,
        debt_payoff_month=payoff_month,
        total_interest_paid=total_interest,
        investment_contributions=contributions,
        investment_value_at_horizon=investment_value,
        remaining_debt_at_horizon=round(remaining_debt_at_horizon, 2),
        net_worth_at_horizon=net_worth,
    )


def compare(inputs: DebtVsInvestInputs, horizon_months: int) -> DebtVsInvestComparison:
    """Compare throwing extra cash at the debt versus investing it instead.

    Both scenarios commit the same total dollars each month
    (minimum_payment + extra_amount); the only difference is where the
    extra_amount goes until the debt is paid off. Once a scenario's debt is
    paid off, the cash that used to service it starts getting invested too,
    so the two schedules stay directly comparable.
    """
    if inputs.debt_balance <= 0:
        raise ValueError("debt_balance must be positive")
    if inputs.debt_apr < 0:
        raise ValueError("debt_apr must not be negative")
    if inputs.minimum_payment <= 0:
        raise ValueError("minimum_payment must be positive")
    if inputs.extra_amount < 0:
        raise ValueError("extra_amount must not be negative")
    if inputs.expected_annual_return < -1:
        raise ValueError("expected_annual_return can't be below -100%")
    if horizon_months <= 0:
        raise ValueError("horizon_months must be positive")

    pay_off_first = _scenario(
        name="pay_off_debt_first",
        debt_balance=inputs.debt_balance,
        debt_apr=inputs.debt_apr,
        debt_payment=inputs.minimum_payment + inputs.extra_amount,
        invest_before_payoff=0.0,
        invest_after_payoff=inputs.minimum_payment + inputs.extra_amount,
        expected_annual_return=inputs.expected_annual_return,
        horizon_months=horizon_months,
    )

    invest_now = _scenario(
        name="invest_now",
        debt_balance=inputs.debt_balance,
        debt_apr=inputs.debt_apr,
        debt_payment=inputs.minimum_payment,
        invest_before_payoff=inputs.extra_amount,
        invest_after_payoff=inputs.minimum_payment + inputs.extra_amount,
        expected_annual_return=inputs.expected_annual_return,
        horizon_months=horizon_months,
    )

    diff = round(invest_now.net_worth_at_horizon - pay_off_first.net_worth_at_horizon, 2)
    if diff > 0:
        better = "invest_now"
    elif diff < 0:
        better = "pay_off_debt_first"
    else:
        better = "tie"

    return DebtVsInvestComparison(
        horizon_months=horizon_months,
        pay_off_debt_first=pay_off_first,
        invest_now=invest_now,
        better_option=better,
        net_worth_difference=abs(diff),
        breakeven_return_rate=inputs.debt_apr,
    )


@dataclass
class SensitivityRow:
    expected_annual_return: float
    better_option: str
    net_worth_difference: float


def sensitivity_by_return(
    inputs: DebtVsInvestInputs, horizon_months: int, return_rates: list[float]
) -> list[SensitivityRow]:
    """Re-run the comparison across a range of expected returns.

    The debt APR is fixed by the debt itself; the expected investment
    return is the genuinely uncertain input in this whole calculator. This
    shows how sensitive the verdict is to that guess, instead of hiding it
    behind a single point estimate.
    """
    rows = []
    for rate in return_rates:
        scenario_inputs = DebtVsInvestInputs(
            debt_balance=inputs.debt_balance,
            debt_apr=inputs.debt_apr,
            minimum_payment=inputs.minimum_payment,
            extra_amount=inputs.extra_amount,
            expected_annual_return=rate,
        )
        result = compare(scenario_inputs, horizon_months)
        rows.append(
            SensitivityRow(
                expected_annual_return=rate,
                better_option=result.better_option,
                net_worth_difference=result.net_worth_difference,
            )
        )
    return rows
