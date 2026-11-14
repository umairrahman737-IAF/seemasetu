"""
Work Orders Blueprint for SeemaSetu.
Encompasses creation, progress updates, contractor assignment,
financial cost recording (budget vs. actual), and resource deductions.
"""

import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import query_db, execute_db
from app.utils import login_required, role_required, log_audit, validate_csrf

work_orders_bp = Blueprint('work_orders', __name__, url_prefix='/work-orders')

WO_STATUSES = ['Assigned', 'In Progress', 'Under Inspection', 'Completed', 'Delayed']


def generate_work_order_number():
    """Generate a clean sequential-like work order identifier (e.g. WO-2026-0004)."""
    year = datetime.datetime.now().strftime('%Y')
    last_wo = query_db("SELECT id FROM work_orders ORDER BY id DESC LIMIT 1", one=True)
    next_id = (last_wo['id'] + 1) if last_wo else 1
    return f"WO-{year}-{next_id:04d}"


@work_orders_bp.route('/')
@login_required
def list_work_orders():
    """Browse and filter work orders across sectors and units."""
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    query = """
        SELECT w.*, i.ticket_number, i.title as issue_title, i.priority_level, i.sector,
               u.full_name as creator_name
        FROM work_orders w
        JOIN issues i ON w.issue_id = i.id
        JOIN users u ON w.created_by = u.id
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND w.status = %s"
        params.append(status)
    if search:
        query += " AND (w.work_order_no LIKE %s OR w.contractor_or_unit LIKE %s OR w.lead_engineer LIKE %s OR i.ticket_number LIKE %s)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term, like_term])

    query += " ORDER BY w.created_at DESC"

    work_orders = query_db(query, tuple(params))

    return render_template(
        'work_orders/list.html',
        work_orders=work_orders,
        statuses=WO_STATUSES,
        current_status=status,
        current_search=search
    )


@work_orders_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'engineer')
def create():
    """Create a new maintenance work order linked to an active issue ticket."""
    issue_id = request.args.get('issue_id')

    # Available issues without an active open work order
    available_issues = query_db(
        """
        SELECT id, ticket_number, title, category, priority_level, sector
        FROM issues
        WHERE id NOT IN (SELECT issue_id FROM work_orders WHERE status NOT IN ('Completed', 'Closed'))
        ORDER BY priority_score DESC
        """
    )

    # Inventory materials for optional initial allocation
    resources = query_db("SELECT id, name, category, quantity, unit FROM resources WHERE quantity > 0")

    if request.method == 'POST':
        token = request.form.get('csrf_token')
        if not validate_csrf(token):
            flash('Security validation failed. Please try again.', 'danger')
            return redirect(url_for('work_orders.create'))

        selected_issue_id = request.form.get('issue_id')
        contractor = request.form.get('contractor_or_unit', '').strip()
        lead_engineer = request.form.get('lead_engineer', '').strip()
        estimated_cost_str = request.form.get('estimated_cost', '0').strip()
        start_date_str = request.form.get('start_date', '').strip()
        target_date_str = request.form.get('target_date', '').strip()
        scope_of_work = request.form.get('scope_of_work', '').strip()

        # Validation
        if not (selected_issue_id and contractor and lead_engineer and start_date_str and target_date_str and scope_of_work):
            flash('Please complete all mandatory work order fields.', 'warning')
            return render_template(
                'work_orders/create.html',
                available_issues=available_issues,
                resources=resources,
                preselected_issue_id=issue_id
            )

        try:
            estimated_cost = float(estimated_cost_str or 0)
            if estimated_cost < 0:
                flash('Estimated budget cannot be negative.', 'warning')
                return render_template(
                    'work_orders/create.html',
                    available_issues=available_issues,
                    resources=resources,
                    preselected_issue_id=issue_id
                )
        except ValueError:
            flash('Invalid estimated cost format.', 'warning')
            return render_template(
                'work_orders/create.html',
                available_issues=available_issues,
                resources=resources,
                preselected_issue_id=issue_id
            )

        # Date Sequence Validation
        try:
            d_start = datetime.date.fromisoformat(start_date_str)
            d_target = datetime.date.fromisoformat(target_date_str)
            if d_start > d_target:
                flash('Deployment start date cannot be after the target completion date.', 'warning')
                return render_template(
                    'work_orders/create.html',
                    available_issues=available_issues,
                    resources=resources,
                    preselected_issue_id=issue_id
                )
        except ValueError:
            pass

        wo_number = generate_work_order_number()
        user_id = session['user_id']

        # Insert Work Order
        wo_id = execute_db(
            """
            INSERT INTO work_orders (
                work_order_no, issue_id, contractor_or_unit, lead_engineer,
                estimated_cost, actual_cost, start_date, target_date,
                status, scope_of_work, progress_percentage, created_by, created_at
            ) VALUES (%s, %s, %s, %s, %s, 0.00, %s, %s, 'Assigned', %s, 0, %s, %s)
            """,
            (
                wo_number, selected_issue_id, contractor, lead_engineer,
                estimated_cost, start_date_str, target_date_str,
                scope_of_work, user_id, datetime.datetime.now()
            )
        )

        # Automatically transition linked issue status to 'Work Order Assigned'
        execute_db(
            """
            UPDATE issues 
            SET status = 'Work Order Assigned', updated_at = %s 
            WHERE id = %s AND status = 'Reported'
            """,
            (datetime.datetime.now(), selected_issue_id)
        )

        # Record event in issue audit timeline
        execute_db(
            """
            INSERT INTO issue_timeline (issue_id, user_id, action, previous_status, new_status, remarks, created_at)
            VALUES (%s, %s, 'WORK_ORDER_ISSUED', 'Reported', 'Work Order Assigned', %s, %s)
            """,
            (
                selected_issue_id, user_id,
                f"Work Order {wo_number} issued to '{contractor}' under Lead Engineer {lead_engineer}.",
                datetime.datetime.now()
            )
        )

        # Optional initial inventory deduction
        res_id = request.form.get('resource_id')
        res_qty = request.form.get('resource_quantity')
        if res_id and res_qty:
            try:
                res_qty_val = float(res_qty)
                if res_qty_val > 0:
                    res_stock = query_db("SELECT quantity, name, unit FROM resources WHERE id = %s", (res_id,), one=True)
                    if res_stock and res_stock['quantity'] >= res_qty_val:
                        execute_db(
                            """
                            INSERT INTO resource_allocations (work_order_id, resource_id, quantity_allocated, allocated_by, allocated_at)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (wo_id, res_id, res_qty_val, user_id, datetime.datetime.now())
                        )
                        execute_db(
                            "UPDATE resources SET quantity = quantity - %s WHERE id = %s",
                            (res_qty_val, res_id)
                        )
                        log_audit('RESOURCE_ALLOCATED', 'WorkOrder', wo_id, f"Allocated {res_qty_val} {res_stock['unit']} of {res_stock['name']}")
                    else:
                        flash('Note: Requested resource quantity exceeded available stock; order created without initial allocation.', 'warning')
            except ValueError:
                pass

        log_audit(
            'WORK_ORDER_CREATED', 'WorkOrder', wo_number,
            f"Assigned to {contractor} for issue #{selected_issue_id} with budget ₹{estimated_cost:,.2f}"
        )

        flash(f"Work Order {wo_number} issued successfully!", 'success')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))

    return render_template(
        'work_orders/create.html',
        available_issues=available_issues,
        resources=resources,
        preselected_issue_id=issue_id
    )


