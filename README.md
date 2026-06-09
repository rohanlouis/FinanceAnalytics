# FinanceAnalytics

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
