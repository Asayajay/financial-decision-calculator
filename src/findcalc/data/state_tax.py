"""State individual income tax structure, snapshot for tax year 2025.

Source: Tax Foundation, "2025 State Income Tax Rates and Brackets"
(https://taxfoundation.org/data/all/state/state-income-tax-rates/), single
filer brackets.

Every graduated state's full bracket ladder is modeled here (not just its
top and bottom rate) -- an earlier draft of this file only tracked the
lowest and highest published rate, which badly understated tax for states
like California that step through 9+ brackets before hitting the top one.
A $150,000 salary in California should land around a 9%+ marginal rate,
not the 1% bottom bracket.

The one remaining simplification: every state here uses the *federal*
standard deduction ($15,750 for 2025) as a stand-in for the state's own
standard deduction or personal exemption, rather than each state's actual
figure. States set their own deduction amounts and some don't offer one at
all, so this will be off by a bracket or two at the margin, particularly
for lower incomes. Modeling that exactly would mean tracking another
41-state dataset for a change that rarely flips which bracket someone
lands in.

Washington taxes capital gains above a threshold but has no tax on wages,
so it's modeled as 0% here since this tool compares W-2 salaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StateTaxModel:
    kind: str  # "none", "flat", or "graduated"
    flat_rate: float = 0.0
    brackets: tuple[tuple[float, float], ...] = field(default_factory=tuple)


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

# state -> ((bracket floor, marginal rate), ...), lowest bracket first.
GRADUATED_TAX_BRACKETS = {
    "Alabama": ((0, 0.0200), (500, 0.0400), (3_000, 0.0500)),
    "Arkansas": ((0, 0.0200), (4_500, 0.0390)),
    "California": (
        (0, 0.0100),
        (10_756, 0.0200),
        (25_499, 0.0400),
        (40_245, 0.0600),
        (55_866, 0.0800),
        (70_606, 0.0930),
        (360_659, 0.1030),
        (432_787, 0.1130),
        (721_314, 0.1230),
        (1_000_000, 0.1330),
    ),
    "Connecticut": (
        (0, 0.0200),
        (10_000, 0.0450),
        (50_000, 0.0550),
        (100_000, 0.0600),
        (200_000, 0.0650),
        (250_000, 0.0690),
        (500_000, 0.0699),
    ),
    "Delaware": (
        (0, 0.0000),
        (2_000, 0.0220),
        (5_000, 0.0390),
        (10_000, 0.0480),
        (20_000, 0.0520),
        (25_000, 0.0555),
        (60_000, 0.0660),
    ),
    "District of Columbia": (
        (0, 0.0400),
        (10_000, 0.0600),
        (40_000, 0.0650),
        (60_000, 0.0850),
        (250_000, 0.0925),
        (500_000, 0.0975),
        (1_000_000, 0.1075),
    ),
    "Hawaii": (
        (0, 0.0140),
        (9_600, 0.0320),
        (14_400, 0.0550),
        (19_200, 0.0640),
        (24_000, 0.0680),
        (36_000, 0.0720),
        (48_000, 0.0760),
        (125_000, 0.0790),
        (175_000, 0.0825),
        (225_000, 0.0900),
        (275_000, 0.1000),
        (325_000, 0.1100),
    ),
    "Kansas": ((0, 0.0520), (23_000, 0.0558)),
    "Maine": ((0, 0.0580), (26_800, 0.0675), (63_450, 0.0715)),
    "Maryland": (
        (0, 0.0200),
        (1_000, 0.0300),
        (2_000, 0.0400),
        (3_000, 0.0475),
        (100_000, 0.0500),
        (125_000, 0.0525),
        (150_000, 0.0550),
        (250_000, 0.0575),
    ),
    "Massachusetts": ((0, 0.0500), (1_083_150, 0.0900)),
    "Minnesota": (
        (0, 0.0535),
        (32_570, 0.0680),
        (106_990, 0.0785),
        (198_630, 0.0985),
    ),
    "Missouri": (
        (0, 0.0000),
        (1_313, 0.0200),
        (2_626, 0.0250),
        (3_939, 0.0300),
        (5_252, 0.0350),
        (6_565, 0.0400),
        (7_878, 0.0450),
        (9_191, 0.0470),
    ),
    "Montana": ((0, 0.0470), (21_100, 0.0590)),
    "Nebraska": (
        (0, 0.0246),
        (4_030, 0.0351),
        (24_120, 0.0501),
        (38_870, 0.0520),
    ),
    "New Jersey": (
        (0, 0.0140),
        (20_000, 0.0175),
        (35_000, 0.0350),
        (40_000, 0.0553),
        (75_000, 0.0637),
        (500_000, 0.0897),
        (1_000_000, 0.1075),
    ),
    "New Mexico": (
        (0, 0.0150),
        (5_500, 0.0320),
        (16_500, 0.0430),
        (33_500, 0.0470),
        (66_500, 0.0490),
        (210_000, 0.0590),
    ),
    "New York": (
        (0, 0.0400),
        (8_500, 0.0450),
        (11_700, 0.0525),
        (13_900, 0.0550),
        (80_650, 0.0600),
        (215_400, 0.0685),
        (1_077_550, 0.0965),
        (5_000_000, 0.1030),
        (25_000_000, 0.1090),
    ),
    "North Dakota": ((0, 0.0000), (48_475, 0.0195), (244_825, 0.0250)),
    "Ohio": ((0, 0.0000), (26_050, 0.0275), (100_000, 0.0350)),
    "Oklahoma": (
        (0, 0.0025),
        (1_000, 0.0075),
        (2_500, 0.0175),
        (3_750, 0.0275),
        (4_900, 0.0375),
        (7_200, 0.0475),
    ),
    "Oregon": ((0, 0.0475), (4_400, 0.0675), (11_050, 0.0875), (125_000, 0.0990)),
    "Rhode Island": ((0, 0.0375), (79_900, 0.0475), (181_650, 0.0599)),
    "South Carolina": ((0, 0.0000), (3_560, 0.0300), (17_830, 0.0620)),
    "Vermont": (
        (0, 0.0335),
        (47_900, 0.0660),
        (116_000, 0.0760),
        (242_000, 0.0875),
    ),
    "Virginia": ((0, 0.0200), (3_000, 0.0300), (5_000, 0.0500), (17_000, 0.0575)),
    "West Virginia": (
        (0, 0.0222),
        (10_000, 0.0296),
        (25_000, 0.0333),
        (40_000, 0.0444),
        (60_000, 0.0482),
    ),
    "Wisconsin": (
        (0, 0.0350),
        (14_680, 0.0440),
        (29_370, 0.0530),
        (323_290, 0.0765),
    ),
}


def get_state_tax_model(state: str) -> StateTaxModel:
    if state in NO_TAX_STATES:
        return StateTaxModel(kind="none")
    if state in FLAT_TAX_RATES:
        return StateTaxModel(kind="flat", flat_rate=FLAT_TAX_RATES[state])
    if state in GRADUATED_TAX_BRACKETS:
        return StateTaxModel(kind="graduated", brackets=GRADUATED_TAX_BRACKETS[state])
    raise KeyError(
        f"Unknown state {state!r}. Check spelling -- states must match the "
        "names used in this dataset exactly (e.g. 'New York', not 'NY')."
    )


def known_states() -> list[str]:
    return sorted(NO_TAX_STATES + list(FLAT_TAX_RATES) + list(GRADUATED_TAX_BRACKETS))
