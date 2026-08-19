/*
 * Frontend glue: tab switching, form -> fetch -> render for each of the
 * three calculators. All the actual math happens server-side in
 * src/findcalc; this file only shapes form data into JSON and renders
 * whatever the API sends back.
 */

const STATES = JSON.parse(document.getElementById("states-data").textContent);

function setupTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");

      document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
      document.getElementById(`panel-${btn.dataset.tab}`).classList.add("active");
    });
  });
}

function formToObject(form) {
  const data = {};
  new FormData(form).forEach((value, key) => {
    data[key] = value;
  });
  return data;
}

function renderError(container, message) {
  container.innerHTML = `<p class="error-banner">${message}</p>`;
}

function buildTable(caption, rows) {
  const table = document.createElement("table");
  table.className = "breakdown";
  const captionEl = document.createElement("caption");
  captionEl.textContent = caption;
  table.appendChild(captionEl);

  const tbody = document.createElement("tbody");
  rows.forEach(([label, value]) => {
    const tr = document.createElement("tr");
    const th = document.createElement("th");
    th.textContent = label;
    const td = document.createElement("td");
    td.textContent = typeof value === "number" ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : value;
    tr.append(th, td);
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  return table;
}

// ---------- Lease vs. buy ----------

document.getElementById("form-lease-vs-buy").addEventListener("submit", async (event) => {
  event.preventDefault();
  const container = document.getElementById("results-lease-vs-buy");
  const payload = formToObject(event.target);

  const response = await fetch("/api/lease-vs-buy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  if (!response.ok) {
    renderError(container, body.error);
    return;
  }

  container.innerHTML = "";
  const verdict = document.createElement("p");
  verdict.className = "verdict";
  verdict.innerHTML = `${body.cheaper_option === "tie" ? "Dead even" : capitalize(body.cheaper_option) + " wins"} by <span class="amount">$${Math.round(body.savings).toLocaleString()}</span> over ${body.horizon_months} months`;
  container.appendChild(verdict);

  const canvas = document.createElement("canvas");
  canvas.className = "chart";
  container.appendChild(canvas);
  drawComparisonChart(canvas, [
    { label: "Buy", value: body.buy.net_cost, highlight: body.cheaper_option === "buy", highlightLabel: "cheaper" },
    { label: "Lease", value: body.lease.net_cost, highlight: body.cheaper_option === "lease", highlightLabel: "cheaper" },
  ]);

  container.appendChild(
    buildTable("Buy", [
      ["Amount financed", body.buy.amount_financed],
      ["Sales tax paid", body.buy.sales_tax_paid],
      ["Monthly loan payment", body.buy.monthly_loan_payment],
      ["Total loan payments through horizon", body.buy.total_loan_payments_through_horizon],
      ["Total interest through horizon", body.buy.total_interest_through_horizon],
      ["Loan balance at horizon", body.buy.loan_balance_at_horizon],
      ["Estimated resale value at horizon", body.buy.estimated_resale_value_at_horizon],
      ["Net equity at horizon", body.buy.net_equity_at_horizon],
      ["Total insurance", body.buy.total_insurance],
      ["Total maintenance", body.buy.total_maintenance],
      ["Total registration", body.buy.total_registration],
      ["Total cash outflow", body.buy.total_cash_outflow],
      ["Net cost", body.buy.net_cost],
    ])
  );
  container.appendChild(
    buildTable("Lease", [
      ["Number of lease signings", body.lease.num_lease_signings],
      ["Total signing fees", body.lease.total_signing_fees],
      ["Total monthly payments", body.lease.total_monthly_payments],
      ["Total disposition fees", body.lease.total_disposition_fees],
      ["Total mileage overage fees", body.lease.total_mileage_overage_fees],
      ["Total insurance", body.lease.total_insurance],
      ["Total maintenance", body.lease.total_maintenance],
      ["Total registration", body.lease.total_registration],
      ["Net cost", body.lease.net_cost],
    ])
  );
});

// ---------- Debt vs. invest ----------

document.getElementById("form-debt-vs-invest").addEventListener("submit", async (event) => {
  event.preventDefault();
  const container = document.getElementById("results-debt-vs-invest");
  const payload = formToObject(event.target);

  const response = await fetch("/api/debt-vs-invest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  if (!response.ok) {
    renderError(container, body.error);
    return;
  }

  container.innerHTML = "";
  const verdict = document.createElement("p");
  verdict.className = "verdict";
  const label = body.better_option === "tie" ? "Dead even" : (body.better_option === "invest_now" ? "Investing" : "Paying off debt first") + " wins";
  verdict.innerHTML = `${label} by <span class="amount">$${Math.round(body.net_worth_difference).toLocaleString()}</span> in net worth after ${body.horizon_months} months`;
  container.appendChild(verdict);

  const note = document.createElement("p");
  note.className = "placeholder";
  note.textContent = `Breakeven: investing beats paying off debt once expected return clears the debt's ${(body.breakeven_return_rate * 100).toFixed(2)}% APR (ignoring risk, taxes, and the value of being debt-free).`;
  container.appendChild(note);

  const canvas = document.createElement("canvas");
  canvas.className = "chart";
  container.appendChild(canvas);
  drawComparisonChart(canvas, [
    { label: "Pay off debt first", value: body.pay_off_debt_first.net_worth_at_horizon, highlight: body.better_option === "pay_off_debt_first" },
    { label: "Invest now", value: body.invest_now.net_worth_at_horizon, highlight: body.better_option === "invest_now" },
  ]);

  container.appendChild(
    buildTable("Pay off debt first", [
      ["Debt payoff month", body.pay_off_debt_first.debt_payoff_month],
      ["Total interest paid", body.pay_off_debt_first.total_interest_paid],
      ["Investment value at horizon", body.pay_off_debt_first.investment_value_at_horizon],
      ["Remaining debt at horizon", body.pay_off_debt_first.remaining_debt_at_horizon],
      ["Net worth at horizon", body.pay_off_debt_first.net_worth_at_horizon],
    ])
  );
  container.appendChild(
    buildTable("Invest now", [
      ["Debt payoff month", body.invest_now.debt_payoff_month],
      ["Total interest paid", body.invest_now.total_interest_paid],
      ["Investment value at horizon", body.invest_now.investment_value_at_horizon],
      ["Remaining debt at horizon", body.invest_now.remaining_debt_at_horizon],
      ["Net worth at horizon", body.invest_now.net_worth_at_horizon],
    ])
  );
});

// ---------- Job offers ----------

let offerCount = 0;

function addOfferRow(defaults) {
  offerCount += 1;
  const wrapper = document.createElement("div");
  wrapper.className = "offer-row";
  wrapper.dataset.index = offerCount;

  const options = STATES.map((s) => `<option value="${s}">${s}</option>`).join("");

  wrapper.innerHTML = `
    <label>Label <input type="text" name="label" value="${defaults.label}"></label>
    <label>State
      <select name="state">${options}</select>
    </label>
    <label>Gross salary ($) <input type="number" name="gross_salary" value="${defaults.salary}" required></label>
    <label>Signing bonus ($) <input type="number" name="signing_bonus" value="0"></label>
    <label>Relocation assistance ($) <input type="number" name="relocation_assistance" value="0"></label>
    <button type="button" class="remove-offer">Remove</button>
  `;
  wrapper.querySelector("select[name=state]").value = defaults.state;
  wrapper.querySelector(".remove-offer").addEventListener("click", () => wrapper.remove());

  document.getElementById("offer-rows").appendChild(wrapper);
}

document.getElementById("add-offer").addEventListener("click", () => {
  addOfferRow({ label: `Offer ${document.querySelectorAll(".offer-row").length + 1}`, state: "Texas", salary: 100000 });
});

document.getElementById("form-job-offer").addEventListener("submit", async (event) => {
  event.preventDefault();
  const container = document.getElementById("results-job-offer");

  const offers = Array.from(document.querySelectorAll(".offer-row")).map((row) => ({
    label: row.querySelector("[name=label]").value,
    state: row.querySelector("[name=state]").value,
    gross_salary: row.querySelector("[name=gross_salary]").value,
    signing_bonus: row.querySelector("[name=signing_bonus]").value,
    relocation_assistance: row.querySelector("[name=relocation_assistance]").value,
  }));

  const response = await fetch("/api/job-offer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ offers }),
  });
  const body = await response.json();
  if (!response.ok) {
    renderError(container, body.error);
    return;
  }

  container.innerHTML = "";
  const verdict = document.createElement("p");
  verdict.className = "verdict";
  verdict.innerHTML = `Best cost-of-living-adjusted offer: <span class="amount">${body.best_by_col_adjusted_income}</span> (best raw take-home: ${body.best_by_raw_net_income})`;
  container.appendChild(verdict);

  const canvas = document.createElement("canvas");
  canvas.className = "chart";
  container.appendChild(canvas);
  drawComparisonChart(
    canvas,
    body.results.map((r) => ({
      label: r.label,
      value: r.col_adjusted_net_annual,
      highlight: r.label === body.best_by_col_adjusted_income,
      highlightLabel: "best adjusted",
    }))
  );

  body.results.forEach((r) => {
    container.appendChild(
      buildTable(`${r.label} (${r.state})`, [
        ["Gross salary", r.take_home.gross_salary],
        ["Federal tax", r.take_home.federal_tax],
        ["State tax", r.take_home.state_tax],
        ["FICA", r.take_home.fica],
        ["Net annual", r.take_home.net_annual],
        ["Net monthly", r.take_home.net_monthly],
        ["First-year cash (incl. bonus/relocation)", r.first_year_cash],
        ["Cost of living index (US avg = 100)", r.cost_of_living_index],
        ["Cost-of-living-adjusted net annual", r.col_adjusted_net_annual],
      ])
    );
  });
});

function capitalize(word) {
  return word.charAt(0).toUpperCase() + word.slice(1);
}

setupTabs();
addOfferRow({ label: "Offer 1", state: "California", salary: 150000 });
addOfferRow({ label: "Offer 2", state: "Texas", salary: 120000 });
