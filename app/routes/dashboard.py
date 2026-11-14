"""
Dashboard Blueprint for SeemaSetu.
Computes real-time operational metrics, infrastructure status distributions,
work order lifecycle figures, budget vs. actual expenditure analytics,
and serialized payloads for Chart.js interactive visualizations.
"""

import json
from flask import Blueprint, render_template, session
from app.db import query_db
from app.utils import login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """Public landing page introducing the border infrastructure project."""
    return render_template('index.html')


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Executive & Operational Analytics Dashboard."""
    # Issue KPIs
    total_issues = query_db("SELECT COUNT(*) as c FROM issues", one=True)['c']
    reported_count = query_db("SELECT COUNT(*) as c FROM issues WHERE status = 'Reported'", one=True)['c']
    under_review_count = query_db("SELECT COUNT(*) as c FROM issues WHERE status = 'Under Review'", one=True)['c']
    in_progress_count = query_db(
        "SELECT COUNT(*) as c FROM issues WHERE status IN ('Work Order Assigned', 'In Progress')",
        one=True
    )['c']
    resolved_count = query_db(
        "SELECT COUNT(*) as c FROM issues WHERE status IN ('Resolved', 'Closed')",
        one=True
    )['c']
    critical_priority_count = query_db(
        "SELECT COUNT(*) as c FROM issues WHERE priority_level = 'Critical' AND status NOT IN ('Resolved', 'Closed')",
        one=True
    )['c']

    # Work Order KPIs & Financial Cost Comparison
    total_work_orders = query_db("SELECT COUNT(*) as c FROM work_orders", one=True)['c']
    active_work_orders = query_db(
        "SELECT COUNT(*) as c FROM work_orders WHERE status IN ('Assigned', 'In Progress', 'Under Inspection')",
        one=True
    )['c']
    completed_work_orders = query_db(
        "SELECT COUNT(*) as c FROM work_orders WHERE status = 'Completed'",
        one=True
    )['c']

    # Budget vs. Actual Expenditure Analytics
    cost_summary = query_db(
        """
        SELECT 
            COALESCE(SUM(estimated_cost), 0) as total_estimated,
            COALESCE(SUM(actual_cost), 0) as total_actual
        FROM work_orders
        """,
        one=True
    )
    total_estimated_cost = float(cost_summary['total_estimated'] or 0)
    total_actual_cost = float(cost_summary['total_actual'] or 0)
    cost_variance = total_estimated_cost - total_actual_cost

    # Logistics & Inventory Alerts
    low_stock_resources = query_db(
        "SELECT * FROM resources WHERE quantity <= min_threshold ORDER BY quantity ASC"
    )

    # Issues by Infrastructure Category (Chart 1)
    cat_rows = query_db(
        "SELECT category, COUNT(*) as count FROM issues GROUP BY category ORDER BY count DESC"
    )
    categories = [r['category'] for r in cat_rows]
    category_counts = [r['count'] for r in cat_rows]

    # Issues by Rule-Based Priority Level (Chart 2)
    prio_rows = query_db("SELECT priority_level, COUNT(*) as count FROM issues GROUP BY priority_level")
    prio_dict = {r['priority_level']: r['count'] for r in prio_rows}
    priority_labels = ['Critical', 'High', 'Medium', 'Low']
    priority_data = [prio_dict.get(lvl, 0) for lvl in priority_labels]

    # Issues by Repair Lifecycle Status (Chart 3)
    status_rows = query_db("SELECT status, COUNT(*) as count FROM issues GROUP BY status")
    status_dict = {r['status']: r['count'] for r in status_rows}
    status_labels = ['Reported', 'Under Review', 'Work Order Assigned', 'In Progress', 'Resolved', 'Closed']
    status_data = [status_dict.get(st, 0) for st in status_labels]

    # Sector Incident Distribution
    sector_rows = query_db("SELECT sector, COUNT(*) as count FROM issues GROUP BY sector ORDER BY count DESC")

    # High-Priority Unresolved Incidents
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

    # Recent System Security & Operations Audit Feed
    recent_activity = query_db("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 8")

    # Overall Resolution Rate
    resolution_rate = round((resolved_count / total_issues * 100), 1) if total_issues > 0 else 0

    return render_template(
        'dashboard/index.html',
        total_issues=total_issues,
        reported_count=reported_count,
        under_review_count=under_review_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        critical_priority_count=critical_priority_count,
        total_work_orders=total_work_orders,
        active_work_orders=active_work_orders,
        completed_work_orders=completed_work_orders,
        total_estimated_cost=total_estimated_cost,
        total_actual_cost=total_actual_cost,
        cost_variance=cost_variance,
        low_stock_resources=low_stock_resources,
        urgent_issues=urgent_issues,
        recent_activity=recent_activity,
        resolution_rate=resolution_rate,
        sector_rows=sector_rows,
        # JSON payloads for Chart.js
        chart_categories=json.dumps(categories),
        chart_cat_counts=json.dumps(category_counts),
        chart_prio_labels=json.dumps(priority_labels),
        chart_prio_counts=json.dumps(priority_data),
        chart_status_labels=json.dumps(status_labels),
        chart_status_counts=json.dumps(status_data)
    )
