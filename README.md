# FinanceAnalytics

2. User Stories (6-8 Core Features)
User stories keep your development focused on user value rather than just writing code. Copy these into your project management tool or README:

CSV Upload: As a user, I want to upload a CSV file of my bank transactions so that I don't have to enter them manually.

Transaction View: As a user, I want to see a paginated list of all my transactions sorted by date so that I can review my recent spending history.

Manual Categorization: As a user, I want to manually change the category of a transaction if the system miscategorized it.

CRUD Operations: As a user, I want to add, edit, or delete individual transactions to fix missing or incorrect bank data.

Search & Filter: As a user, I want to filter transactions by date range, category, or search by description so I can find specific expenses.

Visual Analytics: As a user, I want to see a breakdown of my spending by category in a chart so I can identify where most of my money goes.

Monthly Insights: As a user, I want a simple summary showing my total income vs. total expenses and a flag if I overspent compared to last month.

Data Export: As a user, I want to export my filtered transactions back to a CSV file so I can use it in Excel or Google Sheets.



An 8-week engineering project focused on building a robust, localized Python web application to upload, clean, categorize, and analyze personal bank transactions. Built entirely with a Python-centric backend stack using FastAPI, SQLite, and pandas—omitting heavy JavaScript frameworks to focus strictly on clean data handling, server-side performance, and automated testing.

🎯 Project Goal
The goal of this project is to build a reliable, privacy-focused Minimum Viable Product (MVP) that allows individuals to bypass third-party financial tracking apps (which often sell user data) by hosting their own local financial analytics processor. The application will handle messy CSV bank statements, sanitize the data inputs, auto-categorize recurring merchants, and present insights cleanly using server-rendered HTML.

👥 Target User
Privacy-conscious individuals who want to audit their monthly cash flow without linking their live bank accounts to third-party aggregation APIs (like Plaid).

Developers or data enthusiasts looking for a lightweight, self-hosted option to customize their own transaction categorizations and logic rules.

🛠️ Tech Stack
Language: Python 3.11+

Framework: FastAPI

UI Layer: Jinja2 Templates & Pico.css (A lightweight, classless CSS framework)

Database: SQLite (SQLAlchemy ORM)

Data Processing: pandas

Testing: pytest

Version Control: Git & GitHub

🚀 Planned Features & Roadmap
Core Features (MVP)
CSV File Processing: Drag-and-drop ingestion engine validating user-uploaded statements.

Transaction CRUD: A centralized interface to Create, Read, Update, and Delete individual transaction entries.

Dynamic Search & Filters: Filter down historical spending by category lists, date parameters, or text-matching patterns.

Rule-Based Engine: Automated script patterns to auto-tag merchants (e.g., matching "Starbucks" instantly to Food & Dining).

Analytics Dashboard: Visual representation of spending habits using key KPIs and client-side charts.

CSV Data Export: A feature to clean your data inside the app and re-export it back out as a unified flat file.

Database Schema Notes
Transactions table

The app uses a single SQLite table named transactions to store all manual entries.

Fields
id — primary key, auto-incremented integer
date — transaction date, stored as text in YYYY-MM-DD format
description — short text describing the transaction
amount — numeric value for the transaction amount
category — text label such as Food, Travel, Bills, etc.
source_file_name — original file name if the transaction came from an import
created_at — timestamp showing when the record was added to the database
Design notes
SQLite was chosen because it is lightweight and easy to use for a small app.
The table is designed to support creating, reading, updating, and deleting transactions.
created_at is automatically saved when a record is added.
source_file_name can be left blank for manually entered transactions.
The amount field should support decimal values so cents are preserved.
Example schema
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    source_file_name TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
Page behavior
List page: displays all transactions from the database
Add page: creates a new transaction
Edit page: updates an existing transaction
Delete page: removes a transaction from the database
