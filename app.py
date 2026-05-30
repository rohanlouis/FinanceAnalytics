from __future__ import annotations

import csv
import hashlib
import io
import os
import sqlite3
from html import escape
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs

import pandas as pd
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "finance_app.db"

app = FastAPI(title="Finance Tracker")


AUTO_CATEGORY_RULES = {
    "Food": ["STARBUCKS", "MCDONALD", "RESTAURANT"],
    "Gas": ["SHELL", "BP", "EXXON"],
    "Shopping": ["AMAZON", "WALMART", "TARGET"],
}


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_upper(value: Any) -> str:
    return normalize_text(value).upper()


async def read_form_fields(request: Request) -> dict[str, str]:
    body = await request.body()
    if not body:
        return {}
    parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def display_date(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    return text[:10]


def parse_amount(value: Any) -> float:
    text = normalize_text(value).replace("$", "").replace(",", "")
    if not text:
        raise ValueError("Amount is required")
    return float(text)


def parse_date(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        raise ValueError("Date is required")
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"Invalid date: {text}")
    return parsed.date().isoformat()


def auto_category(description: str, existing: str = "") -> str:
    if normalize_text(existing):
        return normalize_text(existing)
    desc = normalize_upper(description)
    for category, keywords in AUTO_CATEGORY_RULES.items():
        if any(keyword in desc for keyword in keywords):
            return category
    return "Uncategorized"


def row_hash(txn_date: str, description: str, amount: float, category: str) -> str:
    payload = "|".join([txn_date, description.strip(), f"{amount:.2f}", category.strip()])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                txn_date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                source_file TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                row_hash TEXT NOT NULL UNIQUE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_hash TEXT NOT NULL UNIQUE,
                uploaded_at TEXT NOT NULL,
                rows_imported INTEGER NOT NULL DEFAULT 0,
                rows_skipped INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def seed_demo_data() -> None:
    with get_conn() as conn:
        existing = conn.execute("SELECT COUNT(*) AS c FROM transactions").fetchone()["c"]
        if existing:
            return

    sample_rows = [
        ("2026-05-01", "Starbucks Coffee", -5.75, "", "demo.csv"),
        ("2026-05-02", "Shell Gas Station", -42.10, "", "demo.csv"),
        ("2026-05-03", "Amazon Marketplace", -68.20, "", "demo.csv"),
        ("2026-05-04", "Salary", 3200.00, "Income", "demo.csv"),
        ("2026-05-05", "Walmart Supercenter", -88.19, "", "demo.csv"),
        ("2026-05-06", "Local Restaurant", -54.33, "", "demo.csv"),
        ("2026-05-07", "Freelance Project", 450.00, "Income", "demo.csv"),
        ("2026-05-08", "Exxon Fuel", -36.44, "", "demo.csv"),
        ("2026-05-09", "Target", -124.78, "", "demo.csv"),
        ("2026-05-10", "Mcdonald Lunch", -12.09, "", "demo.csv"),
        ("2026-04-03", "Salary", 3200.00, "Income", "demo.csv"),
        ("2026-04-05", "Starbucks Coffee", -6.25, "", "demo.csv"),
        ("2026-04-07", "Rent", -1450.00, "Housing", "demo.csv"),
        ("2026-04-09", "Shell Gas Station", -39.88, "", "demo.csv"),
        ("2026-04-11", "Amazon Marketplace", -149.99, "", "demo.csv"),
        ("2026-04-13", "Bonus", 250.00, "Income", "demo.csv"),
        ("2026-04-15", "Restaurant Dinner", -74.12, "", "demo.csv"),
        ("2026-04-18", "Walmart Supercenter", -96.50, "", "demo.csv"),
        ("2026-04-20", "Electric Bill", -116.70, "Utilities", "demo.csv"),
        ("2026-04-22", "Target", -42.87, "", "demo.csv"),
    ]
    with get_conn() as conn:
        for txn_date, description, amount, category, source_file in sample_rows:
            resolved_category = auto_category(description, category)
            r_hash = row_hash(txn_date, description, amount, resolved_category)
            conn.execute(
                """
                INSERT OR IGNORE INTO transactions
                (txn_date, description, amount, category, source_file, created_at, updated_at, row_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (txn_date, description, amount, resolved_category, source_file, now_iso(), now_iso(), r_hash),
            )


def build_demo_csv() -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "description", "amount", "category"])
    rows = [
        ["2026-05-01", "Starbucks Coffee", "-5.75", ""],
        ["2026-05-02", "Shell Gas Station", "-42.10", ""],
        ["2026-05-03", "Amazon Marketplace", "-68.20", ""],
        ["2026-05-04", "Salary", "3200.00", "Income"],
        ["2026-05-05", "Walmart Supercenter", "-88.19", ""],
        ["2026-05-06", "Local Restaurant", "-54.33", ""],
        ["2026-05-07", "Freelance Project", "450.00", "Income"],
        ["2026-05-08", "Exxon Fuel", "-36.44", ""],
        ["2026-05-09", "Target", "-124.78", ""],
        ["2026-05-10", "Mcdonald Lunch", "-12.09", ""],
        ["2026-04-03", "Salary", "3200.00", "Income"],
        ["2026-04-05", "Starbucks Coffee", "-6.25", ""],
        ["2026-04-07", "Rent", "-1450.00", "Housing"],
        ["2026-04-09", "Shell Gas Station", "-39.88", ""],
        ["2026-04-11", "Amazon Marketplace", "-149.99", ""],
        ["2026-04-13", "Bonus", "250.00", "Income"],
        ["2026-04-15", "Restaurant Dinner", "-74.12", ""],
        ["2026-04-18", "Walmart Supercenter", "-96.50", ""],
        ["2026-04-20", "Electric Bill", "-116.70", "Utilities"],
        ["2026-04-22", "Target", "-42.87", ""],
    ]
    writer.writerows(rows)
    return buffer.getvalue()


def fetch_transactions(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    sql = "SELECT * FROM transactions WHERE 1=1"
    params: list[Any] = []
    if filters.get("month"):
        sql += " AND substr(txn_date, 1, 7) = ?"
        params.append(filters["month"])
    if filters.get("start"):
        sql += " AND txn_date >= ?"
        params.append(filters["start"])
    if filters.get("end"):
        sql += " AND txn_date <= ?"
        params.append(filters["end"])
    if filters.get("category") and filters["category"] != "All":
        sql += " AND category = ?"
        params.append(filters["category"])
    if filters.get("q"):
        sql += " AND LOWER(description) LIKE ?"
        params.append(f"%{filters['q'].lower()}%")
    sql += " ORDER BY txn_date DESC, id DESC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def get_transaction(txn_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM transactions WHERE id = ?", (txn_id,)).fetchone()
    return dict(row) if row else None


def distinct_categories() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM transactions ORDER BY category COLLATE NOCASE"
        ).fetchall()
    categories = [row["category"] for row in rows]
    if "All" not in categories:
        categories.insert(0, "All")
    return categories or ["All"]


def save_transaction(
    txn_date: str,
    description: str,
    amount: float,
    category: str,
    source_file: str = "manual",
) -> None:
    resolved_category = auto_category(description, category)
    r_hash = row_hash(txn_date, description, amount, resolved_category)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO transactions
            (txn_date, description, amount, category, source_file, created_at, updated_at, row_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (txn_date, description, amount, resolved_category, source_file, now_iso(), now_iso(), r_hash),
        )


def update_transaction(txn_id: int, txn_date: str, description: str, amount: float, category: str) -> None:
    resolved_category = auto_category(description, category)
    existing = get_transaction(txn_id)
    if not existing:
        raise ValueError("Transaction not found")
    r_hash = row_hash(txn_date, description, amount, resolved_category)
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE transactions
            SET txn_date = ?, description = ?, amount = ?, category = ?, updated_at = ?, row_hash = ?
            WHERE id = ?
            """,
            (txn_date, description, amount, resolved_category, now_iso(), r_hash, txn_id),
        )


def delete_transaction(txn_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))


