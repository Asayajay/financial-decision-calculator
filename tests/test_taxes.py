import pytest

from findcalc.taxes import compute_fica, compute_federal_tax, compute_state_tax, compute_take_home


def test_federal_tax_matches_hand_calculation_for_80k():
    # $80,000 - $15,750 standard deduction = $64,250 taxable.
    # 10% * 11,925 + 12% * 36,550 + 22% * 15,775 = 1,192.50 + 4,386 + 3,470.50
    assert compute_federal_tax(80_000) == 9_049.0


def test_federal_tax_is_zero_below_standard_deduction():
    assert compute_federal_tax(10_000) == 0.0


def test_federal_tax_increases_with_income():
    assert compute_federal_tax(150_000) > compute_federal_tax(80_000)


def test_fica_matches_hand_calculation_under_wage_base():
    # 80,000 * 6.2% + 80,000 * 1.45% = 4,960 + 1,160
    assert compute_fica(80_000) == 6_120.0


def test_fica_caps_social_security_at_wage_base():
    below_base = compute_fica(176_100)
    above_base = compute_fica(300_000)
    # Social security portion is capped, so FICA on 300k should be less than
    # a naive flat-rate extrapolation from the capped amount.
    naive_extrapolation = below_base * (300_000 / 176_100)
    assert above_base < naive_extrapolation


def test_fica_applies_additional_medicare_surtax_above_200k():
    just_under = compute_fica(200_000)
    just_over = compute_fica(210_000)
    # Expected marginal FICA on the extra 10k: 1.45% + 0.9% additional
    # Medicare (social security is already maxed out well before 200k).
    expected_marginal = 10_000 * (0.0145 + 0.009)
    assert round(just_over - just_under, 2) == round(expected_marginal, 2)


def test_state_tax_zero_for_no_tax_state():
    assert compute_state_tax(90_000, "Texas") == 0.0


def test_state_tax_flat_rate_applies_after_standard_deduction():
    # Colorado flat 4.4% on (90,000 - 15,750)
    expected = round((90_000 - 15_750) * 0.044, 2)
    assert compute_state_tax(90_000, "Colorado") == expected


def test_state_tax_graduated_uses_top_rate_above_threshold():
    low_income_tax = compute_state_tax(20_000, "California")
    high_income_tax = compute_state_tax(1_200_000, "California")
    # Effective rate should be much higher for the high earner given
    # California's top rate kicks in at $1,000,000.
    assert (high_income_tax / 1_200_000) > (low_income_tax / 20_000)


def test_state_tax_unknown_state_raises():
    with pytest.raises(KeyError):
        compute_state_tax(80_000, "Not A Real State")


def test_take_home_total_tax_is_sum_of_components():
    result = compute_take_home(95_000, "New York")
    expected_total = round(result.federal_tax + result.state_tax + result.fica, 2)
    assert result.total_tax == expected_total


def test_take_home_net_annual_equals_gross_minus_total_tax():
    result = compute_take_home(95_000, "New York")
    assert result.net_annual == round(result.gross_salary - result.total_tax, 2)


def test_take_home_zero_salary_has_zero_effective_rate():
    result = compute_take_home(0, "Texas")
    assert result.effective_tax_rate == 0.0
