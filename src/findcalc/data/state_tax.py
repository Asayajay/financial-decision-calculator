"""State individual income tax structure, snapshot for tax year 2025.

Source: Tax Foundation, "2025 State Income Tax Rates and Brackets"
(https://taxfoundation.org/data/all/state/state-income-tax-rates/).

Real graduated-bracket states have anywhere from 3 to 9 brackets. Modeling
every state's exact bracket table is a lot of data entry for a personal
project, and most of it barely moves the answer for a typical salary. So
graduated states here are simplified to two tiers: the state's lowest
published rate below the top bracket's threshold, and the top published
rate at or above it. This is a real, documented approximation, not the
literal statute -- it will slightly overstate tax for someone whose income
lands in a middle bracket. Flat-rate and no-tax states are modeled exactly,
since there's nothing to approximate there.

Washington taxes capital gains above a threshold but has no tax on wages,
so it's modeled as 0% here since this tool compares salaries.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StateTaxModel:
    kind: str  # "none", "flat", or "graduated_2tier"
    flat_rate: float = 0.0
    low_rate: float = 0.0
    top_rate: float = 0.0
    top_threshold: float = 0.0


NO_TAX_STATES = [
    "Alaska",
    "Florida",
    "Nevada",
    "New Hampshire",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Washington",
    "Wyoming",
]

FLAT_TAX_RATES = {
    "Arizona": 0.0250,
    "Colorado": 0.0440,
    "Georgia": 0.0539,
    "Idaho": 0.05695,
    "Illinois": 0.0495,
    "Indiana": 0.0300,
    "Iowa": 0.0380,
    "Kentucky": 0.0400,
    "Louisiana": 0.0300,
    "Michigan": 0.0425,
    "Mississippi": 0.0440,
    "North Carolina": 0.0425,
    "Pennsylvania": 0.0307,
    "Utah": 0.0455,
}

# state -> (low_rate, top_rate, top_threshold)
GRADUATED_TAX_BRACKETS = {
    "Alabama": (0.0200, 0.0500, 3_000),
    "Arkansas": (0.0200, 0.0390, 4_500),
    "California": (0.0100, 0.1330, 1_000_000),
    "Connecticut": (0.0200, 0.0699, 500_000),
    "Delaware": (0.0220, 0.0660, 60_000),
    "District of Columbia": (0.0400, 0.1075, 1_000_000),
    "Hawaii": (0.0140, 0.1100, 325_000),
    "Kansas": (0.0520, 0.0558, 23_000),
    "Maine": (0.0580, 0.0715, 63_450),
    "Maryland": (0.0200, 0.0575, 250_000),
    "Massachusetts": (0.0500, 0.0900, 1_083_150),
    "Minnesota": (0.0535, 0.0985, 198_630),
    "Missouri": (0.0200, 0.0470, 9_191),
    "Montana": (0.0470, 0.0590, 21_100),
    "Nebraska": (0.0246, 0.0520, 38_870),
    "New Jersey": (0.0140, 0.1075, 1_000_000),
    "New Mexico": (0.0150, 0.0590, 210_000),
    "New York": (0.0400, 0.1090, 25_000_000),
    "North Dakota": (0.0195, 0.0250, 244_825),
    "Ohio": (0.0275, 0.0350, 100_000),
    "Oklahoma": (0.0025, 0.0475, 7_200),
    "Oregon": (0.0475, 0.0990, 125_000),
    "Rhode Island": (0.0375, 0.0599, 181_650),
    "South Carolina": (0.0000, 0.0620, 17_830),
    "Vermont": (0.0335, 0.0875, 242_000),
    "Virginia": (0.0200, 0.0575, 17_000),
    "West Virginia": (0.0222, 0.0482, 60_000),
    "Wisconsin": (0.0350, 0.0765, 323_290),
}


def get_state_tax_model(state: str) -> StateTaxModel:
    if state in NO_TAX_STATES:
        return StateTaxModel(kind="none")
    if state in FLAT_TAX_RATES:
        return StateTaxModel(kind="flat", flat_rate=FLAT_TAX_RATES[state])
    if state in GRADUATED_TAX_BRACKETS:
        low_rate, top_rate, top_threshold = GRADUATED_TAX_BRACKETS[state]
        return StateTaxModel(
            kind="graduated_2tier",
            low_rate=low_rate,
            top_rate=top_rate,
            top_threshold=top_threshold,
        )
    raise KeyError(
        f"Unknown state {state!r}. Check spelling -- states must match the "
        "names used in this dataset exactly (e.g. 'New York', not 'NY')."
    )


def known_states() -> list[str]:
    return sorted(NO_TAX_STATES + list(FLAT_TAX_RATES) + list(GRADUATED_TAX_BRACKETS))
