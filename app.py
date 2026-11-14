import os, secrets, tempfile
from pathlib import Path
from functools import wraps
import mysql.connector
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(PROJECT_ROOT / "public" / "static"))
secret_key = os.getenv("SECRET_KEY")
if os.getenv("VERCEL") == "1" and not secret_key:
    raise RuntimeError("Set SECRET_KEY in the Vercel project environment variables.")
app.secret_key = secret_key or secrets.token_hex(32)
UPLOADS = Path(os.getenv(
    "UPLOAD_DIR",
    str(Path(tempfile.gettempdir()) / "seemasetu-uploads")
    if os.getenv("VERCEL") == "1"
    else str(PROJECT_ROOT / "uploads"),
))
UPLOADS.mkdir(exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
ALLOWED = {"jpg", "jpeg", "png", "webp"}
ASSET_TYPES = ("Road", "Bridge", "Pothole", "Streetlight", "Water Supply", "Public Facility", "Slope", "Tunnel", "Other")
URGENCY_LEVELS = ("Routine", "Soon", "Urgent", "Immediate")

def connect():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "seemasetu_app"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "seemasetu"))

def rows(sql, params=()):
    con=connect(); cur=con.cursor(dictionary=True)
    try:
        cur.execute(sql, params); return cur.fetchall()
    finally:
        cur.close(); con.close()

def change(sql, params=()):
    con=connect(); cur=con.cursor()
    try:
        cur.execute(sql, params); con.commit(); return cur.lastrowid
    except Exception:
        con.rollback(); raise
    finally:
        cur.close(); con.close()

def signed_in():
    return session.get("user")

def require_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not signed_in(): return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def require_roles(*roles):
    def deco(fn):
        @wraps(fn)
        @require_login
        def wrapper(*args, **kwargs):
            if signed_in()["role"] not in roles: abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return deco

def audit(action, details=""):
    try:
        change("INSERT INTO audit_logs(user_id,action,details) VALUES(%s,%s,%s)",
               (signed_in()["id"] if signed_in() else None, action, details[:255]))
    except mysql.connector.Error:
        app.logger.exception("Could not write audit log")

def priority(severity, urgency, asset_type, description):
    score={"Low":1,"Medium":2,"High":3,"Critical":4}.get(severity,2)
    score += {"Routine":0,"Soon":1,"Urgent":2,"Immediate":3}.get(urgency,0)
    if any(w in description.lower() for w in ["blocked","collapse","unsafe","landslide"]): score+=1
    if asset_type in ["Bridge","Tunnel"]: score+=1
    return min(score,5)  # Rule-based starter, not a trained AI model.

@app.route("/")
@require_login
def dashboard():
    stats=rows("""SELECT COUNT(*) total,
      SUM(status IN ('Reported','Under Review','Approved','In Progress')) open_count,
      SUM(severity='Critical' AND status<>'Resolved') critical_count,
      SUM(status='Resolved') resolved_count FROM issues""")[0]
    recent=rows("SELECT * FROM issues ORDER BY created_at DESC LIMIT 6")
    return render_template("dashboard.html", stats=stats, recent=recent)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        found=rows("SELECT * FROM users WHERE email=%s AND active=1",(email,))
        if found and check_password_hash(found[0]["password_hash"],password):
            u=found[0]
            session["user"]={"id":u["id"],"name":u["name"],"email":u["email"],"role":u["role"]}
            audit("login","Successful login")
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.","error")
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
@require_login
def logout():
    audit("logout","Signed out"); session.clear()
    return redirect(url_for("login"))

@app.route("/issues")
@require_login
def issues():
    q=request.args.get("q","").strip(); status=request.args.get("status","")
    sql="SELECT * FROM issues WHERE 1=1"; p=[]
    if q:
        sql+=" AND (title LIKE %s OR description LIKE %s OR simulated_location LIKE %s)"
        like="%"+q+"%"; p += [like,like,like]
    valid=["Reported","Under Review","Approved","In Progress","Resolved","Rejected"]
    if status in valid: sql+=" AND status=%s"; p.append(status)
    sql+=" ORDER BY created_at DESC"
    return render_template("issues.html", issues=rows(sql,tuple(p)), q=q, selected=status)

