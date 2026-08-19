import pytest

from findcalc.debt_vs_invest import DebtVsInvestInputs, compare


def make_inputs(**overrides):
    defaults = dict(
        debt_balance=8000,
        debt_apr=0.22,
        minimum_payment=200,
        extra_amount=150,
        expected_annual_return=0.07,
    )
    defaults.update(overrides)
    return DebtVsInvestInputs(**defaults)


def test_paying_off_debt_first_finishes_faster_than_minimum_only():
    result = compare(make_inputs(), horizon_months=60)
    assert result.pay_off_debt_first.debt_payoff_month < result.invest_now.debt_payoff_month


def test_high_interest_debt_favors_paying_it_off():
    # Debt APR (22%) is far above the expected investment return (7%), so
    # paying it off first should win comfortably over a long horizon.
    result = compare(make_inputs(debt_apr=0.22, expected_annual_return=0.07), horizon_months=60)
    assert result.better_option == "pay_off_debt_first"


def test_low_interest_debt_favors_investing():
    # A cheap loan (3%) against a much higher expected return (9%) should
    # flip the recommendation toward investing instead.
    result = compare(make_inputs(debt_apr=0.03, expected_annual_return=0.09), horizon_months=60)
    assert result.better_option == "invest_now"


def test_both_scenarios_pay_off_debt_by_a_long_enough_horizon():
    result = compare(make_inputs(), horizon_months=120)
    assert result.pay_off_debt_first.remaining_debt_at_horizon == 0.0
    assert result.invest_now.remaining_debt_at_horizon == 0.0


def test_short_horizon_leaves_remaining_debt_for_minimum_only_track():
    result = compare(
        make_inputs(debt_balance=3000, debt_apr=0.20, minimum_payment=100, extra_amount=20),
        horizon_months=6,
    )
    assert result.invest_now.remaining_debt_at_horizon > 0


def test_contribution_streams_are_same_length_as_horizon():
    result = compare(make_inputs(), horizon_months=24)
    assert len(result.pay_off_debt_first.investment_contributions) == 24
    assert len(result.invest_now.investment_contributions) == 24


def test_net_worth_difference_is_nonnegative():
    result = compare(make_inputs(), horizon_months=60)
    assert result.net_worth_difference >= 0


def test_breakeven_return_rate_equals_debt_apr():
    # Ignoring risk, taxes, and the psychological value of being debt-free,
    # investing beats paying off debt exactly when the expected return
    # clears the guaranteed "return" of not paying that interest.
    result = compare(make_inputs(debt_apr=0.055), horizon_months=36)
    assert result.breakeven_return_rate == 0.055


def test_minimum_payment_below_interest_raises_clear_error():
    with pytest.raises(ValueError):
        compare(make_inputs(debt_balance=8000, debt_apr=0.22, minimum_payment=50), horizon_months=12)


def test_compare_rejects_zero_debt_balance():
    with pytest.raises(ValueError):
        compare(make_inputs(debt_balance=0), horizon_months=36)


def test_compare_rejects_negative_extra_amount():
    with pytest.raises(ValueError):
        compare(make_inputs(extra_amount=-50), horizon_months=36)


def test_compare_rejects_zero_horizon():
    with pytest.raises(ValueError):
        compare(make_inputs(), horizon_months=0)


def test_compare_rejects_return_below_negative_100_percent():
    with pytest.raises(ValueError):
        compare(make_inputs(expected_annual_return=-1.5), horizon_months=36)
