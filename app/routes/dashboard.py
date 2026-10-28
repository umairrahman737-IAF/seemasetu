import json
from flask import Blueprint, render_template, session
from app.db import query_db
from app.utils import login_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    # If not logged in, show the public landing/overview page or redirect to login
    # Having a crisp public landing page is great for demonstrating the project!
    return render_template('index.html')


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Key Metrics
    total_issues = query_db("SELECT COUNT(*) as c FROM issues", one=True)['c']
    reported_count = query_db("SELECT COUNT(*) as c FROM issues WHERE status = 'Reported'", one=True)['c']
    in_progress_count = query_db("SELECT COUNT(*) as c FROM issues WHERE status IN ('Work Order Assigned', 'In Progress')", one=True)['c']
    resolved_count = query_db("SELECT COUNT(*) as c FROM issues WHERE status IN ('Resolved', 'Closed')", one=True)['c']
    critical_priority_count = query_db("SELECT COUNT(*) as c FROM issues WHERE priority_level = 'Critical' AND status NOT IN ('Resolved', 'Closed')", one=True)['c']
    
    # Work Orders Metrics
    total_work_orders = query_db("SELECT COUNT(*) as c FROM work_orders", one=True)['c']
    active_work_orders = query_db("SELECT COUNT(*) as c FROM work_orders WHERE status IN ('Assigned', 'In Progress')", one=True)['c']
    
    # Low stock resources
    low_stock_resources = query_db(
        "SELECT * FROM resources WHERE quantity <= min_threshold ORDER BY quantity ASC"
    )
    
    # Issues by Category (for Chart)
    cat_rows = query_db(
        "SELECT category, COUNT(*) as count FROM issues GROUP BY category ORDER BY count DESC"
    )
    categories = [r['category'] for r in cat_rows]
    category_counts = [r['count'] for r in cat_rows]
    
    # Issues by Priority Level (for Chart)
    prio_rows = query_db(
        "SELECT priority_level, COUNT(*) as count FROM issues GROUP BY priority_level"
    )
    prio_dict = {r['priority_level']: r['count'] for r in prio_rows}
    priority_labels = ['Critical', 'High', 'Medium', 'Low']
    priority_data = [prio_dict.get(lvl, 0) for lvl in priority_labels]
    
    # Issues by Status (for Chart)
    status_rows = query_db(
        "SELECT status, COUNT(*) as count FROM issues GROUP BY status"
    )
    status_dict = {r['status']: r['count'] for r in status_rows}
    status_labels = ['Reported', 'Under Review', 'Work Order Assigned', 'In Progress', 'Resolved', 'Closed']
    status_data = [status_dict.get(st, 0) for st in status_labels]
    
    # Sector Breakdown
    sector_rows = query_db(
        "SELECT sector, COUNT(*) as count FROM issues GROUP BY sector ORDER BY count DESC"
    )
    
    # Recent high-priority issues
    urgent_issues = query_db(
        """
        SELECT i.*, u.full_name as reporter_name
        FROM issues i
        JOIN users u ON i.reported_by = u.id
        WHERE i.status NOT IN ('Resolved', 'Closed')
        ORDER BY i.priority_score DESC, i.created_at DESC
        LIMIT 6
        """
    )
    
    # Recent system audit activities
    recent_activity = query_db(
        "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 8"
    )
    
    # Resolution percentage
    resolution_rate = round((resolved_count / total_issues * 100), 1) if total_issues > 0 else 0
    
    return render_template(
        'dashboard/index.html',
        total_issues=total_issues,
        reported_count=reported_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        critical_priority_count=critical_priority_count,
        total_work_orders=total_work_orders,
        active_work_orders=active_work_orders,
        low_stock_resources=low_stock_resources,
        urgent_issues=urgent_issues,
        recent_activity=recent_activity,
        resolution_rate=resolution_rate,
        sector_rows=sector_rows,
        # JSON-serialized chart payloads
        chart_categories=json.dumps(categories),
        chart_cat_counts=json.dumps(category_counts),
        chart_prio_labels=json.dumps(priority_labels),
        chart_prio_counts=json.dumps(priority_data),
        chart_status_labels=json.dumps(status_labels),
        chart_status_counts=json.dumps(status_data)
    )