@app.route("/issues/new", methods=["GET","POST"])
@require_roles("admin","engineer","maintenance")
def new_issue():
    if request.method=="POST":
        title=request.form.get("title","").strip()
        desc=request.form.get("description","").strip()
        asset=request.form.get("asset_type","")
        loc=request.form.get("simulated_location","").strip()
        sev=request.form.get("severity","Medium")
        urgency=request.form.get("urgency","Soon")
        if not title or not desc or not loc or asset not in ASSET_TYPES or urgency not in URGENCY_LEVELS or sev not in ["Low","Medium","High","Critical"]:
            flash("Please complete all fields correctly.","error")
            return render_template("issue_form.html")
        filename=None; f=request.files.get("photo")
        if f and f.filename:
            safe=secure_filename(f.filename)
            if "." not in safe or safe.rsplit(".",1)[1].lower() not in ALLOWED:
                flash("Photo must be JPG, PNG, or WEBP.","error")
                return render_template("issue_form.html")
            filename=secrets.token_hex(8)+"_"+safe; f.save(UPLOADS/filename)
        iid=change("""INSERT INTO issues(title,description,asset_type,simulated_location,severity,urgency,priority_score,status,photo_filename,reporter_id)
        VALUES(%s,%s,%s,%s,%s,%s,%s,'Reported',%s,%s)""",
        (title,desc,asset,loc,sev,urgency,priority(sev,urgency,asset,desc),filename,signed_in()["id"]))
        audit("issue_created",f"Issue #{iid}: {title}")
        flash("Issue created successfully.","success")
        return redirect(url_for("issue_detail",iid=iid))
    return render_template("issue_form.html")

@app.route("/issues/<int:iid>")
@require_login
def issue_detail(iid):
    found=rows("SELECT * FROM issues WHERE id=%s",(iid,))
    if not found: abort(404)
    return render_template("issue_detail.html", issue=found[0],
        orders=rows("SELECT * FROM work_orders WHERE issue_id=%s",(iid,)))

@app.route("/issues/<int:iid>/update",methods=["POST"])
@require_roles("admin","engineer")
def update_issue(iid):
    status=request.form.get("status",""); assigned=request.form.get("assigned_to","").strip()
    if status not in ["Reported","Under Review","Approved","In Progress","Resolved","Rejected"]: abort(400)
    change("UPDATE issues SET status=%s,assigned_to=%s WHERE id=%s",(status,assigned or None,iid))
    audit("issue_updated",f"Issue #{iid}: {status}")
    flash("Issue updated.","success")
    return redirect(url_for("issue_detail",iid=iid))

@app.route("/uploads/<path:filename>")
@require_login
def uploaded(filename):
    from flask import send_from_directory
    return send_from_directory(str(UPLOADS),filename)

@app.route("/work-orders",methods=["GET","POST"])
@require_roles("admin","engineer","maintenance","viewer")
def work_orders():
    if request.method=="POST":
        if signed_in()["role"] not in ["admin","engineer"]: abort(403)
        try:
            iid=int(request.form.get("issue_id","")); estimate=float(request.form.get("estimated_cost","0")); actual=float(request.form.get("actual_cost","0"))
        except ValueError:
            flash("Enter a valid issue and costs.","error"); return redirect(url_for("work_orders"))
        team=request.form.get("team_name","").strip(); task=request.form.get("task_description","").strip()
        if not rows("SELECT id FROM issues WHERE id=%s",(iid,)) or not team or not task or estimate<0 or actual<0:
            flash("Check all work order fields.","error"); return redirect(url_for("work_orders"))
        oid=change("INSERT INTO work_orders(issue_id,team_name,task_description,estimated_cost,actual_cost) VALUES(%s,%s,%s,%s,%s)",(iid,team,task,estimate,actual))
        audit("work_order_created",f"Work order #{oid}")
        flash("Work order created.","success"); return redirect(url_for("work_orders"))
    return render_template("work_orders.html",
      orders=rows("SELECT w.*,i.title issue_title FROM work_orders w JOIN issues i ON i.id=w.issue_id ORDER BY w.id DESC"),
      open_issues=rows("SELECT id,title FROM issues WHERE status<>'Resolved' ORDER BY id DESC"))

