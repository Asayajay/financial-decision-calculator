import pytest

from findcalc.job_offer import JobOffer, compare_offers, evaluate_offer


def test_evaluate_offer_computes_take_home_and_col_adjustment():
    offer = JobOffer(label="Austin role", state="Texas", gross_salary=120_000)
    result = evaluate_offer(offer)
    assert result.take_home.net_annual > 0
    assert result.cost_of_living_index == pytest.approx(90.7)
    # Texas is cheaper than the national average, so col-adjusted income
    # should be higher than raw net income.
    assert result.col_adjusted_net_annual > result.take_home.net_annual


def test_evaluate_offer_penalizes_expensive_location():
    offer = JobOffer(label="SF role", state="California", gross_salary=120_000)
    result = evaluate_offer(offer)
    # California is more expensive than average, so col-adjusted income
    # should be lower than raw net income.
    assert result.col_adjusted_net_annual < result.take_home.net_annual


def test_evaluate_offer_includes_signing_bonus_in_first_year_cash():
    offer = JobOffer(label="Offer", state="Texas", gross_salary=100_000, signing_bonus=10_000)
    result = evaluate_offer(offer)
    assert result.first_year_cash == result.take_home.net_annual + 10_000


def test_compare_offers_can_flip_winner_after_col_adjustment():
    # Higher raw salary in an expensive state, lower raw salary in a cheap
    # one -- the cheap-state offer should win once cost of living is priced
    # in, even though it loses on a raw-dollars basis.
    high_salary_expensive = JobOffer(
        label="San Francisco", state="California", gross_salary=150_000
    )
    lower_salary_cheap = JobOffer(label="Austin", state="Texas", gross_salary=120_000)

    comparison = compare_offers([high_salary_expensive, lower_salary_cheap])

    assert comparison.best_by_raw_net_income == "San Francisco"
    assert comparison.best_by_col_adjusted_income == "Austin"


def test_compare_offers_rejects_empty_list():
    with pytest.raises(ValueError):
        compare_offers([])


def test_compare_offers_returns_one_result_per_offer():
    offers = [
        JobOffer(label="A", state="Texas", gross_salary=100_000),
        JobOffer(label="B", state="Colorado", gross_salary=110_000),
        JobOffer(label="C", state="New York", gross_salary=130_000),
    ]
    comparison = compare_offers(offers)
    assert len(comparison.results) == 3
    assert {r.label for r in comparison.results} == {"A", "B", "C"}
