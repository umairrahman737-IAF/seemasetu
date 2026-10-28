# SeemaSetu — Border Infrastructure Monitoring and Maintenance System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.x-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%7C%20SQLite-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/Data-Fictional%20%26%20Unclassified-lightgrey.svg)](#)
[![Tests](https://img.shields.io/badge/Tests-13%2F13%20Passing-brightgreen.svg)](#)

> **Demonstration Notice:** SeemaSetu is developed strictly using **fictional, synthetic, and non-sensitive demonstration data**. It contains no classified coordinates, real military installation details, tactical defense information, or operational troop movements. It is designed for undergraduate BTech Computer Science & Engineering academic demonstration in Python, relational database engineering, cloud computing, and cybersecurity.

---

## 🌟 Executive Summary

**SeemaSetu** (सीमा सेतु — *Bridge to the Border*) is a centralized web platform engineered to monitor, score, assign, and coordinate maintenance for civil infrastructure in India's border sectors. 

In harsh high-altitude, desert, and riverine border corridors, damaged access roads, frozen borewells, failed security solar mast lights, and breached avalanche shelters cut off remote civilian communities and patrol lines. SeemaSetu provides:

1. **Role-Based Incident Reporting:** Field defect submissions with photos, sector categorization, and parameterized input sanitation.
2. **Deterministic Rule-Based Priority Scoring (0–100):** Objective multi-factor scoring combining severity (35%), urgency (25%), category impact (25%), and weather/environmental risk (15%).
3. **Work Order Management & Financial Governance:** Direct assignment of engineering units and contractors with start/target dates, non-negative budget validation, and budget vs. actual expenditure comparison.
4. **Logistics & Material Inventory Control:** Real-time depot stock tracking (cold-mix polymer asphalt, Bailey bridge panels, solar inverters) with low-stock warnings and real-time order deductions.
5. **Interactive Executive Dashboard:** Real-time Chart.js visual analytics, sector distribution tables, and one-click administrative CSV data exports.
6. **User Administration & RBAC:** Comprehensive administrative control panel to manage roles (`admin`, `engineer`, `maintenance`, `viewer`) and toggle account active status.
7. **Secure Administrator Provisioning CLI (`create_admin.py`):** Repeatable, zero-hardcoded-credential administrator creation script.
8. **Immutable Security Audit Trail:** Chronological record of administrative operations and status transitions with operator IDs and IP addresses.

---

## 🛠️ Technology Stack & Architecture

- **Backend:** Python 3.10+, Flask 3.1 (Application Factory pattern with modular Blueprints)
- **Database:** MySQL 8.0+ (supported via `mysql-connector-python` and `PyMySQL`) with automatic zero-configuration SQLite fallback for local development and offline environments
- **Database Abstraction:** Parameterized SQL queries (`execute_db` / `query_db`) with transaction rollback, preventing SQL Injection (CWE-89)
- **Security:** Werkzeug password hashing (`scrypt`), session-based CSRF defense, secure filename hashing, and granular `@role_required` access control
- **Frontend:** Semantic HTML5, Border Operations Command CSS design system, Responsive Grid, and Chart.js for data visualization
- **Cloud Deployment:** Vercel serverless (`vercel.json`, `wsgi.py`, `api/index.py`) and cloud-hosted MySQL engines

---

## 🔑 Demonstration Credentials (Pre-Configured)

The system automatically seeds with three fictional demonstration accounts representing distinct roles:

| Role | Username | Password | Operational Capabilities |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@123` | Full system governance, user administration, work orders, logistics, audit logs. |
| **Lead Engineer** | `officer_sharma` | `Officer@123` | Issue status management, work order dispatch, priority re-scoring, material deduction. |
| **Field Reporter** | `reporter_amit` | `Reporter@123` | Defect ticket reporting, photo uploads, public dashboard inspection. |

---

## ⚖️ Deterministic Rule-Based Priority Scoring Model

SeemaSetu calculates an objective priority score from **0 to 100 points**:

$$\text{Priority Score} = \text{Severity (35)} + \text{Urgency (25)} + \text{Category Impact (25)} + \text{Weather Risk (15)}$$

### Factor Breakdown:
1. **Physical Severity (Max 35 pts):**
   - `Critical` (35 pts) &mdash; Complete structural collapse or total blockage of artery.
   - `High` (25 pts) &mdash; Major damage, single-lane restriction, partial failure.
   - `Medium` (15 pts) &mdash; Moderate defect (potholes, scouring, worn insulation).
   - `Low` (5 pts) &mdash; Cosmetic or minor wear.

2. **Operational Urgency (Max 25 pts):**
   - `Immediate` (25 pts) &mdash; Remote civilian community or patrol line cut off.
   - `High` (18 pts) &mdash; Essential transit impacted; lengthy detour.
   - `Moderate` (10 pts) &mdash; Non-critical delays; alternative path active.
   - `Routine` (5 pts) &mdash; Scheduled maintenance cycle.

3. **Infrastructure Category Impact (Max 25 pts):**
   - `Roads & Bridges` (25 pts) &mdash; Lifeline supply connectivity in isolated terrain.
   - `Water Supply` (20 pts) &mdash; Drinking water borewells, filtration, storage tanks.
   - `Power & Lighting` (15 pts) &mdash; Security perimeter lighting, cold-climate heating.
   - `Communications` (15 pts) &mdash; Telemetry masts, disaster radio repeaters.
   - `Public Facilities` (15 pts) &mdash; Avalanche transit shelters, medical dispensaries.

4. **Weather / Environmental Vulnerability (Max 15 pts):**
   - `Severe/Imminent` (15 pts) &mdash; Active monsoon, freeze-thaw rockfalls, flash flood alert.
   - `Moderate Risk` (10 pts) &mdash; Adverse seasonal weather conditions.
   - `Normal/Stable` (5 pts) &mdash; Clear weather, stable ground conditions.

### Priority Level Classification:
- **$\ge 75$ pts &rarr; Critical:** Immediate emergency team dispatch within 12–24 hours.
- **$55\text{--}74$ pts &rarr; High:** Work order scheduled within 48–72 hours.
- **$35\text{--}54$ pts &rarr; Medium:** Standard weekly maintenance queue.
- **$< 35$ pts &rarr; Low:** Routine periodic field monitoring.

---

## 📂 Project Directory Structure

```text
seemasetu/
├── app/
│   ├── __init__.py          # Flask Application Factory & Jinja filters
│   ├── config.py            # Environment-driven configuration
│   ├── db.py                # Dual MySQL & SQLite abstraction layer (Parameterized)
│   ├── priority.py          # Rule-based priority scoring algorithm
│   ├── utils.py             # RBAC decorators, CSRF, audit logging, & upload helpers
│   ├── routes/
│   │   ├── auth.py          # Authentication, Profile & User Administration
│   │   ├── dashboard.py     # Executive KPI metrics, cost comparisons & Chart.js data
│   │   ├── issues.py        # Issue reporting, timeline, status changes & CSV export
│   │   ├── work_orders.py   # Work order issuance, cost recording & progress tracking
│   │   ├── resources.py     # Material inventory, depot locations & stock alerts
│   │   ├── audit.py         # System security audit log browser
│   │   └── api.py           # JSON endpoints for live preview & metrics
│   ├── static/
│   │   ├── css/style.css    # Professional Border Operations design system
│   │   ├── js/main.js       # Live priority calculation & dynamic UI scripts
│   │   └── uploads/         # Uploaded field photographs (safe filenames)
│   └── templates/           # Semantic Jinja2 responsive HTML templates
├── api/
│   └── index.py             # Vercel zero-config serverless function handler
├── database/
│   ├── schema.sql           # MySQL DDL table schemas
│   └── seed_data.sql        # Unclassified fictional demonstration data
├── docs/
│   └── ACADEMIC_DOCUMENTATION.md # Full BTech CSE AI/ML Major Project Documentation
├── sql/
│   └── schema.sql           # Mirrored SQL schema for database deployment
├── .env.example             # Environment configuration blueprint
├── .gitignore               # Clean VCS ignore definitions
├── app.py                   # Primary application entry point
├── create_admin.py          # Secure interactive administrator provisioning CLI
├── requirements.txt         # Production dependencies
├── run.py                   # Development server launcher
├── test_seemasetu.py        # 13 automated unit & security tests
├── vercel.json              # Vercel serverless deployment config
└── wsgi.py                  # Production WSGI server entrypoint
```

---

## 🚀 Getting Started & Local Installation

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed.
- (Optional) MySQL Server 8.0+ or cloud-hosted MySQL (TiDB / PlanetScale / Azure Database for MySQL).

### 2. Setup & Virtual Environment

```bash
# Clone or navigate to the project repository
cd seemasetu

# Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

- **For Zero-Configuration Local Development (SQLite):**
  Leave `DB_TYPE=sqlite` in `.env`. The system will automatically generate `database/seemasetu.db` and populate all demonstration tables and records on first run!

- **For Production / Cloud MySQL:**
  Set in `.env`:
  ```ini
  DB_TYPE=mysql
  DB_HOST=your_mysql_host
  DB_PORT=3306
  DB_USER=your_db_user
  DB_PASSWORD=your_db_password
  DB_NAME=seemasetu_db
  ```
  Import schema:
  ```bash
  mysql -u your_user -p seemasetu_db < sql/schema.sql
  mysql -u your_user -p seemasetu_db < database/seed_data.sql
  ```

### 4. Provision Initial Administrator Account (CLI)

To create a custom administrator account without hardcoding credentials:

```bash
python create_admin.py
```
*Prompts for username, official email, full name, and password with masked input.*

### 5. Run the Local Development Server

```bash
python app.py
```
*(or `python run.py`)*

Open your browser at **`http://127.0.0.1:5000`** to access the SeemaSetu portal!

### 6. Run the Test Suite

```bash
python test_seemasetu.py
```
*Executes all 13 comprehensive unit, security, RBAC, and calculation tests.*

---

## ☁️ Deployment Guide (Vercel & Cloud Database)

### Step 1: Deploy MySQL Database
Because Vercel serverless functions cannot connect to local `127.0.0.1`, use a remotely accessible cloud MySQL instance:
- **TiDB Cloud Serverless** (Free tier MySQL-compatible cloud database)
- **Aiven for MySQL** (Free tier available)
- **Azure Database for MySQL Flexible Server**

Import `sql/schema.sql` into your remote database:
```bash
mysql -h <remote_host> -u <remote_user> -p <remote_db_name> < sql/schema.sql
mysql -h <remote_host> -u <remote_user> -p <remote_db_name> < database/seed_data.sql
```

### Step 2: Push Repository to GitHub
```bash
git add .
git commit -m "feat: complete SeemaSetu platform for production deployment"
git remote add origin https://github.com/<your_username>/SeemaSetu.git
git push -u origin master
```

### Step 3: Connect to Vercel
1. Sign in to your [Vercel Dashboard](https://vercel.com).
2. Click **Add New &rarr; Project** and import the `SeemaSetu` repository.
3. In **Environment Variables**, configure:
   - `SECRET_KEY`: Cryptographically random string (e.g. `openssl rand -hex 32`)
   - `DB_TYPE`: `mysql`
   - `DB_HOST`: Hostname of cloud MySQL instance
   - `DB_PORT`: `3306` (or provider's port)
   - `DB_NAME`: Database name
   - `DB_USER`: Database user
   - `DB_PASSWORD`: Database password
   - `SESSION_COOKIE_SECURE`: `True`
4. Click **Deploy**. Vercel will build and deploy the application via `vercel.json` and `wsgi.py`.

---

## 📚 Academic Major Project Documentation

For complete academic project documentation including:
- Objectives and Scope
- Functional and Non-Functional Requirements
- Mermaid System Architecture & Data Flow Diagrams
- Mermaid Entity-Relationship (ER) Diagram
- DP-900 Cloud Data Classification (Structured vs. Semi-Structured vs. Unstructured)
- OWASP Security Controls & Role-Permission Matrix
- Complete REST/Flask Route Specifications
- Testing Methodology & Detailed Test Results

Please refer to [`docs/ACADEMIC_DOCUMENTATION.md`](docs/ACADEMIC_DOCUMENTATION.md).
