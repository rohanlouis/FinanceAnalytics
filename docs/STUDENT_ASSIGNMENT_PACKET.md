# Student Assignment Packet: Personal Finance Analytics Web App

## Project Goal

Build a Python web application that lets a user upload transaction CSV files, clean and categorize transactions, view spending analytics, and generate simple monthly insights.

This is an 8-week project. Plan to spend about 8-10 hours per week.

## Required Tech Stack

- Python 3.11+
- FastAPI
- Jinja templates or another simple server-rendered UI approach
- SQLite
- pandas
- pytest
- Git and GitHub

Do not use React for version 1. The focus is Python, backend structure, data handling, and practical analytics.

## Final Deliverables

By the end of the project, your repository should include:

- Working web app
- SQLite-backed transaction storage
- CSV upload and validation
- Transaction create, read, update, and delete flows
- Auto-categorization rules
- Filters and search
- Analytics dashboard
- Monthly summary and simple insights
- CSV export
- Automated tests
- Synthetic demo data
- README with setup, run, test, and demo instructions
- Short final presentation

## Weekly Assignments

### Week 1: Product Definition and Setup

Build:
- Create a new GitHub repository.
- Write a README with project goal, target user, planned features, and setup notes.
- Define 6-8 user stories.
- Sketch 3 screens: upload page, transactions page, dashboard.
- Create synthetic CSV demo data with columns: `date`, `description`, `amount`, `category`.
- Create a basic FastAPI app with one working page.

Submit:
- GitHub repo link.
- README.
- Sample CSV file.
- Screenshot or sketch of the 3 screens.

Acceptance checklist:
- App runs locally.
- README explains what the project is.
- Demo CSV has at least 20 transactions.
- You can explain the user problem in 2 minutes.

### Week 2: Database and Transaction CRUD

Build:
- Add SQLite database storage.
- Create a transaction table.
- Build pages to list, add, edit, and delete transactions.
- Store date, description, amount, category, source file name, and created timestamp.

Submit:
- Working demo of manual transaction entry.
- Database schema notes in README or a separate design note.

Acceptance checklist:
- Added transactions persist after app restart.
- User can edit category or description.
- User can delete a transaction.
- Amounts support both income and expenses.

### Week 3: CSV Upload and Data Cleaning

Build:
- Add CSV upload.
- Parse CSV files using pandas.
- Validate required columns.
- Validate date, amount, and description values.
- Save valid rows to the database.
- Show useful errors for invalid files.

Submit:
- Valid sample CSV.
- At least 2 invalid test CSV examples or written invalid cases.
- Short note documenting duplicate upload behavior.

Acceptance checklist:
- Valid CSV imports successfully.
- Missing required columns show a clear error.
- Bad dates or amounts are handled.
- Duplicate upload behavior is documented.

### Week 4: Categorization and Filtering

Build:
- Add auto-categorization rules.
- Add manual category override.
- Add filters by date range, category, and description search.

Minimum categorization rules:
- `STARBUCKS`, `MCDONALD`, `RESTAURANT` -> Food
- `SHELL`, `BP`, `EXXON` -> Gas
- `AMAZON`, `WALMART`, `TARGET` -> Shopping

Submit:
- Demo showing upload with auto-categorization.
- Demo showing manual category correction.
- Notes explaining where rules live and how they are applied.

Acceptance checklist:
- Uploaded transactions receive categories when rules match.
- Manual category changes are saved.
- Filters work together.
- Search works by description.

### Week 5: Analytics Dashboard

Build:
- Dashboard with monthly spending total.
- Spending by category.
- Top 5 merchants or descriptions.
- Income vs expenses when both exist.
- At least 2 charts.

Submit:
- Dashboard screenshot.
- Explanation of how totals are calculated.

Acceptance checklist:
- Dashboard updates from database data.
- Charts have clear labels.
- User can filter dashboard by month.
- Empty data states are handled cleanly.

### Week 6: Insights and Reports

Build:
- Generate at least 4 simple insights.
- Add monthly summary page.
- Add CSV export for filtered transactions.

Example insights:
- Largest spending category.
- Number of transactions over $100.
- Spending increased or decreased from previous month.
- Total income and expenses for the selected month.

Submit:
- Demo of insights with synthetic data.
- Exported CSV example.

Acceptance checklist:
- At least 4 insights are generated.
- Insights handle missing data gracefully.
- Filtered export works.
- Monthly summary is readable.

### Week 7: Testing, Error Handling, and Polish

Build:
- Add pytest tests.
- Improve error messages.
- Improve README.
- Clean up UI layout.

Required tests:
- CSV parsing.
- Transaction validation.
- Categorization rules.
- Analytics calculations.

Submit:
- Test output.
- README update.
- Short note identifying least-tested area.

Acceptance checklist:
- Tests run with one command.
- At least 8 meaningful tests exist.
- README explains install, run, test, and demo data.
- No obvious broken flows remain.

### Week 8: Deployment, Demo, and Final Presentation

Build:
- Make the app easy to start from a clean setup.
- Prepare demo data.
- Prepare a 5-7 minute walkthrough.
- Write a final project reflection.

Submit:
- Final GitHub repo.
- Final README.
- Demo script or presentation outline.
- Reflection.

Acceptance checklist:
- Fresh setup instructions work.
- Demo shows upload, categorization, dashboard, insights, and export.
- README is portfolio-ready.
- Reflection explains what you built, what you learned, and what you would improve.

## Weekly Handoff Format

At the end of each week, submit:

```text
What works:
- ...

What is incomplete:
- ...

What blocked me:
- ...

What I learned:
- ...

GitHub commit or branch:
- ...
```

## Final Presentation Outline

Use this structure:

1. Problem and target user.
2. App walkthrough.
3. Data model and CSV import flow.
4. Analytics and insights.
5. Testing approach.
6. Hardest technical problem.
7. What you would improve in version 2.

