# SeemaSetu — Border Infrastructure Monitoring and Maintenance System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.x-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%7C%20SQLite-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/Data-Fictional%20%26%20Unclassified-lightgrey.svg)](#)

> **Demonstration Notice:** SeemaSetu is developed strictly using **fictional, synthetic, and non-sensitive demonstration data**. It contains no classified coordinates, real military installation details, tactical defense information, or operational troop movements. It is designed for undergraduate academic demonstration in Python, relational database engineering, cloud computing, and cybersecurity.

---

## 🌟 Executive Summary

**SeemaSetu** (सीमा सेतु — *Bridge to the Border*) is a centralized web platform engineered to monitor, score, assign, and coordinate maintenance for civil infrastructure in India's border sectors.

In harsh high-altitude, desert, and riverine border corridors, damaged access roads, frozen borewells, failed security solar mast lights, and breached avalanche shelters cut off remote civilian communities and patrol lines. SeemaSetu provides:

1. **Role-Based Incident Reporting:** Field defect submissions with photos, sector categorization, and parameterized input sanitation.
2. **Deterministic Priority Scoring:** Objective multi-factor scoring combining severity, urgency, risk keywords, and critical infrastructure assets (bridges, tunnels).
3. **Work Order Management & Financial Governance:** Direct assignment of engineering units and contractors with start/target dates, non-negative budget validation, and budget vs. actual expenditure comparison.
4. **Logistics & Material Inventory Control:** Real-time depot stock tracking with low-stock warnings.
5. **Interactive Executive Dashboard & Analytics:** Real-time visual metrics, status distribution, and cost summaries.
6. **User Administration & RBAC:** Comprehensive administrative control panel to manage roles (`admin`, `engineer`, `maintenance`, `viewer`) and toggle account active status.
7. **Immutable Security Audit Trail:** Chronological record of administrative operations and status transitions with operator IDs.

---

## 🚀 Quick Start (Python + MySQL Basics)

This edition uses Flask for routing, `mysql-connector-python` for database operations, and Werkzeug for password hashing. It does not require external frontend frameworks.

### A. Install Prerequisites
Install Python 3.10+, VS Code, and MySQL Server (or MySQL Workbench).

### B. Create the Database
Open MySQL Workbench or your MySQL shell and execute `sql/schema.sql`. Then create an application user:

```sql
CREATE USER 'seemasetu_app'@'localhost' IDENTIFIED BY 'Replace-With-A-Strong-Password';
GRANT SELECT, INSERT, UPDATE, DELETE ON seemasetu.* TO 'seemasetu_app'@'localhost';
FLUSH PRIVILEGES;
```
*For existing installations upgrading schema urgency levels, execute `sql/migrate_issue_urgency.sql`.*

### C. Set up Virtual Environment & Dependencies
Open your project folder in VS Code terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
*(If PowerShell execution policies block script activation, use Command Prompt: `.venv\Scripts\activate.bat`)*

### D. Configure Environment (.env)
Copy `.env.example` to `.env` and fill in your database credentials:
```ini
SECRET_KEY=your-random-secret-key
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=seemasetu
DB_USER=seemasetu_app
DB_PASSWORD=your_mysql_password
```

### E. Create the First Administrator Account
Run `python` in your terminal and execute:
```python
from app import connect
from werkzeug.security import generate_password_hash
con = connect()
cur = con.cursor()
cur.execute("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,%s)", ("Project Admin","admin@example.com",generate_password_hash("Admin@123"),"admin"))
con.commit()
cur.close()
con.close()
exit()
```

### F. Start the Application
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your web browser and sign in with the administrator account.

---

## 🧪 Testing Features
1. **Create an Issue:** Report a defect using fictional sectors (e.g. `Demo Sector A / Road R-01`). Choose asset category, severity, and urgency.
2. **Work Orders:** Assign a team, set task descriptions, estimated cost, and actual cost.
3. **Logistics & Resources:** Add sample resources and set minimum stock levels to trigger low-stock alerts.
4. **Analytics & Audit:** Review status breakdowns, cost tracking, and chronological audit entries.
5. **Role-Based Access Control:** Create viewer accounts and verify that write/edit operations are restricted.

---

## ☁️ Deployment Guide (Vercel & Cloud Database)

Vercel detects the Flask application in `app.py`. Before deploying:
1. Provision a hosted MySQL database (such as TiDB Cloud Serverless, Aiven, or Azure Database for MySQL) that accepts inbound connections.
2. Run `sql/schema.sql` against your hosted database.
3. Configure these environment variables in your Vercel Project Settings:
   - `SECRET_KEY`: Cryptographically secure random secret
   - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Connection parameters
4. Stylesheets are served from `public/static/`. Photo uploads on serverless platforms use temporary storage; for persistent storage, connect to cloud object storage (e.g. Azure Blob Storage or AWS S3).

---

## 📚 Academic Documentation & Advanced Modular Architecture

For full BTech CSE / Academic major project documentation, including:
- Objectives and Scope
- Mermaid System Architecture & Data Flow Diagrams
- Mermaid Entity-Relationship (ER) Diagram
- DP-900 Cloud Data Classification
- OWASP Security Controls & Role-Permission Matrix
- Automated Test Suite (`test_seemasetu.py`)

Please refer to [`docs/ACADEMIC_DOCUMENTATION.md`](docs/ACADEMIC_DOCUMENTATION.md).
