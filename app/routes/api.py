from flask import Blueprint, request, jsonify
from app.priority import calculate_priority
from app.db import query_db

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/calculate-priority-preview', methods=['POST'])
def calculate_priority_preview():
    """
    Asynchronous JSON endpoint returning rule-based priority evaluation.
    Used by frontend forms for real-time live preview of score and urgency rank.
    """
    data = request.get_json() or {}
    severity = data.get('severity', 'Medium')
    urgency = data.get('urgency', 'Moderate')
    category = data.get('category', 'Roads & Bridges')
    weather = data.get('weather_vulnerability', 'Moderate Risk')
    
    result = calculate_priority(severity, urgency, category, weather)
    return jsonify({
        'status': 'success',
        'data': result
    })

@api_bp.route('/metrics', methods=['GET'])
def get_metrics():
    total_issues = query_db("SELECT COUNT(*) as c FROM issues", one=True)['c']
    resolved_count = query_db("SELECT COUNT(*) as c FROM issues WHERE status IN ('Resolved', 'Closed')", one=True)['c']
    active_wo = query_db("SELECT COUNT(*) as c FROM work_orders WHERE status IN ('Assigned', 'In Progress')", one=True)['c']
    critical = query_db("SELECT COUNT(*) as c FROM issues WHERE priority_level = 'Critical'", one=True)['c']
    
    return jsonify({
        'total_issues': total_issues,
        'resolved_issues': resolved_count,
        'active_work_orders': active_wo,
        'critical_issues': critical
    })