@app.route("/work-orders/<int:oid>/status",methods=["POST"])
@require_roles("admin","engineer","maintenance")
def update_work_order(oid):
    status=request.form.get("status","")
    if status not in ["Planned","Assigned","In Progress","Completed","Cancelled"]: abort(400)
    con=connect(); cur=con.cursor()
    try:
        cur.execute("UPDATE work_orders SET status=%s WHERE id=%s",(status,oid))
        if status=="Completed":
            cur.execute("SELECT issue_id FROM work_orders WHERE id=%s",(oid,)); row=cur.fetchone()
            if row: cur.execute("UPDATE issues SET status='Resolved' WHERE id=%s",(row[0],))
        con.commit()
    except Exception: con.rollback(); raise
    finally: cur.close(); con.close()
    audit("work_order_status",f"Work order #{oid}: {status}")
    flash("Status updated.","success"); return redirect(url_for("work_orders"))

@app.route("/resources",methods=["GET","POST"])
@require_roles("admin","engineer","maintenance","viewer")
def resources():
    if request.method=="POST":
        if signed_in()["role"] not in ["admin","engineer"]: abort(403)
        name=request.form.get("name","").strip(); cat=request.form.get("category","").strip()
        unit=request.form.get("unit","units").strip() or "units"
        try: qty=int(request.form.get("quantity","0")); minimum=int(request.form.get("minimum_quantity","0"))
        except ValueError:
            flash("Quantities must be whole numbers.","error"); return redirect(url_for("resources"))
        if not name or not cat or qty<0 or minimum<0: flash("Check resource details.","error")
        else:
            try:
                change("INSERT INTO resources(name,category,quantity,unit,minimum_quantity) VALUES(%s,%s,%s,%s,%s)",(name,cat,qty,unit,minimum))
                audit("resource_created",name); flash("Resource added.","success")
            except mysql.connector.IntegrityError: flash("That resource already exists.","error")
        return redirect(url_for("resources"))
    return render_template("resources.html", items=rows("SELECT * FROM resources ORDER BY name"))

@app.route("/resources/<int:rid>/quantity",methods=["POST"])
@require_roles("admin","engineer")
def update_resource(rid):
    try: qty=int(request.form.get("quantity",""))
    except ValueError: abort(400)
    if qty<0: abort(400)
    change("UPDATE resources SET quantity=%s WHERE id=%s",(qty,rid))
    audit("resource_updated",f"Resource #{rid} quantity {qty}")
    flash("Resource updated.","success"); return redirect(url_for("resources"))

@app.route("/analytics")
@require_login
def analytics():
    return render_template("analytics.html",
      by_status=rows("SELECT status,COUNT(*) total FROM issues GROUP BY status"),
      by_severity=rows("SELECT severity,COUNT(*) total FROM issues GROUP BY severity"),
      costs=rows("SELECT COALESCE(SUM(estimated_cost),0) estimated,COALESCE(SUM(actual_cost),0) actual FROM work_orders")[0],
      low_stock=rows("SELECT COUNT(*) total FROM resources WHERE quantity<=minimum_quantity")[0]["total"])

@app.route("/admin/users",methods=["GET","POST"])
@require_roles("admin")
def users():
    if request.method=="POST":
        name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower()
        password=request.form.get("password",""); role=request.form.get("role","")
        if not name or "@" not in email or len(password)<10 or role not in ["admin","engineer","maintenance","viewer"]:
            flash("Check details; password must have 10+ characters.","error")
        else:
            try:
                change("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,%s)",(name,email,generate_password_hash(password),role))
                audit("user_created",f"{email}: {role}"); flash("User created.","success")
            except mysql.connector.IntegrityError: flash("That email already exists.","error")
        return redirect(url_for("users"))
    return render_template("users.html", users=rows("SELECT id,name,email,role,active,created_at FROM users ORDER BY id DESC"))

@app.route("/audit")
@require_roles("admin")
def audit_page():
    return render_template("audit.html", logs=rows("SELECT a.*,u.email FROM audit_logs a LEFT JOIN users u ON a.user_id=u.id ORDER BY a.id DESC LIMIT 200"))

@app.errorhandler(403)
def forbidden(e): return render_template("error.html",code=403,message="You do not have permission to access this page."),403
@app.errorhandler(404)
def missing(e): return render_template("error.html",code=404,message="Page not found."),404

if __name__=="__main__":
    app.run(debug=True)  # Local development only, never production.
