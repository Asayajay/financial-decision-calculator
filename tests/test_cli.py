import csv

from findcalc.cli import main


def test_lease_vs_buy_command_runs_and_prints_verdict(capsys):
    exit_code = main([
        "lease-vs-buy",
        "--price", "30000",
        "--down-payment", "3000",
        "--loan-apr", "0.06",
        "--loan-term-months", "60",
        "--lease-due-at-signing", "2000",
        "--lease-monthly", "350",
        "--lease-term-months", "36",
        "--horizon-months", "36",
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "cheaper_option" in out


def test_lease_vs_buy_writes_csv(tmp_path, capsys):
    csv_path = tmp_path / "lease.csv"
    main([
        "lease-vs-buy",
        "--price", "30000",
        "--loan-apr", "0.06",
        "--loan-term-months", "60",
        "--lease-due-at-signing", "2000",
        "--lease-monthly", "350",
        "--lease-term-months", "36",
        "--horizon-months", "36",
        "--csv", str(csv_path),
    ])
    capsys.readouterr()
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    assert {row["scenario"] for row in rows} == {"buy", "lease"}


def test_debt_vs_invest_command_runs_and_prints_verdict(capsys):
    exit_code = main([
        "debt-vs-invest",
        "--debt-balance", "8000",
        "--debt-apr", "0.22",
        "--minimum-payment", "200",
        "--extra-amount", "150",
        "--expected-return", "0.07",
        "--horizon-months", "48",
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "better_option" in out


def test_job_offer_command_runs_with_multiple_offers(capsys):
    exit_code = main([
        "job-offer",
        "--offer", "SF|California|150000",
        "--offer", "Austin|Texas|120000|5000",
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "best by cost-of-living-adjusted income" in out


def test_job_offer_command_rejects_malformed_offer_string(capsys):
    try:
        main(["job-offer", "--offer", "not-enough-parts"])
        assert False, "expected SystemExit from argparse"
    except SystemExit:
        pass


def test_cli_reports_unknown_state_as_clean_error(capsys):
    exit_code = main([
        "job-offer",
        "--offer", "Nowhere|Atlantis|100000",
    ])
    err = capsys.readouterr().err
    assert exit_code == 1
    assert "Atlantis" in err
