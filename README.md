# Cloud-Based IT Help Desk & Incident Management System

**Portfolio Project for Technical Support Engineer / IT Help Desk / Service Desk roles**

A complete web-based IT Service Desk application demonstrating incident management, service request handling, SLA tracking, troubleshooting work logs, knowledge base, role-based access control, and administrative reporting.

Built with **Python, Flask, SQLite, Bootstrap, Docker** — zero cost stack.

---

## Live Demo

**Public Demo URL:** https://stupid-coats-clap.loca.lt

> Note: Free tunnel may sleep or require a one-time "Click to Continue" on first visit. Demo accounts are pre-seeded.

### Demo Accounts

| Role        | Email                      | Password   |
|-------------|----------------------------|------------|
| Admin       | admin@company.com          | Admin@123  |
| Technician  | technician@company.com     | Tech@123   |
| Employee    | employee@company.com       | Emp@123    |

---

## Features Implemented

### Core ITSM Functionality
- **Incident & Service Request** ticket management with auto-generated numbers (INC-xxxx / SR-xxxx)
- **Role-Based Access Control** (Employee, Technician, Administrator)
- **Ticket Lifecycle**: Open → Assigned → In Progress → Pending User / Third Party → Resolved → Closed / Reopened
- **Priority Matrix** based on Impact + Urgency (Critical / High / Medium / Low)
- **SLA Tracking**: Response & Resolution targets per priority with breach detection
- **Ticket Assignment** with history and workload visibility
- **Troubleshooting Work Logs**: Record diagnostic commands, findings, time spent (critical for support interviews)
- **Comments / Collaboration** between employees and technicians (internal notes supported)
- **Knowledge Base** with reusable troubleshooting articles
- **Admin Dashboard**: Ticket volume, status/priority breakdowns, technician workload, SLA compliance %
- **Audit Logging** of key actions
- **User Management** (create, activate/deactivate)

### Technical
- Secure password hashing (Werkzeug)
- Flask-Login sessions + CSRF protection
- SQLite with SQLAlchemy ORM
- Docker + Docker Compose ready
- Responsive Bootstrap 5 UI

---

## Tech Stack

| Layer       | Technology              |
|-------------|-------------------------|
| Backend     | Python 3.12, Flask 3    |
| ORM         | Flask-SQLAlchemy        |
| Auth        | Flask-Login, Werkzeug   |
| Frontend    | HTML5, Bootstrap 5, JS  |
| Database    | SQLite                  |
| Container   | Docker, Gunicorn        |
| CI concept  | GitHub Actions ready    |

---

## Project Structure

```
cloud-it-helpdesk/
├── app/
│   ├── auth/           # Login / logout
│   ├── employee/       # End-user ticket submission & tracking
│   ├── technician/     # Investigation, work logs, knowledge base
│   ├── admin/          # Full management, reports, users
│   ├── models/         # User, Ticket, WorkLog, SLA, KB, Audit
│   ├── templates/      # Role-based UI
│   └── static/
├── database/seed.py    # Demo users, categories, sample tickets & work logs
├── docs/               # Architecture & guides (expandable)
├── tests/              # Placeholder for unit tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── run.py
```

---

## Quick Start (Local)

```bash
git clone <your-repo-url>
cd cloud-it-helpdesk
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5000

### Docker

```bash
docker compose up --build
```

App available at http://localhost:5000. SQLite data persists via volume.

---

## Resume Bullet Points (copy-ready)

**Cloud-Based IT Help Desk & Incident Management System**  
*Python · Flask · SQLite · Bootstrap · Docker*

- Designed and developed a full-stack IT Service Desk platform supporting Incident and Service Request workflows aligned with ITIL practices.
- Implemented role-based authentication and authorization for Employees, Technicians, and Administrators with secure password hashing and session management.
- Built complete ticket lifecycle management including priority classification (impact/urgency matrix), assignment, status transitions, and SLA response/resolution tracking with breach detection.
- Developed troubleshooting work-log module enabling technicians to document diagnostic commands (ipconfig, ping, nslookup, Task Manager analysis, etc.), findings, and resolutions — demonstrating real L1 support documentation skills.
- Created knowledge base with reusable articles covering network, Windows performance, Outlook, VPN, and account issues.
- Implemented administrative dashboards showing ticket volume, category/priority distribution, technician workload, and SLA compliance percentage.
- Containerized the application with Docker and Gunicorn for consistent deployment; prepared GitHub Actions workflow for automated testing.

**GitHub:** *(add your repo URL after pushing)*  
**Live Demo:** https://stupid-coats-clap.loca.lt

---

## Sample Troubleshooting Scenarios Included

The seeded data and knowledge base cover realistic L1 scenarios:

1. Internet connected but no website access (DNS misconfiguration) — full work log with ipconfig / ping / nslookup
2. Outlook not receiving emails
3. Laptop running slowly (high CPU / startup items)
4. Printer offline
5. Account lockout concepts
6. VPN connectivity issues
7. Windows performance investigation patterns

These can be expanded into full incident reports for interview discussion.

---

## Industry Alignment

- **ITIL 4** concepts: Incident Management, Service Request Management, Service Desk, Knowledge Management, Service Level Management
- **Access control** principles (least privilege, RBAC)
- **Auditability** of support actions
- **OWASP-inspired** practices: password hashing, CSRF, input handling, session management

*This is a demonstration portfolio project, not a certified production system.*

---

## Future Enhancements (ideas)

- Business-hours aware SLA calculation
- Email notifications
- File attachments on tickets
- PostgreSQL for multi-user production
- Advanced reporting / CSV export
- Mobile-responsive polish

---

## License

MIT License — free to use for portfolio and learning purposes.

---

**Built as a Technical Support Engineer portfolio project — demonstrating both application development and practical IT support process understanding.**