@work_orders_bp.route('/<int:wo_id>')
@login_required
def detail(wo_id):
    """View details of a specific work order, its progress, and allocated assets."""
    wo = query_db(
        """
        SELECT w.*, 
               i.ticket_number, i.title as issue_title, i.category as issue_category,
               i.sector as issue_sector, i.location_name, i.priority_score, i.priority_level,
               u.full_name as created_by_name
        FROM work_orders w
        JOIN issues i ON w.issue_id = i.id
        JOIN users u ON w.created_by = u.id
        WHERE w.id = %s
        """,
        (wo_id,),
        one=True
    )
    if not wo:
        flash('Requested work order was not found.', 'danger')
        return redirect(url_for('work_orders.list_work_orders'))

    allocations = query_db(
        """
        SELECT ra.*, r.name as resource_name, r.resource_code, r.unit, r.unit_cost,
               u.full_name as allocated_by_name
        FROM resource_allocations ra
        JOIN resources r ON ra.resource_id = r.id
        JOIN users u ON ra.allocated_by = u.id
        WHERE ra.work_order_id = %s
        ORDER BY ra.allocated_at DESC
        """,
        (wo_id,)
    )

    available_resources = query_db("SELECT * FROM resources WHERE quantity > 0")

    return render_template(
        'work_orders/detail.html',
        wo=wo,
        allocations=allocations,
        available_resources=available_resources,
        statuses=WO_STATUSES
    )


