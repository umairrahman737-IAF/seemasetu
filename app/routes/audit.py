from flask import Blueprint, render_template, request
from app.db import query_db
from app.utils import login_required, role_required

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@login_required
@role_required('admin')
def list_logs():
    action = request.args.get('action', '').strip()
    entity_type = request.args.get('entity_type', '').strip()
    search = request.args.get('search', '').strip()
    
    query = """
        SELECT a.*, u.full_name as user_full_name, u.role as user_role
        FROM audit_logs a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE 1=1
    """
    params = []
    
    if action:
        query += " AND a.action = %s"
        params.append(action)
    if entity_type:
        query += " AND a.entity_type = %s"
        params.append(entity_type)
    if search:
        query += " AND (a.username LIKE %s OR a.details LIKE %s OR a.entity_id LIKE %s)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term])
        
    query += " ORDER BY a.created_at DESC LIMIT 200"
    
    logs = query_db(query, tuple(params))
    
    # Unique actions for filtering dropdown
    action_types = query_db("SELECT DISTINCT action FROM audit_logs ORDER BY action ASC")
    entity_types = query_db("SELECT DISTINCT entity_type FROM audit_logs ORDER BY entity_type ASC")
    
    return render_template(
        'audit/list.html',
        logs=logs,
        action_types=[a['action'] for a in action_types],
        entity_types=[e['entity_type'] for e in entity_types],
        current_action=action,
        current_entity=entity_type,
        current_search=search
    )
