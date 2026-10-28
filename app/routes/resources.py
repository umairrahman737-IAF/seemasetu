import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import query_db, execute_db
from app.utils import login_required, role_required, log_audit, validate_csrf

resources_bp = Blueprint('resources', __name__, url_prefix='/resources')

RESOURCE_CATEGORIES = [
    'Civil & Road Material',
    'Structural Steel',
    'Electrical & Solar',
    'Water Supply & Piping',
    'Heavy Machinery'
]

RESOURCE_UNITS = ['Tons', 'Units', 'Meters', 'Drums', 'Bags', 'Kits']

@resources_bp.route('/')
@login_required
def list_resources():
    category = request.args.get('category', '').strip()
    filter_low_stock = request.args.get('low_stock', '')
    search = request.args.get('search', '').strip()
    
    query = "SELECT * FROM resources WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = %s"
        params.append(category)
    if filter_low_stock == '1':
        query += " AND quantity <= min_threshold"
    if search:
        query += " AND (name LIKE %s OR resource_code LIKE %s OR depot_location LIKE %s)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term])
        
    query += " ORDER BY category ASC, name ASC"
    
    resources = query_db(query, tuple(params))
    
    # Summary metrics
    total_items = query_db("SELECT COUNT(*) as c FROM resources", one=True)['c']
    low_stock_count = query_db("SELECT COUNT(*) as c FROM resources WHERE quantity <= min_threshold", one=True)['c']
    
    return render_template(
        'resources/list.html',
        resources=resources,
        categories=RESOURCE_CATEGORIES,
        units=RESOURCE_UNITS,
        total_items=total_items,
        low_stock_count=low_stock_count,
        current_category=category,
        current_low_stock=filter_low_stock,
        current_search=search
    )


@resources_bp.route('/add', methods=['POST'])
@login_required
@role_required('admin')
def add_resource():
    token = request.form.get('csrf_token')
    if not validate_csrf(token):
        flash('Security check failed.', 'danger')
        return redirect(url_for('resources.list_resources'))
        
    code = request.form.get('resource_code', '').strip().upper()
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    quantity = float(request.form.get('quantity', 0) or 0)
    unit = request.form.get('unit', '').strip()
    min_threshold = float(request.form.get('min_threshold', 10) or 10)
    depot_location = request.form.get('depot_location', '').strip()
    unit_cost = float(request.form.get('unit_cost', 0) or 0)
    
    if not (code and name and category and unit and depot_location):
        flash('Please fill in all mandatory resource fields.', 'warning')
        return redirect(url_for('resources.list_resources'))
        
    existing = query_db("SELECT id FROM resources WHERE resource_code = %s", (code,), one=True)
    if existing:
        flash(f"Resource with code '{code}' already exists.", 'warning')
        return redirect(url_for('resources.list_resources'))
        
    res_id = execute_db(
        """
        INSERT INTO resources (
            resource_code, name, category, quantity, unit,
            min_threshold, depot_location, unit_cost, last_restocked, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            code, name, category, quantity, unit,
            min_threshold, depot_location, unit_cost,
            datetime.datetime.now(), datetime.datetime.now()
        )
    )
    
    log_audit('RESOURCE_ADDED', 'Resource', code, f"Added {name} ({quantity} {unit}) to inventory")
    flash(f"Resource '{name}' ({code}) added to logistics inventory.", 'success')
    return redirect(url_for('resources.list_resources'))


@resources_bp.route('/<int:resource_id>/restock', methods=['POST'])
@login_required
@role_required('admin', 'officer')
def restock_resource(resource_id):
    token = request.form.get('csrf_token')
    if not validate_csrf(token):
        flash('Security check failed.', 'danger')
        return redirect(url_for('resources.list_resources'))
        
    res = query_db("SELECT * FROM resources WHERE id = %s", (resource_id,), one=True)
    if not res:
        flash('Resource not found.', 'danger')
        return redirect(url_for('resources.list_resources'))
        
    add_qty = float(request.form.get('add_quantity', 0) or 0)
    if add_qty <= 0:
        flash('Restock quantity must be positive.', 'warning')
        return redirect(url_for('resources.list_resources'))
        
    execute_db(
        """
        UPDATE resources 
        SET quantity = quantity + %s, last_restocked = %s 
        WHERE id = %s
        """,
        (add_qty, datetime.datetime.now(), resource_id)
    )
    
    log_audit(
        'RESOURCE_RESTOCKED', 'Resource', res['resource_code'],
        f"Added +{add_qty} {res['unit']}. New Total: {res['quantity'] + add_qty}"
    )
    
    flash(f"Restocked +{add_qty} {res['unit']} for {res['name']}.", 'success')
    return redirect(url_for('resources.list_resources'))
