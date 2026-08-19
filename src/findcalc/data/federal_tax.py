"""2025 federal individual income tax parameters, single filer only.

Source: Tax Foundation, "2025 Tax Brackets and Federal Income Tax Rates"
(https://taxfoundation.org/data/all/federal/2025-tax-brackets/), cross-checked
against NerdWallet's 2025 bracket writeup. Standard deduction and Social
Security wage base confirmed against the same Tax Foundation page and the
SSA's 2025 wage base announcement, respectively.

This is a snapshot for tax year 2025. It does not update itself and will go
stale every year the IRS re-indexes brackets for inflation -- if you're
using this for a real decision, check irs.gov for the current year first.
"""

from __future__ import annotations

# (bracket floor, marginal rate) for a single filer, tax year 2025.
FEDERAL_BRACKETS_SINGLE: list[tuple[float, float]] = [
    (0, 0.10),
    (11_925, 0.12),
    (48_475, 0.22),
    (103_350, 0.24),
    (197_300, 0.32),
    (250_525, 0.35),
    (626_350, 0.37),
]

STANDARD_DEDUCTION_SINGLE_2025 = 15_750.0

# Social Security (OASDI): 6.2% on wages up to the annual wage base.
SOCIAL_SECURITY_RATE = 0.062
SOCIAL_SECURITY_WAGE_BASE_2025 = 176_100.0

# Medicare: 1.45% on all wages, plus an extra 0.9% on wages above the
# threshold (unindexed since it was introduced by the ACA).
MEDICARE_RATE = 0.0145
ADDITIONAL_MEDICARE_RATE = 0.009
ADDITIONAL_MEDICARE_THRESHOLD_SINGLE = 200_000.0