def validate_columns(columns: Iterable[str]) -> list[str]:
    required = {"date", "description", "amount"}
    missing = sorted(required - set(c.strip().lower() for c in columns))
    return missing


def import_csv_bytes(file_name: str, data: bytes) -> tuple[int, int, list[str]]:
    file_hash = hashlib.sha256(data).hexdigest()
    with get_conn() as conn:
        existing_upload = conn.execute("SELECT 1 FROM uploads WHERE file_hash = ?", (file_hash,)).fetchone()
        if existing_upload:
            return 0, 0, [f"Duplicate upload skipped: {file_name}"]

    try:
        df = pd.read_csv(io.BytesIO(data))
    except Exception as exc:
        return 0, 0, [f"Could not read CSV: {exc}"]

    missing = validate_columns(df.columns)
    if missing:
        return 0, 0, [f"Missing required columns: {', '.join(missing)}"]

    df = df.fillna("")
    imported = 0
    skipped = 0
    errors: list[str] = []

    with get_conn() as conn:
        for index, row in df.iterrows():
            try:
                txn_date = parse_date(row["date"])
                description = normalize_text(row["description"])
                if not description:
                    raise ValueError("Description is required")
                amount = parse_amount(row["amount"])
                category = auto_category(description, normalize_text(row.get("category", "")))
                r_hash = row_hash(txn_date, description, amount, category)
                result = conn.execute(
                    """
                    INSERT OR IGNORE INTO transactions
                    (txn_date, description, amount, category, source_file, created_at, updated_at, row_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (txn_date, description, amount, category, file_name, now_iso(), now_iso(), r_hash),
                )
                if result.rowcount:
                    imported += 1
                else:
                    skipped += 1
            except Exception as exc:
                errors.append(f"Row {index + 2}: {exc}")

        conn.execute(
            """
            INSERT INTO uploads (file_name, file_hash, uploaded_at, rows_imported, rows_skipped)
            VALUES (?, ?, ?, ?, ?)
            """,
            (file_name, file_hash, now_iso(), imported, skipped),
        )

    return imported, skipped, errors


def month_key(value: str) -> str:
    return value[:7]


def month_options() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(txn_date, 1, 7) AS month FROM transactions ORDER BY month DESC"
        ).fetchall()
    return [row["month"] for row in rows]


def selected_month(value: str | None) -> str:
    if value and len(value) >= 7:
        return value[:7]
    months = month_options()
    if months:
        return months[0]
    return datetime.utcnow().strftime("%Y-%m")


def month_transactions(month: str) -> list[dict[str, Any]]:
    return fetch_transactions({"month": month})


def summarize_transactions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    expenses = [r for r in rows if float(r["amount"]) < 0]
    income = [r for r in rows if float(r["amount"]) > 0]
    expense_total = round(sum(abs(float(r["amount"])) for r in expenses), 2)
    income_total = round(sum(float(r["amount"]) for r in income), 2)
    net_total = round(income_total - expense_total, 2)
    category_spend: dict[str, float] = {}
    for row in expenses:
        category_spend[row["category"]] = category_spend.get(row["category"], 0.0) + abs(float(row["amount"]))
    merchant_spend: dict[str, float] = {}
    for row in expenses:
        key = row["description"]
        merchant_spend[key] = merchant_spend.get(key, 0.0) + abs(float(row["amount"]))
    return {
        "count": len(rows),
        "expenses_count": len(expenses),
        "income_count": len(income),
        "expense_total": expense_total,
        "income_total": income_total,
        "net_total": net_total,
        "category_spend": dict(sorted(category_spend.items(), key=lambda item: item[1], reverse=True)),
        "merchant_spend": dict(sorted(merchant_spend.items(), key=lambda item: item[1], reverse=True)),
    }


def previous_month(month: str) -> str:
    dt = datetime.strptime(f"{month}-01", "%Y-%m-%d")
    year = dt.year if dt.month > 1 else dt.year - 1
    m = dt.month - 1 if dt.month > 1 else 12
    return f"{year:04d}-{m:02d}"


def html_page(title: str, body: str, notice: str = "") -> HTMLResponse:
    style = """
    <style>
      :root {
        --bg: #ffffff;
        --panel: #ffffff;
        --panel-2: #f8fafc;
        --text: #000000;
        --muted: #222222;
        --accent: #2563eb;
        --accent-2: #16a34a;
        --danger: #b91c1c;
        --border: #d1d5db;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
      }
      a { color: var(--text); text-decoration: none; }
      a:hover { text-decoration: underline; }
      .shell { max-width: 1280px; margin: 0 auto; padding: 24px; }
      .topbar {
        display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; align-items: center;
        margin-bottom: 24px; padding: 18px 20px; background: #ffffff; border: 1px solid var(--border); border-radius: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,.06);
      }
      .brand { font-size: 20px; font-weight: 700; letter-spacing: .2px; }
      .nav { display: flex; flex-wrap: wrap; gap: 12px; }
      .nav a, .button, button {
        display: inline-flex; align-items: center; justify-content: center;
        padding: 10px 14px; border-radius: 12px; border: 1px solid var(--border);
        background: #ffffff;
        color: var(--text); font-weight: 600; cursor: pointer;
      }
      .nav a:hover, .button:hover, button:hover { border-color: var(--accent); background: #f8fafc; }
      .grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; }
      .card {
        background: #ffffff; border: 1px solid var(--border); border-radius: 20px;
        padding: 18px; box-shadow: 0 8px 24px rgba(0,0,0,.05);
      }
      .span-12 { grid-column: span 12; }
      .span-8 { grid-column: span 8; }
      .span-6 { grid-column: span 6; }
      .span-4 { grid-column: span 4; }
      .span-3 { grid-column: span 3; }
      h1, h2, h3 { margin: 0 0 12px 0; }
      h1 { font-size: 30px; }
      h2 { font-size: 22px; }
      h3 { font-size: 18px; }
      p { color: var(--text); line-height: 1.6; }
      .muted { color: var(--muted); }
      .notice {
        margin-bottom: 16px; padding: 12px 14px; border-radius: 14px; background: #eff6ff;
        border: 1px solid #93c5fd; color: var(--text);
      }
      .error {
        margin-bottom: 16px; padding: 12px 14px; border-radius: 14px; background: #fef2f2;
        border: 1px solid #fca5a5; color: var(--text);
      }
      .stats {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px;
      }
      .stat {
        padding: 16px; border-radius: 18px; background: #ffffff;
        border: 1px solid var(--border);
      }
      .stat .value { font-size: 26px; font-weight: 700; margin-top: 6px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
      th { color: var(--text); font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }
      input, select {
        width: 100%; padding: 10px 12px; border-radius: 12px; border: 1px solid var(--border);
        background: #ffffff; color: var(--text);
      }
      label { display: block; margin-bottom: 6px; font-size: 13px; color: var(--text); }
      .form-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 14px; }
      .field-6 { grid-column: span 6; }
      .field-4 { grid-column: span 4; }
      .field-3 { grid-column: span 3; }
      .field-12 { grid-column: span 12; }
      .actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
      .pill {
        display: inline-flex; padding: 4px 10px; border-radius: 999px;
        background: #f3f4f6; color: var(--text); font-size: 12px; font-weight: 700;
      }
      .chart-bar {
        display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
      }
      .chart-bar .label { width: 160px; flex: 0 0 160px; color: var(--text); font-size: 14px; }
      .chart-bar .track {
        height: 14px; border-radius: 999px; background: #e5e7eb; overflow: hidden; flex: 1;
      }
      .chart-bar .fill {
        height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--accent), var(--accent-2));
      }
      .chart-bar .value { width: 96px; text-align: right; font-variant-numeric: tabular-nums; }
      .summary-grid {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px;
      }
      .summary-item {
        padding: 16px; border: 1px solid var(--border); border-radius: 18px; background: #f9fafb;
      }
      .footer-note { margin-top: 16px; font-size: 13px; color: var(--muted); }
      .small { font-size: 13px; }
      @media (max-width: 860px) {
        .span-8, .span-6, .span-4, .span-3, .field-6, .field-4, .field-3 { grid-column: span 12; }
        .chart-bar .label { width: 120px; flex-basis: 120px; }
      }
    </style>
    """
    nav = """
    <div class="nav">
      <a href="/transactions">Transactions</a>
      <a href="/upload">Upload CSV</a>
      <a href="/transactions/new">Add Transaction</a>
      <a href="/dashboard">Dashboard</a>
      <a href="/insights">Insights</a>
      <a href="/sample.csv">Sample CSV</a>
    </div>
    """
    notice_html = f'<div class="notice">{notice}</div>' if notice else ""
    return HTMLResponse(
        f"""
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>{title}</title>
            {style}
          </head>
          <body>
            <div class="shell">
              <div class="topbar">
                <div>
                  <div class="brand">Finance Tracker</div>
      <div class="muted small">Upload CSVs, clean transactions, track spending, and export filtered data.</div>
                </div>
                {nav}
              </div>
              {notice_html}
              {body}
            </div>
          </body>
        </html>
        """
    )


def render_bar_chart(items: list[tuple[str, float]], color: str = "gradient") -> str:
    if not items:
        return "<p class='muted'>No data available.</p>"
    max_value = max(v for _, v in items) or 1
    bars = []
    for label, value in items:
        pct = min(100, (value / max_value) * 100)
        bars.append(
            f"""
            <div class="chart-bar">
              <div class="label">{escape(label)}</div>
              <div class="track"><div class="fill" style="width:{pct:.1f}%"></div></div>
              <div class="value">${value:,.2f}</div>
            </div>
            """
        )
    return "".join(bars)


def render_transactions_table(rows: list[dict[str, Any]], include_actions: bool = True) -> str:
    if not rows:
        return "<p class='muted'>No transactions found for the selected filters.</p>"
    header = """
    <tr>
      <th>Date</th>
      <th>Description</th>
      <th>Amount</th>
      <th>Category</th>
      <th>Source</th>
      <th>Updated</th>
      <th>Actions</th>
    </tr>
    """
    body_rows = []
    for row in rows:
        amount = float(row["amount"])
        amount_class = "style='font-weight:700; color:#15803d'" if amount >= 0 else "style='font-weight:700; color:#b91c1c'"
        actions = (
            f"""
            <a class="button" href="/transactions/{row['id']}/edit">Edit</a>
            <form method="post" action="/transactions/{row['id']}/delete" style="display:inline" onsubmit="return confirm('Delete this transaction?')">
              <button type="submit">Delete</button>
            </form>
            """
            if include_actions
            else ""
        )
        body_rows.append(
            f"""
            <tr>
              <td>{escape(row['txn_date'])}</td>
              <td>{escape(row['description'])}</td>
              <td {amount_class}>${amount:,.2f}</td>
              <td><span class="pill">{escape(row['category'])}</span></td>
              <td>{escape(row['source_file'])}</td>
              <td>{escape(display_date(row['updated_at']))}</td>
              <td><div class="actions">{actions}</div></td>
            </tr>
            """
        )
    return f"<table>{header}{''.join(body_rows)}</table>"


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    seed_demo_data()


@app.get("/", response_class=HTMLResponse)
def home() -> Response:
    return RedirectResponse("/transactions", status_code=302)


@app.get("/upload", response_class=HTMLResponse)
def upload_page(message: str | None = None) -> HTMLResponse:
    body = """
    <div class="grid">
      <div class="card span-8">
        <h1>Upload CSV</h1>
        <p>Import transaction files with columns: <code>date</code>, <code>description</code>, <code>amount</code>, and optional <code>category</code>. The browser reads the file locally and sends the CSV text to the server.</p>
        <form method="post" action="/upload">
          <div class="form-grid">
            <div class="field-12">
              <label for="file">CSV file</label>
              <input id="file" type="file" accept=".csv,text/csv" required />
              <input type="hidden" id="file_name" name="file_name" />
              <textarea id="csv_text" name="csv_text" hidden></textarea>
            </div>
            <div class="field-12">
              <button type="submit">Upload and Import</button>
            </div>
          </div>
        </form>
        <script>
          const fileInput = document.getElementById('file');
          const csvText = document.getElementById('csv_text');
          const fileName = document.getElementById('file_name');
          fileInput.addEventListener('change', async () => {
            const file = fileInput.files && fileInput.files[0];
            if (!file) return;
            fileName.value = file.name;
            csvText.value = await file.text();
          });
        </script>
      </div>
      <div class="card span-4">
        <h2>Import rules</h2>
        <ul>
          <li>Dates are validated and normalized to ISO format.</li>
          <li>Amounts support positive income and negative expenses.</li>
          <li>Descriptions are required.</li>
          <li>Duplicate file uploads are skipped using a file hash.</li>
        </ul>
        <p class="footer-note">You can download a built-in demo CSV from <a href="/sample.csv">/sample.csv</a>.</p>
      </div>
    </div>
    """
    return html_page("Upload CSV", body, notice=message or "")


@app.post("/upload", response_class=HTMLResponse)
async def upload_csv(request: Request) -> HTMLResponse:
    fields = await read_form_fields(request)
    file_name = fields.get("file_name") or "upload.csv"
    csv_text = fields.get("csv_text", "")
    if not csv_text.strip():
        return html_page("Upload results", "<div class='error'>No CSV content was provided.</div>", notice="Upload failed.")
    imported, skipped, errors = import_csv_bytes(file_name, csv_text.encode("utf-8"))
    notice = f"Imported {imported} rows, skipped {skipped} duplicates."
    if errors:
        body = "<div class='error'><strong>Some rows failed validation:</strong><ul>" + "".join(
            f"<li>{escape(error)}</li>" for error in errors[:20]
        ) + "</ul></div>"
        body += """
        <div class="card">
          <a class="button" href="/transactions">View transactions</a>
          <a class="button" href="/upload">Upload another file</a>
        </div>
        """
        return html_page("Upload results", body, notice=notice)
    return RedirectResponse(url=f"/transactions?message={notice}", status_code=303)


@app.get("/sample.csv")
def sample_csv() -> StreamingResponse:
    data = build_demo_csv()
    return StreamingResponse(
        iter([data]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="sample_transactions.csv"'},
    )


@app.get("/transactions", response_class=HTMLResponse)
def transactions_page(
    request: Request,
    q: str | None = None,
    category: str | None = None,
    start: str | None = None,
    end: str | None = None,
    message: str | None = None,
) -> HTMLResponse:
    filters = {"q": q, "category": category, "start": start, "end": end}
    rows = fetch_transactions(filters)
    cats = distinct_categories()
    safe_q = escape(q or "")
    safe_category = escape(category or "All")
    safe_start = escape(start or "")
    safe_end = escape(end or "")
    body = f"""
    <div class="grid">
      <div class="card span-12">
        <h1>Transactions</h1>
        <p>Filter, search, edit, and delete stored transactions. The same filters are reused by export and analytics.</p>
        <form method="get" action="/transactions">
          <div class="form-grid">
            <div class="field-3">
              <label for="q">Search description</label>
              <input id="q" name="q" value="{safe_q}" placeholder="coffee, rent, amazon..." />
            </div>
            <div class="field-3">
              <label for="category">Category</label>
              <select id="category" name="category">
                {''.join(f'<option value="{escape(c)}" {"selected" if c == (category or "All") else ""}>{escape(c)}</option>' for c in cats)}
              </select>
            </div>
            <div class="field-3">
              <label for="start">Start date</label>
              <input id="start" name="start" type="date" value="{safe_start}" />
            </div>
            <div class="field-3">
              <label for="end">End date</label>
              <input id="end" name="end" type="date" value="{safe_end}" />
            </div>
            <div class="field-12 actions">
              <button type="submit">Apply Filters</button>
              <a class="button" href="/transactions">Reset</a>
              <a class="button" href="/transactions/new">Add Transaction</a>
              <a class="button" href="/export.csv?q={safe_q}&category={safe_category}&start={safe_start}&end={safe_end}">Export CSV</a>
            </div>
          </div>
        </form>
      </div>
      <div class="card span-12">
        {render_transactions_table(rows)}
      </div>
    </div>
    """
    return html_page("Transactions", body, notice=message or request.query_params.get("message", ""))


@app.get("/transactions/new", response_class=HTMLResponse)
def new_transaction_page() -> HTMLResponse:
    body = """
    <div class="card">
      <h1>Add Transaction</h1>
      <form method="post" action="/transactions/new">
        <div class="form-grid">
          <div class="field-3">
            <label for="txn_date">Date</label>
            <input id="txn_date" name="txn_date" type="date" required />
          </div>
          <div class="field-6">
            <label for="description">Description</label>
            <input id="description" name="description" required />
          </div>
          <div class="field-3">
            <label for="amount">Amount</label>
            <input id="amount" name="amount" type="number" step="0.01" required />
          </div>
          <div class="field-6">
            <label for="category">Category</label>
            <input id="category" name="category" placeholder="Optional. Auto-categorized if blank." />
          </div>
          <div class="field-12">
            <button type="submit">Save Transaction</button>
          </div>
        </div>
      </form>
    </div>
    """
    return html_page("Add Transaction", body)


@app.post("/transactions/new", response_class=HTMLResponse)
async def create_transaction(request: Request) -> Response:
    try:
        fields = await read_form_fields(request)
        txn_date = fields.get("txn_date", "")
        description = fields.get("description", "")
        amount = fields.get("amount", "")
        category = fields.get("category", "")
        parsed_date = parse_date(txn_date)
        parsed_amount = parse_amount(amount)
        if not normalize_text(description):
            raise ValueError("Description is required")
        save_transaction(parsed_date, normalize_text(description), parsed_amount, category)
        return RedirectResponse("/transactions?message=Transaction%20saved", status_code=303)
    except Exception as exc:
        return html_page("Add Transaction", f"<div class='error'>{escape(str(exc))}</div>" + new_transaction_page().body.decode())


@app.get("/transactions/{txn_id}/edit", response_class=HTMLResponse)
def edit_transaction_page(txn_id: int) -> HTMLResponse:
    row = get_transaction(txn_id)
    if not row:
        return html_page("Not found", "<div class='error'>Transaction not found.</div>")
    body = f"""
    <div class="card">
      <h1>Edit Transaction</h1>
      <form method="post" action="/transactions/{txn_id}/edit">
        <div class="form-grid">
          <div class="field-3">
            <label for="txn_date">Date</label>
            <input id="txn_date" name="txn_date" type="date" value="{escape(row['txn_date'])}" required />
          </div>
          <div class="field-6">
            <label for="description">Description</label>
            <input id="description" name="description" value="{escape(row['description'])}" required />
          </div>
          <div class="field-3">
            <label for="amount">Amount</label>
            <input id="amount" name="amount" type="number" step="0.01" value="{escape(str(row['amount']))}" required />
          </div>
          <div class="field-6">
            <label for="category">Category</label>
            <input id="category" name="category" value="{escape(row['category'])}" />
          </div>
          <div class="field-12 actions">
            <button type="submit">Update Transaction</button>
            <a class="button" href="/transactions">Cancel</a>
          </div>
        </div>
      </form>
    </div>
    """
    return html_page("Edit Transaction", body)


@app.post("/transactions/{txn_id}/edit", response_class=HTMLResponse)
async def edit_transaction(txn_id: int, request: Request) -> Response:
    try:
        fields = await read_form_fields(request)
        txn_date = fields.get("txn_date", "")
        description = fields.get("description", "")
        amount = fields.get("amount", "")
        category = fields.get("category", "")
        update_transaction(txn_id, parse_date(txn_date), normalize_text(description), parse_amount(amount), category)
        return RedirectResponse("/transactions?message=Transaction%20updated", status_code=303)
    except Exception as exc:
        return html_page("Edit Transaction", f"<div class='error'>{escape(str(exc))}</div>" + edit_transaction_page(txn_id).body.decode())


@app.post("/transactions/{txn_id}/delete")
def remove_transaction(txn_id: int) -> Response:
    delete_transaction(txn_id)
    return RedirectResponse("/transactions?message=Transaction%20deleted", status_code=303)


def dashboard_metrics(month: str) -> dict[str, Any]:
    rows = month_transactions(month)
    summary = summarize_transactions(rows)
    prior_rows = month_transactions(previous_month(month))
    prior_summary = summarize_transactions(prior_rows)
    trend_change = round(summary["expense_total"] - prior_summary["expense_total"], 2)
    trend_label = "up" if trend_change > 0 else "down" if trend_change < 0 else "flat"
    return {
        **summary,
        "month": month,
        "prior_month": previous_month(month),
        "trend_change": abs(trend_change),
        "trend_label": trend_label,
        "category_spend_items": list(summary["category_spend"].items())[:8],
        "merchant_spend_items": list(summary["merchant_spend"].items())[:5],
    }


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(month: str | None = None) -> HTMLResponse:
    chosen_month = selected_month(month)
    metrics = dashboard_metrics(chosen_month)
    categories = metrics["category_spend_items"]
    merchants = metrics["merchant_spend_items"]
    body = f"""
    <div class="grid">
      <div class="card span-12">
        <h1>Dashboard</h1>
        <p>Monthly analytics from the SQLite transaction store. Choose a month to update totals and charts.</p>
        <form method="get" action="/dashboard">
          <div class="form-grid">
            <div class="field-3">
              <label for="month">Month</label>
              <input id="month" name="month" type="month" value="{chosen_month}" />
            </div>
            <div class="field-12">
              <button type="submit">Refresh</button>
            </div>
          </div>
        </form>
      </div>
      <div class="span-12 stats">
        <div class="stat"><div class="muted">Monthly spending</div><div class="value">${metrics['expense_total']:,.2f}</div></div>
        <div class="stat"><div class="muted">Income</div><div class="value">${metrics['income_total']:,.2f}</div></div>
        <div class="stat"><div class="muted">Net total</div><div class="value">${metrics['net_total']:,.2f}</div></div>
        <div class="stat"><div class="muted">Transactions</div><div class="value">{metrics['count']}</div></div>
      </div>
      <div class="card span-6">
        <h2>Spending by Category</h2>
        {render_bar_chart(categories)}
      </div>
      <div class="card span-6">
        <h2>Top 5 Merchants or Descriptions</h2>
        {render_bar_chart(merchants)}
      </div>
      <div class="card span-6">
        <h2>Income vs Expenses</h2>
        <div class="summary-grid">
          <div class="summary-item"><div class="muted">Income total</div><div class="value">${metrics['income_total']:,.2f}</div></div>
          <div class="summary-item"><div class="muted">Expense total</div><div class="value">${metrics['expense_total']:,.2f}</div></div>
        </div>
      </div>
      <div class="card span-6">
        <h2>Month-over-Month</h2>
        <p>The {metrics['trend_label']} change vs {metrics['prior_month']} is ${metrics['trend_change']:,.2f}.</p>
        <p class="footer-note">This comparison uses the previous month’s expense total, so the same dashboard month selector drives both views.</p>
      </div>
    </div>
    """
    return html_page("Dashboard", body)


@app.get("/insights", response_class=HTMLResponse)
def insights(month: str | None = None) -> HTMLResponse:
    chosen_month = selected_month(month)
    rows = month_transactions(chosen_month)
    summary = summarize_transactions(rows)
    prior_rows = month_transactions(previous_month(chosen_month))
    prior_summary = summarize_transactions(prior_rows)
    largest_category = next(iter(summary["category_spend"].items()), ("None", 0.0))
    over_100 = sum(1 for row in rows if abs(float(row["amount"])) > 100)
    spending_change = summary["expense_total"] - prior_summary["expense_total"]
    direction = "increased" if spending_change > 0 else "decreased" if spending_change < 0 else "did not change"
    body = f"""
    <div class="grid">
      <div class="card span-12">
        <h1>Insights and Monthly Summary</h1>
        <form method="get" action="/insights">
          <div class="form-grid">
            <div class="field-3">
              <label for="month">Month</label>
              <input id="month" name="month" type="month" value="{chosen_month}" />
            </div>
            <div class="field-12">
              <button type="submit">Update Insights</button>
            </div>
          </div>
        </form>
      </div>
      <div class="card span-6">
        <h2>Monthly Summary</h2>
        <div class="summary-grid">
          <div class="summary-item"><div class="muted">Total income</div><div class="value">${summary['income_total']:,.2f}</div></div>
          <div class="summary-item"><div class="muted">Total expenses</div><div class="value">${summary['expense_total']:,.2f}</div></div>
          <div class="summary-item"><div class="muted">Net total</div><div class="value">${summary['net_total']:,.2f}</div></div>
          <div class="summary-item"><div class="muted">Transactions</div><div class="value">{summary['count']}</div></div>
        </div>
      </div>
      <div class="card span-6">
        <h2>Generated Insights</h2>
        <ol>
          <li>Largest spending category: <strong>{largest_category[0]}</strong> at ${largest_category[1]:,.2f}.</li>
          <li>Transactions over $100: <strong>{over_100}</strong>.</li>
          <li>Spending {direction} vs previous month by <strong>${abs(spending_change):,.2f}</strong>.</li>
          <li>Total income and expenses for the month: <strong>${summary['income_total']:,.2f}</strong> income and <strong>${summary['expense_total']:,.2f}</strong> expenses.</li>
        </ol>
      </div>
      <div class="card span-12">
        <h2>Filtered Export</h2>
        <p>Export the same month as CSV using the current filters.</p>
        <a class="button" href="/export.csv?start={chosen_month}-01&end={chosen_month}-31">Download CSV</a>
      </div>
    </div>
    """
    return html_page("Insights", body)


@app.get("/export.csv")
def export_csv(
    q: str | None = None,
    category: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> Response:
    rows = fetch_transactions({"q": q, "category": category, "start": start, "end": end})
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "description", "amount", "category", "source_file", "created_at", "updated_at"])
    for row in rows:
        writer.writerow(
            [
                row["txn_date"],
                row["description"],
                row["amount"],
                row["category"],
                row["source_file"],
                row["created_at"],
                row["updated_at"],
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="filtered_transactions.csv"'},
    )


@app.get("/api/summary")
def api_summary(month: str | None = None) -> dict[str, Any]:
    chosen_month = selected_month(month)
    metrics = dashboard_metrics(chosen_month)
    return {
        "month": chosen_month,
        "summary": {
            "income_total": metrics["income_total"],
            "expense_total": metrics["expense_total"],
            "net_total": metrics["net_total"],
            "count": metrics["count"],
        },
        "categories": metrics["category_spend_items"],
        "merchants": metrics["merchant_spend_items"],
    }


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
