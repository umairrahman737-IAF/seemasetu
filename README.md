# SeemaSetu — Border Infrastructure Monitoring and Maintenance System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.x-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%7C%20SQLite-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/Data-Fictional%20%26%20Unclassified-lightgrey.svg)](#)

> **Important Notice:** SeemaSetu is built strictly using **fictional, unclassified demonstration data**. It contains no real military installations, classified coordinates, tactical defense information, or operational troop movements. It is designed to demonstrate practical web architecture, database engineering, priority ranking algorithms, and cloud deployment principles for civilian infrastructure maintenance.

---

## 🌟 Executive Summary

**SeemaSetu** (सीमा सेतु — *Bridge to the Border*) is a centralized web platform designed to monitor, score, assign, and track maintenance for critical civil infrastructure in remote border sectors. 

In harsh high-altitude, desert, or riverine border corridors, damaged access roads, frozen water borewells, failed security solar mast lights, or collapsed avalanche shelters can disrupt civilian mobility and remote settlement lifelines. SeemaSetu solves this by providing:

1. **Role-Based Incident Reporting** with photo uploads and parameterized input sanitation.
2. **Deterministic Rule-Based Priority Scoring (0–100)** to objectively rank urgent emergencies over routine defects.
3. **Work Order Dispatch** to assign specific civil engineering task forces and contractors.
4. **Logistics & Inventory Depots** tracking materials (cold-mix asphalt, Bailey bridge panels, solar inverters) with low-stock alerts.
5. **Interactive Executive Dashboard** with real-time Chart.js visual analytics and CSV exports.
6. **Immutable Audit Trail** for cybersecurity and administrative accountability.

---

## 🛠️ Technology Stack & Architecture

- **Backend:** Python 3.10+, Flask 3.1 (Application Factory pattern with modular Blueprints)
- **Database:** MySQL 8.0+ (with seamless zero-configuration SQLite fallback for local development and testing)
- **Database Interface:** Parameterized SQL queries (`execute_db` / `query_db`) preventing SQL Injection (CWE-89)
- **Security:** Werkzeug password hashing (`scrypt`), session-based CSRF protection, secure filename hashing
- **Frontend:** Semantic HTML5, Custom Border-Command CSS, Responsive Grid, Chart.js for data visualization
- **Deployment:** Vercel serverless (`vercel.json`), Gunicorn WSGI (`wsgi.py`), Azure App Service compatible

---

## 🔑 Demonstration Credentials

The database automatically seeds with three fictional demonstration accounts representing distinct roles:

| Role | Username | Password | Department / Description |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@123` | Border Infrastructure Command HQ (Full privileges, Work Orders, Inventory, Audit Logs) |
| **Field Officer** | `officer_sharma` | `Officer@123` | Sector Road & Bridge Division (Assign Work Orders, update progress, allocate materials) |
| **Field Reporter** | `reporter_amit` | `Reporter@123` | Field Patrol & Survey Unit (Submit incident reports, monitor tickets) |

---

## ⚖️ Rule-Based Priority Scoring Engine

SeemaSetu eliminates subjective guesswork by scoring every reported defect using a transparent formula from **0 to 100 points**:

$$\text{Priority Score} = \text{Severity (35)} + \text{Urgency (25)} + \text{Category Impact (25)} + \text{Weather Risk (15)}$$

### Factor Breakdown:

1. **Severity Factor (Max 35 pts):**
   - `Critical` (35 pts) &mdash; Complete structural collapse or total blockage of artery.
   - `High` (25 pts) &mdash; Major physical damage, single-lane restriction, partial failure.
   - `Medium` (15 pts) &mdash; Moderate defect (potholes, scouring, worn insulation).
   - `Low` (5 pts) &mdash; Cosmetic or minor wear.

2. **Urgency Factor (Max 25 pts):**
   - `Immediate` (25 pts) &mdash; Remote settlement or outpost cut off from survival supplies.
   - `High` (18 pts) &mdash; Essential transit impacted; alternative routes lengthy.
   - `Moderate` (10 pts) &mdash; Non-critical delays.
   - `Routine` (5 pts) &mdash; Scheduled maintenance cycle.

3. **Infrastructure Category Impact (Max 25 pts):**
   - `Roads & Bridges` (25 pts) &mdash; Lifeline supply connectivity in isolated terrain.
   - `Water Supply` (20 pts) &mdash; Drinking water borewells, filtration, storage tanks.
   - `Power & Lighting` (15 pts) &mdash; Security perimeter lighting, cold-climate heating.
   - `Communications` (15 pts) &mdash; Telemetry masts, disaster radio repeaters.
   - `Public Facilities` (15 pts) &mdash; Avalanche transit shelters, medical dispensaries.

4. **Weather / Environmental Vulnerability (Max 15 pts):**
   - `Severe/Imminent` (15 pts) &mdash; Active monsoon, freeze-thaw thaw, rockfall season.
   - `Moderate Risk` (10 pts) &mdash; Adverse seasonal weather conditions.
   - `Normal/Stable` (5 pts) &mdash; Clear weather, stable ground conditions.

### Priority Level Classification:
- **$\ge 75$ pts &rarr; Critical (Rank 1):** Immediate emergency team dispatch within 12–24 hours.
- **$55\text{--}74$ pts &rarr; High (Rank 2):** Work order scheduled within 48–72 hours.
- **$35\text{--}54$ pts &rarr; Medium (Rank 3):** Standard weekly maintenance queue.
- **$< 35$ pts &rarr; Low (Rank 4):** Routine periodic monitoring.

*A real-time Live Priority Preview calculator on the report form calculates this score dynamically via `/api/calculate-priority-preview` as dropdowns change!*

---

## 📂 Project Directory Structure

```text
seemasetu/
├── app/
│   ├── __init__.py          # Flask Application Factory & Custom Jinja Filters
│   ├── config.py            # Environment-driven configuration
│   ├── db.py                # Dual MySQL & SQLite abstraction layer (Parameterized)
│   ├── priority.py          # Rule-based priority scoring algorithm
│   ├── utils.py             # Security, CSRF, audit logging, & upload helpers
│   ├── routes/
│   │   ├── auth.py          # Authentication (Login, Register, Logout, Profile)
│   │   ├── dashboard.py     # Executive KPI metrics & Chart.js data
│   │   ├── issues.py        # Issue reporting, timeline, and CSV export
│   │   ├── work_orders.py   # Work order issuance & progress tracking
│   │   ├── resources.py     # Material inventory & stock alerts
│   │   ├── audit.py         # System security audit log browser
│   │   └── api.py           # JSON endpoints for live preview & metrics
│   ├── static/
│   │   ├── css/style.css    # Professional Border Operations design system
│   │   ├── js/main.js       # Live priority calculation & dynamic UI scripts
│   │   └── uploads/         # Uploaded field photographs (safe filenames)
│   └── templates/           # Semantic Jinja2 responsive HTML templates
├── database/
│   ├── schema.sql           # MySQL DDL table schemas
│   └── seed_data.sql        # Unclassified fictional demonstration data
├── .env.example             # Environment configuration blueprint
├── .gitignore               # Clean VCS ignore definitions
├── requirements.txt         # Production dependencies
├── run.py                   # Local development server entrypoint
├── vercel.json              # Vercel serverless deployment config
└── wsgi.py                  # Production WSGI server entrypoint
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed.
- (Optional) MySQL Server 8.0+ or cloud-hosted MySQL (TiDB / PlanetScale / Azure Database for MySQL).

