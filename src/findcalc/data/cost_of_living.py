"""State-level cost of living index, Q1 2026 snapshot.

Source: Missouri Economic Research and Information Center (MERIC) composite
cost of living index (https://meric.mo.gov/data/cost-living-data-series),
US average = 100. The composite covers housing, utilities, groceries,
transportation, health care, and misc. goods and services.

This is state-level, not city-level. A real MSA-level index (say, San
Francisco vs. Fresno, both in California) would tell a very different
story than the state average does, but city-level cost of living data
generally sits behind a paid data feed (C2ER's own index, for one).
MERIC's state-level numbers are the most complete free public series
available, so that is the tradeoff this tool makes. Don't use this to
compare two cities in the same state -- it can't see that difference.
"""

from __future__ import annotations

COST_OF_LIVING_INDEX: dict[str, float] = {
    "Alabama": 85.0,
    "Alaska": 129.0,
    "Arizona": 107.6,
    "Arkansas": 89.1,
    "California": 140.5,
    "Colorado": 101.8,
    "Connecticut": 114.2,
    "Delaware": 101.7,
    "District of Columbia": 134.3,
    "Florida": 100.7,
    "Georgia": 90.6,
    "Hawaii": 184.8,
    "Idaho": 101.7,
    "Illinois": 95.1,
    "Indiana": 88.3,
    "Iowa": 88.6,
    "Kansas": 87.6,
    "Kentucky": 92.5,
    "Louisiana": 91.1,
    "Maine": 114.6,
    "Maryland": 121.1,
    "Massachusetts": 147.8,
    "Michigan": 93.9,
    "Minnesota": 93.4,
    "Mississippi": 86.2,
    "Missouri": 88.6,
    "Montana": 105.9,
    "Nebraska": 91.3,
    "Nevada": 100.7,
    "New Hampshire": 110.1,
    "New Jersey": 118.8,
    "New Mexico": 89.9,
    "New York": 124.7,
    "North Carolina": 96.6,
    "North Dakota": 90.7,
    "Ohio": 93.7,
    "Oklahoma": 83.5,
    "Oregon": 109.6,
    "Pennsylvania": 96.2,
    "Rhode Island": 111.2,
    "South Carolina": 91.9,
    "South Dakota": 94.1,
    "Tennessee": 88.9,
    "Texas": 90.7,
    "Utah": 100.6,
    "Vermont": 113.0,
    "Virginia": 99.1,
    "Washington": 114.6,
    "West Virginia": 87.9,
    "Wisconsin": 97.4,
    "Wyoming": 93.7,
}


def get_col_index(state: str) -> float:
    try:
        return COST_OF_LIVING_INDEX[state]
    except KeyError as exc:
        raise KeyError(
            f"No cost of living index for {state!r}. Check spelling against "
            "findcalc.data.cost_of_living.COST_OF_LIVING_INDEX."
        ) from exc
