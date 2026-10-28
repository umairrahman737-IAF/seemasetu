import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import query_db, execute_db
from app.utils import login_required, role_required, log_audit, validate_csrf

work_orders_bp = Blueprint('work_orders', __name__, url_prefix='/work-orders')

WO_STATUSES = ['Assigned', 'In Progress', 'Under Inspection', 'Completed', 'Delayed']

def generate_work_order_number():
    year = datetime.datetime.now().strftime('%Y')
    last_wo = query_db("SELECT id FROM work_orders ORDER BY id DESC LIMIT 1", one=True)
    next_id = (last_wo['id'] + 1) if last_wo else 1
    return f"WO-{year}-{next_id:04d}"


@work_orders_bp.route('/')
@login_required
def list_work_orders():
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
@role_required('admin', 'officer')
def create():
    issue_id = request.args.get('issue_id')
    
    # Available issues without an active work order
    available_issues = query_db(
        """
        SELECT id, ticket_number, title, category, priority_level, sector
        FROM issues
        WHERE id NOT IN (SELECT issue_id FROM work_orders WHERE status != 'Completed')
        ORDER BY priority_score DESC
        """
    )
    
    # Resources for optional direct allocation
    resources = query_db("SELECT id, name, category, quantity, unit FROM resources WHERE quantity > 0")
    
    if request.method == 'POST':
        token = request.form.get('csrf_token')
        if not validate_csrf(token):
            flash('Security validation failed.', 'danger')
            return redirect(url_for('work_orders.create'))
            
        selected_issue_id = request.form.get('issue_id')
        contractor = request.form.get('contractor_or_unit', '').strip()
        lead_engineer = request.form.get('lead_engineer', '').strip()
        estimated_cost = request.form.get('estimated_cost', '0').strip()
        start_date = request.form.get('start_date', '').strip()
        target_date = request.form.get('target_date', '').strip()
        scope_of_work = request.form.get('scope_of_work', '').strip()
        
        if not (selected_issue_id and contractor and lead_engineer and start_date and target_date and scope_of_work):
            flash('Please fill in all mandatory fields.', 'warning')
            return render_template(
                'work_orders/create.html',
                available_issues=available_issues,
                resources=resources,
                preselected_issue_id=issue_id
            )
            
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
                float(estimated_cost or 0), start_date, target_date,
                scope_of_work, user_id, datetime.datetime.now()
            )
        )
        
        # Automatically update issue status to 'Work Order Assigned'
        execute_db(
            """
            UPDATE issues 
            SET status = 'Work Order Assigned', updated_at = %s 
            WHERE id = %s AND status = 'Reported'
            """,
            (datetime.datetime.now(), selected_issue_id)
        )
        
        # Add issue timeline entry
        execute_db(
            """
            INSERT INTO issue_timeline (issue_id, user_id, action, previous_status, new_status, remarks, created_at)
            VALUES (%s, %s, 'WORK_ORDER_ISSUED', 'Reported', 'Work Order Assigned', %s, %s)
            """,
            (
                selected_issue_id, user_id,
                f"Work order {wo_number} assigned to {contractor} under lead engineer {lead_engineer}.",
                datetime.datetime.now()
            )
        )
        
        # Optional resource allocation during creation
        res_id = request.form.get('resource_id')
        res_qty = request.form.get('resource_quantity')
        if res_id and res_qty:
            try:
                res_qty_val = float(res_qty)
                if res_qty_val > 0:
                    execute_db(
                        """
                        INSERT INTO resource_allocations (work_order_id, resource_id, quantity_allocated, allocated_by, allocated_at)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (wo_id, res_id, res_qty_val, user_id, datetime.datetime.now())
                    )
                    # Deduct from inventory
                    execute_db(
                        "UPDATE resources SET quantity = quantity - %s WHERE id = %s",
                        (res_qty_val, res_id)
                    )
            except ValueError:
                pass
                
        log_audit(
            'WORK_ORDER_CREATED', 'WorkOrder', wo_number,
            f"Assigned to {contractor} for issue #{selected_issue_id}"
        )
        
        flash(f"Work Order {wo_number} initialized successfully!", 'success')
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
        flash('Work order not found.', 'danger')
        return redirect(url_for('work_orders.list_work_orders'))
        
    # Get allocated resources
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
    
    # Available resources for new allocation
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
def update_progress(wo_id):
    token = request.form.get('csrf_token')
    if not validate_csrf(token):
        flash('Security check failed.', 'danger')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))
        
    wo = query_db("SELECT * FROM work_orders WHERE id = %s", (wo_id,), one=True)
    if not wo:
        flash('Work order not found.', 'danger')
        return redirect(url_for('work_orders.list_work_orders'))
        
    progress = int(request.form.get('progress_percentage', 0))
    status = request.form.get('status', wo['status'])
    actual_cost = float(request.form.get('actual_cost', wo['actual_cost']) or 0)
    remarks = request.form.get('remarks', '').strip()
    
    completion_date = None
    if progress == 100 or status == 'Completed':
        completion_date = datetime.date.today()
        status = 'Completed'
        # Also mark linked issue as Resolved!
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
    elif status == 'In Progress':
        # Mark linked issue as In Progress
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
@role_required('admin', 'officer')
def allocate_resource(wo_id):
    token = request.form.get('csrf_token')
    if not validate_csrf(token):
        flash('Security verification failed.', 'danger')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))
        
    resource_id = request.form.get('resource_id')
    quantity = request.form.get('quantity')
    
    if not (resource_id and quantity):
        flash('Please select a resource and specify quantity.', 'warning')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))
        
    try:
        qty_val = float(quantity)
        if qty_val <= 0:
            flash('Quantity must be greater than zero.', 'warning')
            return redirect(url_for('work_orders.detail', wo_id=wo_id))
    except ValueError:
        flash('Invalid quantity format.', 'warning')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))
        
    res = query_db("SELECT * FROM resources WHERE id = %s", (resource_id,), one=True)
    if not res:
        flash('Resource not found in inventory.', 'danger')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))
        
    if res['quantity'] < qty_val:
        flash(f"Insufficient stock for {res['name']}. Available: {res['quantity']} {res['unit']}.", 'danger')
        return redirect(url_for('work_orders.detail', wo_id=wo_id))
        
    # Allocate resource
    execute_db(
        """
        INSERT INTO resource_allocations (work_order_id, resource_id, quantity_allocated, allocated_by, allocated_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (wo_id, resource_id, qty_val, session['user_id'], datetime.datetime.now())
    )
    
    # Decrement available quantity
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
