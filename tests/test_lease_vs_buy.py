import pytest

from findcalc.lease_vs_buy import (
    BuyInputs,
    LeaseInputs,
    compare,
    compute_buy,
    compute_lease,
    find_crossover_month,
)


def make_buy_inputs(**overrides):
    defaults = dict(
        vehicle_price=30000,
        down_payment=3000,
        loan_apr=0.06,
        loan_term_months=60,
        sales_tax_rate=0.07,
        annual_insurance=1200,
        annual_maintenance=600,
        annual_registration_fee=150,
        annual_depreciation_rate=0.15,
    )
    defaults.update(overrides)
    return BuyInputs(**defaults)


def make_lease_inputs(**overrides):
    defaults = dict(
        due_at_signing=2000,
        monthly_payment=350,
        lease_term_months=36,
        disposition_fee=395,
        mileage_overage_fee=0,
        annual_insurance=1100,
        annual_maintenance=200,
        annual_registration_fee=150,
    )
    defaults.update(overrides)
    return LeaseInputs(**defaults)


def test_buy_finances_price_plus_tax_minus_down_payment():
    result = compute_buy(make_buy_inputs(), horizon_months=60)
    assert result.sales_tax_paid == 2100.0
    assert result.amount_financed == 29100.0


def test_buy_loan_paid_off_by_horizon_when_horizon_equals_term():
    result = compute_buy(make_buy_inputs(), horizon_months=60)
    assert result.loan_balance_at_horizon == 0.0


def test_buy_loan_balance_nonzero_when_horizon_shorter_than_term():
    result = compute_buy(make_buy_inputs(loan_term_months=72), horizon_months=36)
    assert result.loan_balance_at_horizon > 0


def test_buy_resale_value_decreases_with_more_depreciation():
    low_dep = compute_buy(make_buy_inputs(annual_depreciation_rate=0.05), horizon_months=36)
    high_dep = compute_buy(make_buy_inputs(annual_depreciation_rate=0.25), horizon_months=36)
    assert high_dep.estimated_resale_value_at_horizon < low_dep.estimated_resale_value_at_horizon


def test_buy_net_cost_is_outflow_minus_equity():
    result = compute_buy(make_buy_inputs(), horizon_months=36)
    expected = round(result.total_cash_outflow - result.net_equity_at_horizon, 2)
    assert result.net_cost == expected


def test_lease_single_term_matches_horizon():
    result = compute_lease(make_lease_inputs(), horizon_months=36)
    assert result.num_lease_signings == 1
    assert result.total_monthly_payments == 350 * 36
    assert result.total_signing_fees == 2000
    # Lease still active exactly at the end of its term: no disposition fee
    # charged for a term that completes exactly at the horizon boundary is
    # ambiguous in real life, but our model counts full terms that fit
    # evenly as completed.
    assert result.total_disposition_fees == 395


def test_lease_horizon_longer_than_term_triggers_second_signing():
    result = compute_lease(make_lease_inputs(), horizon_months=48)
    assert result.num_lease_signings == 2
    assert result.total_signing_fees == 4000


def test_lease_rejects_nonpositive_term():
    with pytest.raises(ValueError):
        compute_lease(make_lease_inputs(lease_term_months=0), horizon_months=12)


def test_compare_picks_cheaper_option_consistently():
    comparison = compare(make_buy_inputs(), make_lease_inputs(), horizon_months=36)
    assert comparison.cheaper_option in ("buy", "lease", "tie")
    if comparison.cheaper_option == "buy":
        assert comparison.buy.net_cost < comparison.lease.net_cost
    elif comparison.cheaper_option == "lease":
        assert comparison.lease.net_cost < comparison.buy.net_cost


def test_compare_savings_is_nonnegative():
    comparison = compare(make_buy_inputs(), make_lease_inputs(), horizon_months=36)
    assert comparison.savings >= 0


def test_compute_buy_rejects_zero_price():
    with pytest.raises(ValueError):
        compute_buy(make_buy_inputs(vehicle_price=0), horizon_months=36)


def test_compute_buy_rejects_negative_down_payment():
    with pytest.raises(ValueError):
        compute_buy(make_buy_inputs(down_payment=-500), horizon_months=36)


def test_compute_buy_rejects_depreciation_rate_of_one_or_more():
    with pytest.raises(ValueError):
        compute_buy(make_buy_inputs(annual_depreciation_rate=1.0), horizon_months=36)


def test_compute_buy_rejects_zero_horizon():
    with pytest.raises(ValueError):
        compute_buy(make_buy_inputs(), horizon_months=0)


def test_compute_lease_rejects_negative_monthly_payment():
    with pytest.raises(ValueError):
        compute_lease(make_lease_inputs(monthly_payment=-100), horizon_months=36)


def test_compute_lease_rejects_zero_horizon():
    with pytest.raises(ValueError):
        compute_lease(make_lease_inputs(), horizon_months=0)


def test_find_crossover_month_matches_known_flip_point():
    # With these defaults, leasing wins at every horizon through 60 months
    # (the loan term), then buying pulls ahead once the loan is paid off
    # and equity keeps building while lease payments never stop.
    crossover = find_crossover_month(make_buy_inputs(), make_lease_inputs(), max_months=120)
    assert crossover == 65

    before = compare(make_buy_inputs(), make_lease_inputs(), horizon_months=crossover - 1)
    at_crossover = compare(make_buy_inputs(), make_lease_inputs(), horizon_months=crossover)
    assert before.cheaper_option == "lease"
    assert at_crossover.cheaper_option == "buy"


def test_find_crossover_month_returns_none_when_no_flip_occurs():
    # A lease so cheap it never loses just keeps winning the whole window.
    crossover = find_crossover_month(
        make_buy_inputs(), make_lease_inputs(monthly_payment=1), max_months=24
    )
    assert crossover is None


def test_find_crossover_month_rejects_tiny_max_months():
    with pytest.raises(ValueError):
        find_crossover_month(make_buy_inputs(), make_lease_inputs(), max_months=1)
