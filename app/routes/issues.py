"""
Issues Blueprint for SeemaSetu.
Handles incident reporting, deterministic rule-based priority scoring,
multi-criteria filtering, issue detail views, status transitions,
attached field photographs, and CSV data exports.
"""

import csv
import io
import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    session, current_app, Response
)
from app.db import query_db, execute_db
from app.priority import calculate_priority
from app.utils import (
    login_required, role_required, log_audit, validate_csrf,
    save_uploaded_file
)

issues_bp = Blueprint('issues', __name__, url_prefix='/issues')

CATEGORIES = [
    'Roads & Bridges',
    'Water Supply',
    'Power & Lighting',
    'Communications',
    'Public Facilities'
]

SECTORS = [
    'Sector North-A (Zanskar Valley Corridor)',
    'Sector East-C (Lohit River Foothills)',
    'Sector West-D (Thar Border Staging)',
    'Sector Central-B (Niti High Pass Access)',
    'Sector North-East (Siang Civil Transit)'
]

SEVERITIES = ['Critical', 'High', 'Medium', 'Low']
URGENCIES = ['Immediate', 'High', 'Moderate', 'Routine']
WEATHER_CONDITIONS = ['Severe/Imminent', 'Moderate Risk', 'Normal/Stable']
STATUSES = ['Reported', 'Under Review', 'Work Order Assigned', 'In Progress', 'Resolved', 'Closed']


def generate_ticket_number():
    """Generate a clean sequential-like demonstration ticket number (e.g. SS-2026-0007)."""
    now = datetime.datetime.now()
    year = now.strftime('%Y')
    last_issue = query_db("SELECT id FROM issues ORDER BY id DESC LIMIT 1", one=True)
    next_id = (last_issue['id'] + 1) if last_issue else 1
    return f"SS-{year}-{next_id:04d}"


