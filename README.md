# Financial decision calculator

Three calculators for real financial decisions, all built the same way: show every
number that goes into the answer, not just a final recommendation.

- **Lease vs. buy** a car, as a full cost of ownership comparison, not just a
  monthly payment comparison.
- **Pay off debt vs. invest** extra cash, run as two actual month-by-month
  schedules instead of a rule of thumb about interest rates.
- **Compare job offers across states**, after federal tax, state tax, FICA,
  and cost of living, since raw salary numbers alone aren't comparable across
  locations.

I built this after noticing that most calculators for these decisions online
either hide the math behind a single "you should do X" answer, or only handle
one piece of the decision (a lease payment calculator that ignores insurance
and resale value, say). Every function here returns a full breakdown, and the
web UI and CLI both print that breakdown in full.

## Try it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -r webapp/requirements.txt   # only needed for the web UI
```

### Command line

```bash
python -m findcalc.cli lease-vs-buy \
  --price 30000 --down-payment 3000 --loan-apr 0.06 --loan-term-months 60 \
  --sales-tax-rate 0.07 --buy-insurance 1200 --buy-maintenance 600 \
  --lease-due-at-signing 2000 --lease-monthly 350 --lease-term-months 36 \
  --lease-insurance 1100 --lease-maintenance 200 \
  --horizon-months 36 --find-crossover 120
```

```bash
python -m findcalc.cli debt-vs-invest \
  --debt-balance 8000 --debt-apr 0.22 --minimum-payment 200 --extra-amount 150 \
  --expected-return 0.07 --horizon-months 60 --sensitivity 0.03,0.05,0.10,0.15
```

```bash
python -m findcalc.cli job-offer \
  --offer "San Francisco|California|150000" \
  --offer "Austin|Texas|120000|5000"
```

Every subcommand takes `--csv path.csv` to write the same breakdown to a file
instead of (or in addition to) the terminal. Run any subcommand with `-h` for
the full flag list.

### Web UI

```bash
python webapp/app.py
```

Opens a Flask app at `http://127.0.0.1:8077` with a form and a chart for each
calculator. The backend is a thin wrapper around the same `findcalc` package
the CLI uses, so the two never disagree.

## Project layout

- `src/findcalc/amortization.py` -- shared loan math (amortization schedules,
  fixed-payment payoff schedules, future value of a contribution stream).
  Every other calculator is built on top of this.
- `src/findcalc/lease_vs_buy.py` -- the lease vs. buy comparison, plus a
  crossover-month finder that walks the horizon month by month to find where
  the cheaper option flips.
- `src/findcalc/debt_vs_invest.py` -- the debt-payoff vs. invest comparison,
  plus a sensitivity sweep across a range of expected investment returns.
- `src/findcalc/taxes.py` -- federal tax, FICA, and state tax on a single
  filer's W-2 salary.
- `src/findcalc/job_offer.py` -- wraps `taxes.py` with a cost-of-living
  adjustment to compare offers across states.
- `src/findcalc/data/` -- the actual tax brackets and cost-of-living numbers,
  each sourced (see [DATA_SOURCES.md](DATA_SOURCES.md)).
- `src/findcalc/cli.py` -- the command-line entry point.
- `webapp/` -- the Flask app: `app.py` (backend), `templates/`, `static/`.
- `tests/` -- one test file per module, plus `test_cli.py` and
  `test_webapp.py` for the two front ends.

## Tests

```bash
pytest
```

No network calls, no external services. Every test runs against the plain
math and static reference data in this repo.

## What this doesn't do

- No itemized deductions, dependents, or filing statuses other than single.
- No local/city income tax (relevant if you're comparing, say, New York City
  against a state with no local tax on top of its state tax).
- Cost of living is state-level, not city-level -- it can't tell Austin from
  Dallas, only Texas from California. See DATA_SOURCES.md for why.
- The debt-vs-invest breakeven treats "expected return" as certain. Real
  investment returns are a distribution, not a point estimate, and paying
  off debt is the only one of the two options that's actually guaranteed.
  The sensitivity sweep is there because that uncertainty is real, not a
  detail to wave away.

Full sourcing and every simplification made in the reference data lives in
[DATA_SOURCES.md](DATA_SOURCES.md).
