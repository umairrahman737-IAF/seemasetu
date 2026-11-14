# SeemaSetu — Python + MySQL beginner project

This edition is designed around skills taught in a programming-language course: Python, SQL, basic HTML/CSS, and standard Python libraries. It uses Flask for routing, `mysql-connector-python` for database operations, and Werkzeug for password hashing. It does not require Tailwind, React, or SQLAlchemy.

## A. Install
Install Python 3.10+, VS Code, MySQL Server and MySQL Workbench.

## B. Create the database
Open MySQL Workbench and execute `sql/schema.sql`. Then create an app account using a strong unique password:
```sql
CREATE USER 'seemasetu_app'@'localhost' IDENTIFIED BY 'Replace-With-A-Strong-Password';
GRANT SELECT, INSERT, UPDATE, DELETE ON seemasetu.* TO 'seemasetu_app'@'localhost';
FLUSH PRIVILEGES;
```
For an existing installation, run `sql/migrate_issue_urgency.sql` instead of recreating the database schema.

## C. Set up Python in VS Code
Extract the ZIP and open the project folder in VS Code. Open Terminal > New Terminal:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If PowerShell blocks activation, use Command Prompt: `.venv\\Scripts\\activate.bat`.

## D. Configure .env
Copy `.env.example` to `.env` and enter the MySQL password you set. Never commit `.env` to GitHub.

## E. Create the first administrator
Run `python` in the VS Code terminal, then enter:
```python
from app import connect
from werkzeug.security import generate_password_hash
con = connect()
cur = con.cursor()
cur.execute("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,%s)", ("Project Admin","admin@example.com",generate_password_hash("Use-Your-Own-Demo-Password-123"),"admin"))
con.commit()
cur.close()
con.close()
exit()
```
Choose your own unique demo password. If `admin@example.com` already exists, use another email.

## F. Start the app
```bash
python app.py
```
Open `http://127.0.0.1:5000`. Sign in with the admin account created above.

## G. Test features
1. Create a report using a fictional location such as `Demo Sector A / Road R-01`.
   Choose an asset category, severity, and urgency; priority is capped at 5 and considers urgency, severity, risk keywords, and bridge/tunnel assets.
2. Open it, assign a team and change its status.
3. Create a work order and costs.
4. Add sample resources; set a minimum-stock level to test alerts.
5. Open Analytics, Users and Audit.
6. Create a viewer account and check that it cannot perform write actions.

## Deploy to Vercel
Vercel detects the Flask application in `app.py`. Before deploying, provision a hosted MySQL database that accepts connections from your deployment and run `sql/schema.sql` against it. Do not use `127.0.0.1` as the production database host.

Add these environment variables in the Vercel project settings for every environment you use:

- `SECRET_KEY`: a long, random secret value.
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: connection details for the hosted MySQL database.

The stylesheet is served from `public/static/`. Photo uploads on Vercel use temporary storage and may disappear between invocations; use persistent object storage before relying on photo uploads in production. The schema must be initialized separately; the app does not create database tables at startup.

## H. Map to your assignment
- System Design: draw architecture and ER diagrams using draw.io; document requirements, routes, data flow and trade-offs.
- RDBMS: five tables, primary/foreign keys, constraints, indexes, joins and a view are in `sql/schema.sql`. Add the specific transaction and stored procedure/trigger examples required by your rubric.
- DP-900: classify SQL rows as structured, JSON logs as semi-structured, and photos as unstructured; later configure Azure SQL, private Blob Storage and Power BI.
- Cloud Security: test roles, password hashing, parameterized SQL, environment secrets, HTTPS, firewall/network rules and audit logs.

## Important
The local app uses MySQL and local photo uploads. Azure SQL is not MySQL: it needs a compatible driver and SQL adaptations. Blob Storage integration and Power BI setup are later tasks. The priority score is a rule-based demonstration, not a trained ML model. This starter is for a student demo only; add CSRF protection, rate limiting, secure production configuration and thorough testing before public deployment. Use only fictional, non-sensitive infrastructure information.