@issues_bp.route('/')
@login_required
def list_issues():
    """List, search, and filter reported infrastructure defects."""
    status = request.args.get('status', '').strip()
    category = request.args.get('category', '').strip()
    priority = request.args.get('priority', '').strip()
    sector = request.args.get('sector', '').strip()
    search = request.args.get('search', '').strip()

    query = """
        SELECT i.*, u.full_name as reporter_name
        FROM issues i
        JOIN users u ON i.reported_by = u.id
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND i.status = %s"
        params.append(status)
    if category:
        query += " AND i.category = %s"
        params.append(category)
    if priority:
        query += " AND i.priority_level = %s"
        params.append(priority)
    if sector:
        query += " AND i.sector = %s"
        params.append(sector)
    if search:
        query += " AND (i.title LIKE %s OR i.ticket_number LIKE %s OR i.location_name LIKE %s)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term])

    query += " ORDER BY i.priority_score DESC, i.created_at DESC"

    issues = query_db(query, tuple(params))

    return render_template(
        'issues/list.html',
        issues=issues,
        categories=CATEGORIES,
        sectors=SECTORS,
        statuses=STATUSES,
        priorities=['Critical', 'High', 'Medium', 'Low'],
        current_status=status,
        current_category=category,
        current_priority=priority,
        current_sector=sector,
        current_search=search
    )


@issues_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_issue():
    """Submit a new border infrastructure defect report with automatic priority calculation."""
    if request.method == 'POST':
        token = request.form.get('csrf_token')
        if not validate_csrf(token):
            flash('Invalid session token. Please submit again.', 'danger')
            return redirect(url_for('issues.create_issue'))

        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        sector = request.form.get('sector', '').strip()
        location_name = request.form.get('location_name', '').strip()
        coordinates = request.form.get('coordinates', '').strip()
        severity = request.form.get('severity', '').strip()
        urgency = request.form.get('urgency', '').strip()
        weather = request.form.get('weather_vulnerability', 'Moderate Risk').strip()
        description = request.form.get('description', '').strip()

        # Validation
        if not (title and category and sector and location_name and severity and urgency and description):
            flash('Please complete all mandatory report fields.', 'warning')
            return render_template(
                'issues/create.html',
                categories=CATEGORIES,
                sectors=SECTORS,
                severities=SEVERITIES,
                urgencies=URGENCIES,
                weather_conditions=WEATHER_CONDITIONS,
                form=request.form
            )

        # Handle file upload safely
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                upload_dir = current_app.config['UPLOAD_FOLDER']
                image_filename = save_uploaded_file(file, upload_dir)

        # Calculate Rule-Based Priority Score
        prio_result = calculate_priority(severity, urgency, category, weather)
        priority_score = prio_result['score']
        priority_level = prio_result['level']

        ticket_number = generate_ticket_number()
        user_id = session['user_id']

        issue_id = execute_db(
            """
            INSERT INTO issues (
                ticket_number, title, description, category, sector, location_name,
                coordinates, severity, urgency, weather_vulnerability, priority_score,
                priority_level, status, image_path, reported_by, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Reported', %s, %s, %s)
            """,
            (
                ticket_number, title, description, category, sector, location_name,
                coordinates, severity, urgency, weather, priority_score,
                priority_level, image_filename, user_id, datetime.datetime.now()
            )
        )

        # Timeline entry
        execute_db(
            """
            INSERT INTO issue_timeline (issue_id, user_id, action, new_status, remarks, created_at)
            VALUES (%s, %s, 'ISSUE_REPORTED', 'Reported', %s, %s)
            """,
            (
                issue_id, user_id,
                f"Defect reported with calculated priority score {priority_score} ({priority_level}).",
                datetime.datetime.now()
            )
        )

        log_audit(
            'ISSUE_REPORTED', 'Issue', ticket_number,
            f"Title: {title} | Sector: {sector} | Priority: {priority_level} ({priority_score}/100)"
        )

        flash(
            f"Issue ticket {ticket_number} submitted successfully! Priority calculated as {priority_level} (Score: {priority_score}/100).",
            'success'
        )
        return redirect(url_for('issues.detail', issue_id=issue_id))

    return render_template(
        'issues/create.html',
        categories=CATEGORIES,
        sectors=SECTORS,
        severities=SEVERITIES,
        urgencies=URGENCIES,
        weather_conditions=WEATHER_CONDITIONS,
        form={}
    )


@issues_bp.route('/<int:issue_id>')
@login_required
def detail(issue_id):
    """View detailed issue ticket, priority breakdown, and timeline history."""
    issue = query_db(
        """
        SELECT i.*, 
               u1.full_name as reporter_name, u1.department as reporter_dept, u1.badge_number as reporter_badge,
               u2.full_name as assigned_name
        FROM issues i
        JOIN users u1 ON i.reported_by = u1.id
        LEFT JOIN users u2 ON i.assigned_to = u2.id
        WHERE i.id = %s
        """,
        (issue_id,),
        one=True
    )
    if not issue:
        flash('Requested issue ticket was not found.', 'danger')
        return redirect(url_for('issues.list_issues'))

    timeline = query_db(
        """
        SELECT t.*, u.full_name as user_name, u.role as user_role
        FROM issue_timeline t
        JOIN users u ON t.user_id = u.id
        WHERE t.issue_id = %s
        ORDER BY t.created_at DESC
        """,
        (issue_id,)
    )

    work_order = query_db(
        "SELECT * FROM work_orders WHERE issue_id = %s",
        (issue_id,),
        one=True
    )

    prio_details = calculate_priority(
        issue['severity'],
        issue['urgency'],
        issue['category'],
        issue['weather_vulnerability']
    )

    # Qualified engineers/officers for ticket assignment
    officers = query_db("SELECT id, full_name, department, role FROM users WHERE role IN ('admin', 'engineer', 'officer') AND is_active = 1")

    return render_template(
        'issues/detail.html',
        issue=issue,
        timeline=timeline,
        work_order=work_order,
        prio_details=prio_details,
        statuses=STATUSES,
        officers=officers
    )


@issues_bp.route('/<int:issue_id>/update-status', methods=['POST'])
@login_required
@role_required('admin', 'engineer', 'maintenance')
def update_status(issue_id):
    """Update issue status, assigned personnel, and timeline remarks."""
    token = request.form.get('csrf_token')
    if not validate_csrf(token):
        flash('Security verification failed.', 'danger')
        return redirect(url_for('issues.detail', issue_id=issue_id))

    issue = query_db("SELECT * FROM issues WHERE id = %s", (issue_id,), one=True)
    if not issue:
        flash('Issue not found.', 'danger')
        return redirect(url_for('issues.list_issues'))

    new_status = request.form.get('status', '').strip()
    remarks = request.form.get('remarks', '').strip()
    assigned_to = request.form.get('assigned_to')

    if new_status not in STATUSES:
        flash('Invalid status transition.', 'warning')
        return redirect(url_for('issues.detail', issue_id=issue_id))

    old_status = issue['status']
    user_id = session['user_id']

    if assigned_to:
        execute_db(
            """
            UPDATE issues 
            SET status = %s, assigned_to = %s, updated_at = %s
            WHERE id = %s
            """,
            (new_status, int(assigned_to), datetime.datetime.now(), issue_id)
        )
    else:
        execute_db(
            """
            UPDATE issues 
            SET status = %s, updated_at = %s
            WHERE id = %s
            """,
            (new_status, datetime.datetime.now(), issue_id)
        )

    execute_db(
        """
        INSERT INTO issue_timeline (issue_id, user_id, action, previous_status, new_status, remarks, created_at)
        VALUES (%s, %s, 'STATUS_CHANGE', %s, %s, %s, %s)
        """,
        (issue_id, user_id, old_status, new_status, remarks or f"Status shifted from {old_status} to {new_status}.", datetime.datetime.now())
    )

    log_audit(
        'STATUS_CHANGE', 'Issue', issue['ticket_number'],
        f"Status changed from '{old_status}' to '{new_status}'. Remarks: {remarks}"
    )

    flash(f"Status for {issue['ticket_number']} updated to '{new_status}'.", 'success')
    return redirect(url_for('issues.detail', issue_id=issue_id))


@issues_bp.route('/<int:issue_id>/recalculate-priority', methods=['POST'])
@login_required
@role_required('admin', 'engineer')
def recalculate_priority(issue_id):
    """Recompute rule-based priority score when weather, urgency, or ground hazards change."""
    token = request.form.get('csrf_token')
    if not validate_csrf(token):
        flash('Security verification failed.', 'danger')
        return redirect(url_for('issues.detail', issue_id=issue_id))

    issue = query_db("SELECT * FROM issues WHERE id = %s", (issue_id,), one=True)
    if not issue:
        flash('Issue not found.', 'danger')
        return redirect(url_for('issues.list_issues'))

    new_severity = request.form.get('severity', issue['severity']).strip()
    new_urgency = request.form.get('urgency', issue['urgency']).strip()
    new_weather = request.form.get('weather_vulnerability', issue['weather_vulnerability']).strip()

    prio_result = calculate_priority(new_severity, new_urgency, issue['category'], new_weather)

    execute_db(
        """
        UPDATE issues 
        SET severity = %s, urgency = %s, weather_vulnerability = %s,
            priority_score = %s, priority_level = %s, updated_at = %s
        WHERE id = %s
        """,
        (
            new_severity, new_urgency, new_weather,
            prio_result['score'], prio_result['level'],
            datetime.datetime.now(), issue_id
        )
    )

    execute_db(
        """
        INSERT INTO issue_timeline (issue_id, user_id, action, remarks, created_at)
        VALUES (%s, %s, 'PRIORITY_UPDATED', %s, %s)
        """,
        (
            issue_id, session['user_id'],
            f"Rule-based re-scoring: Severity={new_severity}, Urgency={new_urgency}, Weather={new_weather} => Score: {prio_result['score']} ({prio_result['level']}).",
            datetime.datetime.now()
        )
    )

    log_audit(
        'PRIORITY_UPDATED', 'Issue', issue['ticket_number'],
        f"Re-scored to {prio_result['score']} ({prio_result['level']})"
    )

    flash(f"Priority re-calculated: Score is now {prio_result['score']} ({prio_result['level']}).", 'info')
    return redirect(url_for('issues.detail', issue_id=issue_id))


@issues_bp.route('/export/csv')
@login_required
def export_csv():
    """Export all infrastructure defect records to CSV for administrative and reporting briefings."""
    issues = query_db(
        """
        SELECT i.ticket_number, i.title, i.category, i.sector, i.location_name,
               i.severity, i.urgency, i.weather_vulnerability, i.priority_score,
               i.priority_level, i.status, u.full_name as reported_by, i.created_at
        FROM issues i
        JOIN users u ON i.reported_by = u.id
        ORDER BY i.priority_score DESC
        """
    )

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow([
        'Ticket Number', 'Title', 'Category', 'Sector', 'Location',
        'Severity', 'Urgency', 'Weather Risk', 'Priority Score',
        'Priority Level', 'Status', 'Reported By', 'Created At'
    ])
    for row in issues:
        cw.writerow([
            row['ticket_number'], row['title'], row['category'], row['sector'],
            row['location_name'], row['severity'], row['urgency'],
            row['weather_vulnerability'], row['priority_score'], row['priority_level'],
            row['status'], row['reported_by'], str(row['created_at'])
        ])

    output = Response(si.getvalue(), mimetype='text/csv')
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    output.headers["Content-Disposition"] = f"attachment; filename=seemasetu_issues_{timestamp}.csv"
    return output
