"""Job-offer-across-locations comparator.

Raw salary numbers don't mean much on their own: a $120,000 offer in Austin
and a $150,000 offer in San Francisco could easily land at the same real
purchasing power once state tax and cost of living are accounted for. This
module runs each offer through the same take-home-pay math, then adjusts
for cost of living so offers are comparable on equal footing.
"""

from __future__ import annotations

from dataclasses import dataclass

from findcalc.data.cost_of_living import get_col_index
from findcalc.taxes import TakeHomeBreakdown, compute_take_home


@dataclass
class JobOffer:
    label: str
    state: str
    gross_salary: float
    signing_bonus: float = 0.0
    relocation_assistance: float = 0.0


@dataclass
class JobOfferResult:
    label: str
    state: str
    take_home: TakeHomeBreakdown
    first_year_cash: float
    cost_of_living_index: float
    col_adjusted_net_annual: float


@dataclass
class JobOfferComparison:
    results: list[JobOfferResult]
    best_by_col_adjusted_income: str
    best_by_raw_net_income: str


def evaluate_offer(offer: JobOffer) -> JobOfferResult:
    if offer.gross_salary <= 0:
        raise ValueError(f"gross_salary must be positive for offer {offer.label!r}")
    if offer.signing_bonus < 0 or offer.relocation_assistance < 0:
        raise ValueError(f"signing_bonus/relocation_assistance can't be negative for offer {offer.label!r}")

    take_home = compute_take_home(offer.gross_salary, offer.state)
    col_index = get_col_index(offer.state)

    # Normalize to "purchasing power at the national average cost of
    # living": if a location is 20% more expensive than average, its net
    # income is worth proportionally less.
    col_adjusted_net_annual = round(take_home.net_annual / (col_index / 100), 2)

    first_year_cash = round(
        take_home.net_annual + offer.signing_bonus + offer.relocation_assistance, 2
    )

    return JobOfferResult(
        label=offer.label,
        state=offer.state,
        take_home=take_home,
        first_year_cash=first_year_cash,
        cost_of_living_index=col_index,
        col_adjusted_net_annual=col_adjusted_net_annual,
    )


def compare_offers(offers: list[JobOffer]) -> JobOfferComparison:
    if not offers:
        raise ValueError("compare_offers requires at least one offer")

    results = [evaluate_offer(offer) for offer in offers]

    best_col_adjusted = max(results, key=lambda r: r.col_adjusted_net_annual)
    best_raw = max(results, key=lambda r: r.take_home.net_annual)

    return JobOfferComparison(
        results=results,
        best_by_col_adjusted_income=best_col_adjusted.label,
        best_by_raw_net_income=best_raw.label,
    )