@work_orders_bp.route('/<int:wo_id>/update-progress', methods=['POST'])
@login_required
@role_required('admin', 'engineer', 'maintenance')
def update_progress(wo_id):
    """Update progress percentage, actual expenditure, and milestone status."""
    token = request.form.get('csrf_token')
    if not validate_csrf(token):
        flash('Security check failed.', 'danger')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))

    wo = query_db("SELECT * FROM work_orders WHERE id = %s", (wo_id,), one=True)
    if not wo:
        flash('Work order not found.', 'danger')
        return redirect(url_for('work_orders.list_work_orders'))

    try:
        progress = max(0, min(100, int(request.form.get('progress_percentage', 0))))
    except ValueError:
        progress = wo['progress_percentage']

    status = request.form.get('status', wo['status']).strip()
    if status not in WO_STATUSES:
        status = wo['status']

    try:
        actual_cost = float(request.form.get('actual_cost', wo['actual_cost']) or 0)
        if actual_cost < 0:
            flash('Actual expenditure cost cannot be negative.', 'warning')
            return redirect(url_for('work_orders.detail', wo_id=wo_id))
    except ValueError:
        actual_cost = wo['actual_cost']

    completion_date = None
    if progress == 100 or status == 'Completed':
        completion_date = datetime.date.today()
        status = 'Completed'
        progress = 100

        # Mark linked issue as Resolved automatically
        execute_db(
            "UPDATE issues SET status = 'Resolved', updated_at = %s WHERE id = %s",
            (datetime.datetime.now(), wo['issue_id'])
        )
        execute_db(
            """
            INSERT INTO issue_timeline (issue_id, user_id, action, previous_status, new_status, remarks, created_at)
            VALUES (%s, %s, 'STATUS_CHANGE', 'In Progress', 'Resolved', %s, %s)
            """,
            (
                wo['issue_id'], session['user_id'],
                f"Work order {wo['work_order_no']} reached 100% completion. Issue marked Resolved.",
                datetime.datetime.now()
            )
        )
    elif status == 'In Progress' and progress > 0:
        execute_db(
            "UPDATE issues SET status = 'In Progress', updated_at = %s WHERE id = %s AND status != 'In Progress'",
            (datetime.datetime.now(), wo['issue_id'])
        )

    execute_db(
        """
        UPDATE work_orders 
        SET progress_percentage = %s, status = %s, actual_cost = %s, completion_date = %s, updated_at = %s
        WHERE id = %s
        """,
        (progress, status, actual_cost, completion_date, datetime.datetime.now(), wo_id)
    )

    log_audit(
        'WORK_ORDER_UPDATED', 'WorkOrder', wo['work_order_no'],
        f"Progress: {progress}% | Status: {status} | Actual Cost: ₹{actual_cost:,.2f}"
    )

    flash(f"Work order {wo['work_order_no']} progress updated to {progress}% ({status}).", 'success')
    return redirect(url_for('work_orders.detail', wo_id=wo_id))


@work_orders_bp.route('/<int:wo_id>/allocate-resource', methods=['POST'])
@login_required
@role_required('admin', 'engineer', 'maintenance')
def allocate_resource(wo_id):
    """Allocate materials or assets from depot to a work order and deduct stock."""
    token = request.form.get('csrf_token')
    if not validate_csrf(token):
        flash('Security verification failed.', 'danger')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))

    resource_id = request.form.get('resource_id')
    quantity = request.form.get('quantity')

    if not (resource_id and quantity):
        flash('Please select an asset and specify the quantity to allocate.', 'warning')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))

    try:
        qty_val = float(quantity)
        if qty_val <= 0:
            flash('Allocation quantity must be greater than zero.', 'warning')
            return redirect(url_for('work_orders.detail', wo_id=wo_id))
    except ValueError:
        flash('Invalid quantity format.', 'warning')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))

    res = query_db("SELECT * FROM resources WHERE id = %s", (resource_id,), one=True)
    if not res:
        flash('Resource item not found in logistics registry.', 'danger')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))

    if res['quantity'] < qty_val:
        flash(f"Insufficient stock for '{res['name']}'. Available: {res['quantity']} {res['unit']}.", 'danger')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))

    execute_db(
        """
        INSERT INTO resource_allocations (work_order_id, resource_id, quantity_allocated, allocated_by, allocated_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (wo_id, resource_id, qty_val, session['user_id'], datetime.datetime.now())
    )

    execute_db(
        "UPDATE resources SET quantity = quantity - %s WHERE id = %s",
        (qty_val, resource_id)
    )

    log_audit(
        'RESOURCE_ALLOCATED', 'WorkOrder', wo_id,
        f"Allocated {qty_val} {res['unit']} of {res['name']} to WO #{wo_id}"
    )

    flash(f"Allocated {qty_val} {res['unit']} of '{res['name']}' to this work order.", 'success')
    return redirect(url_for('work_orders.detail', wo_id=wo_id))
