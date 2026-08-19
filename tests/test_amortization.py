import pytest

from findcalc.amortization import (
    amortization_schedule,
    fixed_payment_schedule,
    future_value_of_series,
    future_value_of_variable_series,
    monthly_payment,
    remaining_balance_at,
)


def test_monthly_payment_zero_interest_is_even_split():
    assert monthly_payment(12000, 0.0, 12) == 1000.0


def test_monthly_payment_matches_known_example():
    # $20,000 loan, 6% APR, 60 months -> standard textbook value ~ $386.66
    payment = monthly_payment(20000, 0.06, 60)
    assert round(payment, 2) == 386.66


def test_schedule_pays_off_exactly_to_zero():
    schedule = amortization_schedule(20000, 0.06, 60)
    assert schedule[-1].balance == 0.0
    assert len(schedule) == 60


def test_schedule_total_principal_equals_original_balance():
    schedule = amortization_schedule(15000, 0.05, 36)
    total_principal = round(sum(row.principal_paid for row in schedule), 2)
    # Rounding each row to the cent (like a real statement would) can leave
    # a couple of cents of drift over a long schedule.
    assert abs(total_principal - 15000.0) < 0.05


def test_extra_payment_shortens_schedule():
    baseline = amortization_schedule(15000, 0.05, 36)
    accelerated = amortization_schedule(15000, 0.05, 36, extra_payment=200)
    assert len(accelerated) < len(baseline)


def test_extra_payment_reduces_total_interest():
    baseline = amortization_schedule(15000, 0.05, 36)
    accelerated = amortization_schedule(15000, 0.05, 36, extra_payment=200)
    baseline_interest = sum(row.interest_paid for row in baseline)
    accelerated_interest = sum(row.interest_paid for row in accelerated)
    assert accelerated_interest < baseline_interest


def test_remaining_balance_at_start_is_principal():
    assert remaining_balance_at(10000, 0.04, 24, 0) == 10000.0


def test_remaining_balance_at_end_is_zero():
    assert remaining_balance_at(10000, 0.04, 24, 24) == 0.0


def test_remaining_balance_matches_schedule():
    schedule = amortization_schedule(10000, 0.04, 24)
    assert remaining_balance_at(10000, 0.04, 24, 12) == schedule[11].balance


def test_future_value_of_series_zero_rate_is_simple_sum():
    assert future_value_of_series(100, 0.0, 12) == 1200.0


def test_future_value_of_series_grows_with_rate():
    no_growth = future_value_of_series(100, 0.0, 60)
    with_growth = future_value_of_series(100, 0.07, 60)
    assert with_growth > no_growth


def test_future_value_of_series_zero_months_is_zero():
    assert future_value_of_series(100, 0.05, 0) == 0.0


def test_fixed_payment_schedule_pays_off_balance():
    schedule = fixed_payment_schedule(5000, 0.18, 200)
    assert schedule[-1].balance == 0.0


def test_fixed_payment_schedule_rejects_payment_below_interest():
    with pytest.raises(ValueError):
        fixed_payment_schedule(5000, 0.24, 90)  # monthly interest is $100


def test_fixed_payment_schedule_higher_payment_pays_off_faster():
    slow = fixed_payment_schedule(5000, 0.18, 150)
    fast = fixed_payment_schedule(5000, 0.18, 300)
    assert len(fast) < len(slow)


def test_future_value_of_variable_series_matches_constant_case():
    amounts = [100] * 24
    assert round(future_value_of_variable_series(amounts, 0.06), 2) == round(
        future_value_of_series(100, 0.06, 24), 2
    )


def test_future_value_of_variable_series_handles_ramp_up():
    amounts = [0, 0, 0, 500, 500, 500]
    fv = future_value_of_variable_series(amounts, 0.06)
    assert fv > 1500  # more than the raw sum, thanks to compounding
