# Data sources

Every static number baked into this repo, where it came from, and what's simplified.

## Federal tax (`src/findcalc/data/federal_tax.py`)

- 2025 federal income tax brackets, single filer: [Tax Foundation, "2025 Tax Brackets and Federal Income Tax Rates"](https://taxfoundation.org/data/all/federal/2025-tax-brackets/), cross-checked against [NerdWallet's 2025 bracket writeup](https://www.nerdwallet.com/taxes/learn/2025-tax-brackets).
- 2025 standard deduction, single filer ($15,750): same Tax Foundation page.
- Social Security wage base for 2025 ($176,100) and the 6.2% rate: [SSA's 2025 wage base announcement](https://hrpayroll.ssc.jhu.edu/wp-content/uploads/sites/14/2025-Social-Security-wage-base-increase.pdf).
- Medicare rate (1.45%) and the 0.9% additional Medicare surtax above $200,000: [IRS Topic no. 751](https://www.irs.gov/taxtopics/tc751).

Snapshot for tax year 2025 only. Married filing jointly, dependents, itemizing, and credits are all out of scope -- this models a single filer taking the standard deduction, full stop.

## State tax (`src/findcalc/data/state_tax.py`)

Full bracket ladders for every graduated-rate state, plus flat rates and no-tax states, all from [Tax Foundation, "2025 State Income Tax Rates and Brackets"](https://taxfoundation.org/data/all/state/state-income-tax-rates/), single filer.

Two real simplifications:

- Every state uses the *federal* standard deduction ($15,750) as a stand-in for its own standard deduction or personal exemption. States set their own amounts, and some don't offer a deduction at all. Building an accurate 41-state deduction table for a modest accuracy gain (it rarely changes which bracket someone lands in) wasn't worth the added data-entry surface for a personal project.
- Washington taxes capital gains above a threshold but has no tax on W-2 wages, so it's modeled as 0% here since this tool compares salaries, not capital gains.

An earlier version of this file only tracked each graduated state's lowest and highest published rate and interpolated between them. That badly understated tax for states with many brackets -- a $150,000 salary in California came out to a 1% effective state tax instead of the real ~9%. Every graduated state now carries its actual bracket ladder.

## Cost of living (`src/findcalc/data/cost_of_living.py`)

State-level composite cost of living index, Q1 2026, US average = 100: [Missouri Economic Research and Information Center (MERIC)](https://meric.mo.gov/data/cost-living-data-series). The composite covers housing, utilities, groceries, transportation, health care, and misc. goods and services.

This is **state-level, not city-level**. Comparing a job offer in San Francisco to one in Fresno (both California) with this data would be misleading, since the tool can't see the difference between those two cities -- it only knows "California." City-level cost of living data generally sits behind a paid feed (C2ER's own index, for instance); MERIC's free state-level series was the tradeoff made here. If you're comparing two cities in the same state, this tool isn't precise enough to help.

## What's not modeled at all

- Local/city income tax (New York City's added tax on top of NY state tax, for instance).
- FICA employer match, 401(k)/HSA contributions, or any other payroll deduction that changes taxable income.
- Sales tax differences between locations (relevant to the job-offer comparator, since cost of living captures average consumption patterns, not any one person's actual spending).
- Inflation, beyond whatever's already baked into the depreciation-rate and expected-return assumptions you supply for lease-vs-buy and debt-vs-invest.

## Staleness

Every one of these numbers is a snapshot. Tax brackets get re-indexed for inflation every year, the standard deduction changes annually (and can change legislatively, as the 2025 numbers already reflect), and MERIC republishes its cost of living index quarterly. None of this updates itself -- if you're using this for a real decision, check the source pages above for the current numbers before you trust the output.
