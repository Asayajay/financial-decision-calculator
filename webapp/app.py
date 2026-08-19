"""Flask backend for the three calculators.

Thin by design, same as the rest of this account's web apps: all the real
math lives in src/findcalc, this file just turns request JSON into the
dataclasses those modules expect and serializes the result back out.
"""

import os
import sys
from dataclasses import asdict

from flask import Flask, jsonify, render_template, request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from findcalc.data.cost_of_living import COST_OF_LIVING_INDEX
from findcalc.data.state_tax import known_states
from findcalc.debt_vs_invest import DebtVsInvestInputs
from findcalc.debt_vs_invest import compare as compare_debt_vs_invest
from findcalc.job_offer import JobOffer, compare_offers
from findcalc.lease_vs_buy import BuyInputs, LeaseInputs
from findcalc.lease_vs_buy import compare as compare_lease_vs_buy

app = Flask(__name__)


def _num(data: dict, key: str, default=0.0):
    value = data.get(key, default)
    return float(value) if value not in (None, "") else default


@app.route("/")
def index():
    return render_template("index.html", states=known_states())


@app.route("/api/states")
def api_states():
    return jsonify(
        [{"state": state, "col_index": COST_OF_LIVING_INDEX[state]} for state in known_states()]
    )


@app.route("/api/lease-vs-buy", methods=["POST"])
def api_lease_vs_buy():
    data = request.get_json(force=True)

    buy_inputs = BuyInputs(
        vehicle_price=_num(data, "price"),
        down_payment=_num(data, "down_payment"),
        loan_apr=_num(data, "loan_apr"),
        loan_term_months=int(_num(data, "loan_term_months")),
        sales_tax_rate=_num(data, "sales_tax_rate"),
        annual_insurance=_num(data, "buy_insurance"),
        annual_maintenance=_num(data, "buy_maintenance"),
        annual_registration_fee=_num(data, "buy_registration"),
        annual_depreciation_rate=_num(data, "depreciation_rate", 0.15),
    )
    lease_inputs = LeaseInputs(
        due_at_signing=_num(data, "lease_due_at_signing"),
        monthly_payment=_num(data, "lease_monthly"),
        lease_term_months=int(_num(data, "lease_term_months")),
        disposition_fee=_num(data, "lease_disposition_fee"),
        mileage_overage_fee=_num(data, "lease_mileage_fee"),
        annual_insurance=_num(data, "lease_insurance"),
        annual_maintenance=_num(data, "lease_maintenance"),
        annual_registration_fee=_num(data, "lease_registration"),
    )
    horizon_months = int(_num(data, "horizon_months"))

    try:
        result = compare_lease_vs_buy(buy_inputs, lease_inputs, horizon_months)
    except (ValueError, ZeroDivisionError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "horizon_months": result.horizon_months,
            "buy": asdict(result.buy),
            "lease": asdict(result.lease),
            "cheaper_option": result.cheaper_option,
            "savings": result.savings,
        }
    )


@app.route("/api/debt-vs-invest", methods=["POST"])
def api_debt_vs_invest():
    data = request.get_json(force=True)

    inputs = DebtVsInvestInputs(
        debt_balance=_num(data, "debt_balance"),
        debt_apr=_num(data, "debt_apr"),
        minimum_payment=_num(data, "minimum_payment"),
        extra_amount=_num(data, "extra_amount"),
        expected_annual_return=_num(data, "expected_return"),
    )
    horizon_months = int(_num(data, "horizon_months"))

    try:
        result = compare_debt_vs_invest(inputs, horizon_months)
    except (ValueError, ZeroDivisionError) as exc:
        return jsonify({"error": str(exc)}), 400

    def scenario_dict(scenario):
        d = asdict(scenario)
        d.pop("investment_contributions", None)
        return d

    return jsonify(
        {
            "horizon_months": result.horizon_months,
            "pay_off_debt_first": scenario_dict(result.pay_off_debt_first),
            "invest_now": scenario_dict(result.invest_now),
            "better_option": result.better_option,
            "net_worth_difference": result.net_worth_difference,
            "breakeven_return_rate": result.breakeven_return_rate,
        }
    )


@app.route("/api/job-offer", methods=["POST"])
def api_job_offer():
    data = request.get_json(force=True)
    raw_offers = data.get("offers", [])

    try:
        offers = [
            JobOffer(
                label=o.get("label") or f"Offer {i + 1}",
                state=o["state"],
                gross_salary=_num(o, "gross_salary"),
                signing_bonus=_num(o, "signing_bonus"),
                relocation_assistance=_num(o, "relocation_assistance"),
            )
            for i, o in enumerate(raw_offers)
        ]
        comparison = compare_offers(offers)
    except (ValueError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 400

    results = []
    for r in comparison.results:
        results.append(
            {
                "label": r.label,
                "state": r.state,
                "take_home": asdict(r.take_home),
                "first_year_cash": r.first_year_cash,
                "cost_of_living_index": r.cost_of_living_index,
                "col_adjusted_net_annual": r.col_adjusted_net_annual,
            }
        )

    return jsonify(
        {
            "results": results,
            "best_by_raw_net_income": comparison.best_by_raw_net_income,
            "best_by_col_adjusted_income": comparison.best_by_col_adjusted_income,
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5060)
