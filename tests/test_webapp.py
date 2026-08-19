import os
import sys

import pytest

WEBAPP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webapp")
sys.path.insert(0, WEBAPP_DIR)

from app import app  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200


def test_states_endpoint_lists_known_states(client):
    response = client.get("/api/states")
    assert response.status_code == 200
    states = response.get_json()
    assert any(entry["state"] == "Texas" for entry in states)


def test_lease_vs_buy_endpoint_returns_verdict(client):
    response = client.post(
        "/api/lease-vs-buy",
        json={
            "price": 30000,
            "down_payment": 3000,
            "loan_apr": 0.06,
            "loan_term_months": 60,
            "lease_due_at_signing": 2000,
            "lease_monthly": 350,
            "lease_term_months": 36,
            "horizon_months": 36,
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["cheaper_option"] in ("buy", "lease", "tie")


def test_lease_vs_buy_endpoint_rejects_bad_term(client):
    response = client.post(
        "/api/lease-vs-buy",
        json={
            "price": 30000,
            "loan_apr": 0.06,
            "loan_term_months": 0,
            "lease_due_at_signing": 2000,
            "lease_monthly": 350,
            "lease_term_months": 36,
            "horizon_months": 36,
        },
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_debt_vs_invest_endpoint_returns_verdict(client):
    response = client.post(
        "/api/debt-vs-invest",
        json={
            "debt_balance": 8000,
            "debt_apr": 0.22,
            "minimum_payment": 200,
            "extra_amount": 150,
            "expected_return": 0.07,
            "horizon_months": 48,
        },
    )
    assert response.status_code == 200
    assert response.get_json()["better_option"] in ("pay_off_debt_first", "invest_now", "tie")


def test_job_offer_endpoint_flips_winner_after_col_adjustment(client):
    response = client.post(
        "/api/job-offer",
        json={
            "offers": [
                {"label": "SF", "state": "California", "gross_salary": 150000},
                {"label": "Austin", "state": "Texas", "gross_salary": 120000},
            ]
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["best_by_raw_net_income"] == "SF"
    assert body["best_by_col_adjusted_income"] == "Austin"


def test_job_offer_endpoint_rejects_unknown_state(client):
    response = client.post(
        "/api/job-offer",
        json={"offers": [{"label": "X", "state": "Atlantis", "gross_salary": 100000}]},
    )
    assert response.status_code == 400
    assert "error" in response.get_json()
