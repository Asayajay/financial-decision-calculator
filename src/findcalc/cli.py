"""Command-line entry point for all three calculators.

Every subcommand prints the full math breakdown to the terminal and can
optionally write the same numbers to a CSV file with --csv.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import asdict, is_dataclass

from findcalc.debt_vs_invest import DebtVsInvestInputs, sensitivity_by_return
from findcalc.debt_vs_invest import compare as compare_debt_vs_invest
from findcalc.job_offer import JobOffer
from findcalc.job_offer import compare_offers
from findcalc.lease_vs_buy import BuyInputs, LeaseInputs, find_crossover_month
from findcalc.lease_vs_buy import compare as compare_lease_vs_buy


def _flatten(obj, prefix: str = "") -> dict:
    """Turn a (possibly nested) dataclass into a flat dict of column -> value,
    for CSV export. Lists of numbers are dropped since they don't fit a
    single CSV cell (investment_contributions, for instance)."""
    row: dict = {}
    if is_dataclass(obj):
        for key, value in asdict(obj).items():
            full_key = f"{prefix}{key}"
            if is_dataclass(value):
                row.update(_flatten(value, prefix=f"{full_key}."))
            elif isinstance(value, list):
                continue
            else:
                row[full_key] = value
    return row


def export_csv(rows: list[dict], path: str) -> None:
    if not rows:
        raise ValueError("nothing to export")
    # Different rows can come from different dataclasses (e.g. a buy row
    # and a lease row have almost no fields in common), so the column list
    # has to be the union of every row's keys, not just the first row's.
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _print_section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def _print_kv(label: str, value) -> None:
    if isinstance(value, float):
        print(f"  {label}: {value:,.2f}")
    else:
        print(f"  {label}: {value}")


def run_lease_vs_buy(args: argparse.Namespace) -> None:
    buy_inputs = BuyInputs(
        vehicle_price=args.price,
        down_payment=args.down_payment,
        loan_apr=args.loan_apr,
        loan_term_months=args.loan_term_months,
        sales_tax_rate=args.sales_tax_rate,
        annual_insurance=args.buy_insurance,
        annual_maintenance=args.buy_maintenance,
        annual_registration_fee=args.buy_registration,
        annual_depreciation_rate=args.depreciation_rate,
    )
    lease_inputs = LeaseInputs(
        due_at_signing=args.lease_due_at_signing,
        monthly_payment=args.lease_monthly,
        lease_term_months=args.lease_term_months,
        disposition_fee=args.lease_disposition_fee,
        mileage_overage_fee=args.lease_mileage_fee,
        annual_insurance=args.lease_insurance,
        annual_maintenance=args.lease_maintenance,
        annual_registration_fee=args.lease_registration,
    )

    result = compare_lease_vs_buy(buy_inputs, lease_inputs, args.horizon_months)

    _print_section(f"Buy, over {result.horizon_months} months")
    for label, value in asdict(result.buy).items():
        _print_kv(label, value)

    _print_section(f"Lease, over {result.horizon_months} months")
    for label, value in asdict(result.lease).items():
        _print_kv(label, value)

    _print_section("Verdict")
    _print_kv("cheaper_option", result.cheaper_option)
    _print_kv("savings", result.savings)

    if args.find_crossover:
        crossover = find_crossover_month(buy_inputs, lease_inputs, max_months=args.find_crossover)
        if crossover is None:
            _print_kv(
                "crossover_month",
                f"none found within {args.find_crossover} months -- {result.cheaper_option} stays cheaper the whole window",
            )
        else:
            _print_kv("crossover_month", f"{crossover} (the cheaper option flips there)")

    if args.csv:
        row = {"scenario": "buy", **_flatten(result.buy)}
        row2 = {"scenario": "lease", **_flatten(result.lease)}
        export_csv([row, row2], args.csv)
        print(f"\nWrote {args.csv}")


def run_debt_vs_invest(args: argparse.Namespace) -> None:
    inputs = DebtVsInvestInputs(
        debt_balance=args.debt_balance,
        debt_apr=args.debt_apr,
        minimum_payment=args.minimum_payment,
        extra_amount=args.extra_amount,
        expected_annual_return=args.expected_return,
    )
    result = compare_debt_vs_invest(inputs, args.horizon_months)

    for scenario in (result.pay_off_debt_first, result.invest_now):
        _print_section(scenario.name)
        for key, value in asdict(scenario).items():
            if key == "investment_contributions":
                continue
            _print_kv(key, value)

    _print_section("Verdict")
    _print_kv("better_option", result.better_option)
    _print_kv("net_worth_difference", result.net_worth_difference)
    _print_kv("breakeven_return_rate", result.breakeven_return_rate)

    if args.sensitivity:
        rates = [float(r) for r in args.sensitivity.split(",")]
        _print_section("Sensitivity to expected return")
        for row in sensitivity_by_return(inputs, args.horizon_months, rates):
            print(
                f"  {row.expected_annual_return:.2%}: {row.better_option} "
                f"(by ${row.net_worth_difference:,.2f})"
            )

    if args.csv:
        rows = []
        for scenario in (result.pay_off_debt_first, result.invest_now):
            row = _flatten(scenario)
            row.pop("investment_contributions", None)
            rows.append(row)
        export_csv(rows, args.csv)
        print(f"\nWrote {args.csv}")


def _parse_offer(raw: str) -> JobOffer:
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 3:
        raise argparse.ArgumentTypeError(
            "offer must be 'label|state|salary[|signing_bonus[|relocation]]', "
            f"got {raw!r}"
        )
    label, state, salary = parts[0], parts[1], float(parts[2])
    signing_bonus = float(parts[3]) if len(parts) > 3 else 0.0
    relocation = float(parts[4]) if len(parts) > 4 else 0.0
    return JobOffer(
        label=label,
        state=state,
        gross_salary=salary,
        signing_bonus=signing_bonus,
        relocation_assistance=relocation,
    )


def run_job_offer(args: argparse.Namespace) -> None:
    comparison = compare_offers(args.offer)

    rows = []
    for result in comparison.results:
        _print_section(result.label)
        _print_kv("state", result.state)
        _print_kv("gross_salary", result.take_home.gross_salary)
        _print_kv("federal_tax", result.take_home.federal_tax)
        _print_kv("state_tax", result.take_home.state_tax)
        _print_kv("fica", result.take_home.fica)
        _print_kv("net_annual", result.take_home.net_annual)
        _print_kv("net_monthly", result.take_home.net_monthly)
        _print_kv("first_year_cash", result.first_year_cash)
        _print_kv("cost_of_living_index", result.cost_of_living_index)
        _print_kv("col_adjusted_net_annual", result.col_adjusted_net_annual)
        row = {"label": result.label, **_flatten(result.take_home)}
        row["first_year_cash"] = result.first_year_cash
        row["cost_of_living_index"] = result.cost_of_living_index
        row["col_adjusted_net_annual"] = result.col_adjusted_net_annual
        rows.append(row)

    _print_section("Verdict")
    _print_kv("best by raw net income", comparison.best_by_raw_net_income)
    _print_kv("best by cost-of-living-adjusted income", comparison.best_by_col_adjusted_income)

    if args.csv:
        export_csv(rows, args.csv)
        print(f"\nWrote {args.csv}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="findcalc",
        description="Transparent calculators for lease-vs-buy, debt-vs-invest, and job-offer decisions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    lvb = subparsers.add_parser("lease-vs-buy", help="Compare leasing a car to buying one.")
    lvb.add_argument("--price", type=float, required=True)
    lvb.add_argument("--down-payment", type=float, default=0.0)
    lvb.add_argument("--loan-apr", type=float, required=True)
    lvb.add_argument("--loan-term-months", type=int, required=True)
    lvb.add_argument("--sales-tax-rate", type=float, default=0.0)
    lvb.add_argument("--buy-insurance", type=float, default=0.0, help="Annual insurance if bought.")
    lvb.add_argument("--buy-maintenance", type=float, default=0.0, help="Annual maintenance if bought.")
    lvb.add_argument("--buy-registration", type=float, default=0.0)
    lvb.add_argument("--depreciation-rate", type=float, default=0.15)
    lvb.add_argument("--lease-due-at-signing", type=float, required=True)
    lvb.add_argument("--lease-monthly", type=float, required=True)
    lvb.add_argument("--lease-term-months", type=int, required=True)
    lvb.add_argument("--lease-disposition-fee", type=float, default=0.0)
    lvb.add_argument("--lease-mileage-fee", type=float, default=0.0)
    lvb.add_argument("--lease-insurance", type=float, default=0.0, help="Annual insurance if leased.")
    lvb.add_argument("--lease-maintenance", type=float, default=0.0, help="Annual maintenance if leased.")
    lvb.add_argument("--lease-registration", type=float, default=0.0)
    lvb.add_argument("--horizon-months", type=int, required=True)
    lvb.add_argument(
        "--find-crossover",
        type=int,
        metavar="MAX_MONTHS",
        help="Search up to this many months for the point where the cheaper option flips.",
    )
    lvb.add_argument("--csv", help="Write the breakdown to this CSV path.")
    lvb.set_defaults(func=run_lease_vs_buy)

    dvi = subparsers.add_parser("debt-vs-invest", help="Compare paying off debt to investing extra cash.")
    dvi.add_argument("--debt-balance", type=float, required=True)
    dvi.add_argument("--debt-apr", type=float, required=True)
    dvi.add_argument("--minimum-payment", type=float, required=True)
    dvi.add_argument("--extra-amount", type=float, required=True)
    dvi.add_argument("--expected-return", type=float, required=True)
    dvi.add_argument("--horizon-months", type=int, required=True)
    dvi.add_argument(
        "--sensitivity",
        metavar="RATE,RATE,...",
        help="Comma-separated expected-return rates to re-run the comparison at, e.g. 0.03,0.05,0.07,0.10",
    )
    dvi.add_argument("--csv", help="Write the breakdown to this CSV path.")
    dvi.set_defaults(func=run_debt_vs_invest)

    job = subparsers.add_parser("job-offer", help="Compare job offers across locations.")
    job.add_argument(
        "--offer",
        action="append",
        type=_parse_offer,
        required=True,
        help="Repeatable. Format: label|state|salary[|signing_bonus[|relocation]]",
    )
    job.add_argument("--csv", help="Write the comparison to this CSV path.")
    job.set_defaults(func=run_job_offer)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