### 2. Setup & Virtual Environment

```bash
# Navigate to the project directory
cd seemasetu

# Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

- **For Zero-Configuration Local Development (SQLite):**
  Leave `DB_TYPE=sqlite` in `.env`. The system will automatically generate `database/seemasetu.db` and populate all demonstration tables and records on first run!

- **For MySQL:**
  Set in `.env`:
  ```ini
  DB_TYPE=mysql
  DB_HOST=localhost
  DB_PORT=3306
  DB_USER=root
  DB_PASSWORD=your_password
  DB_NAME=seemasetu_db
  ```
  Create the database in MySQL:
  ```sql
  CREATE DATABASE seemasetu_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```
  The app will auto-apply `schema.sql` and `seed_data.sql` on startup, or you can import them manually:
  ```bash
  mysql -u root -p seemasetu_db < database/schema.sql
  mysql -u root -p seemasetu_db < database/seed_data.sql
  ```

### 4. Run the Local Development Server

```bash
python run.py
```

Open your browser at **`http://127.0.0.1:5000`** to access the SeemaSetu portal!

---

## 🛡️ Cybersecurity & Robustness Principles

1. **SQL Injection Defense:** All database interactions strictly utilize parameterized statements (`cursor.execute(sql, (arg1, arg2))`). Dynamic string concatenations are banned.
2. **Password Security:** Passwords stored exclusively as salted `scrypt` cryptographic hashes generated by Werkzeug.
3. **Cross-Site Request Forgery (CSRF):** Form submissions validate cryptographic session tokens (`validate_csrf`).
4. **File Upload Hardening:** Uploaded images are validated for whitelisted extensions (`.png`, `.jpg`, `.jpeg`, `.webp`), sanitized with `secure_filename`, uniquely renamed with timestamps, and restricted to a 5MB threshold.
5. **Role-Based Access Control (RBAC):** Route decorators `@login_required`, `@role_required`, and `@admin_required` prevent horizontal and vertical privilege escalation.
6. **Audit Trail:** Critical operations (`USER_LOGIN`, `ISSUE_REPORTED`, `STATUS_CHANGE`, `WORK_ORDER_CREATED`, `RESOURCE_ALLOCATED`) are recorded with user ID, IP address, and details.

---

## ☁️ Deployment Instructions (Vercel & Cloud)

### Deploying to Vercel:
1. Ensure your repository is pushed to GitHub.
2. Link your repository in the Vercel dashboard.
3. Set the following Environment Variables in Vercel:
   - `SECRET_KEY`: Long random string
   - `DB_TYPE`: `mysql`
   - `DB_HOST`: Hostname of cloud MySQL (e.g. TiDB Cloud Serverless or Aiven)
   - `DB_USER`: Database username
   - `DB_PASSWORD`: Database password
   - `DB_NAME`: Database name
   - `DB_PORT`: `3306` (or provider's port)
4. Deploy! Vercel will execute `wsgi.py` via the configuration in `vercel.json`.

---

## 🔮 Future Enhancements Roadmap
- **Azure Integration:** Direct migration to Azure Database for MySQL and Azure Blob Storage for photo archives.
- **Power BI / Grafana:** Direct analytics data connector for infrastructure uptime metrics.
- **Machine Learning Prioritization:** Predictive slope failure detection combining weather forecasts with soil moisture telemetry.
