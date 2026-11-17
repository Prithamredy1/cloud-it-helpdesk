# Cloud-Based IT Help Desk & Incident Management System

A Flask + SQLite service desk where employees raise incidents and service requests, technicians investigate and log troubleshooting, and admins assign work and monitor SLA performance.

**Live demo:** _add your Vercel URL_ · Demo logins (password `Password123!`): `employee@`, `technician@`, `admin@company.com`

## Features
- Role-based access (employee / technician / admin), hashed passwords, CSRF protection, parameterised SQL
- Incidents (`INC-`) and service requests (`SR-`), priority from impact × urgency
- Lifecycle rules: resolving or closing needs resolution details; closed tickets can only be reopened
- SLA response/resolution tracking, overdue detection, compliance % calculated from real data
- Work logs, comments, knowledge base, audit log, admin dashboard with technician workload

## Run locally
```
pip install -r requirements.txt -r requirements-dev.txt
python app.py        # http://127.0.0.1:5000
pytest -q
```
Docker: `docker compose up --build` (SQLite lives in a named volume).

## Deploy to Vercel
1. Push this repo to GitHub. 2. In Vercel: Add New → Project → import it (Flask is auto-detected from `app.py`). 3. Add env var `SECRET_KEY`. 4. Deploy.

> On Vercel the SQLite file lives in `/tmp`, so demo data resets on cold starts. Fine for a demo; use PostgreSQL for real deployments.

## Not yet implemented
Admin screens for user/category/SLA management, business-hours SLA, email notifications, assignment history table (assignments are recorded in the audit log).
