"""
Utility helpers for security, audit logging, file uploads, and role decorators.
"""

import os
import secrets
from functools import wraps
from datetime import datetime
from flask import session, request, redirect, url_for, flash, abort, current_app
from werkzeug.utils import secure_filename
from app.db import execute_db

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def login_required(f):
    """Ensure user is logged in before accessing view."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Ensure current user holds one of the specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))
            user_role = session.get('role', 'user')
            if user_role not in allowed_roles and 'admin' not in allowed_roles and user_role != 'admin':
                flash('You do not have administrative authorization to access that resource.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Shortcut decorator for admin-only endpoints."""
    return role_required('admin')(f)

def generate_csrf_token():
    """Generate or retrieve a CSRF token for the session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(24)
    return session['_csrf_token']

def validate_csrf(token):
    """Validate submitted CSRF token against session."""
    session_token = session.get('_csrf_token')
    return bool(session_token and token and secrets.compare_digest(session_token, token))

def allowed_file(filename):
    """Check if uploaded file has safe image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, destination_dir):
    """
    Sanitize filename and save uploaded image safely with a unique prefix.
    Returns the relative filename or None.
    """
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None
    
    os.makedirs(destination_dir, exist_ok=True)
    orig_name = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    rand_suffix = secrets.token_hex(4)
    filename = f"issue_{timestamp}_{rand_suffix}_{orig_name}"
    
    filepath = os.path.join(destination_dir, filename)
    file.save(filepath)
    return filename

def log_audit(action, entity_type, entity_id, details=None, user_id=None, username=None):
    """
    Insert an audit log entry tracking critical system actions.
    Uses parameterized query to prevent SQL injection.
    """
    try:
        if user_id is None:
            user_id = session.get('user_id')
        if username is None:
            username = session.get('username', 'Anonymous/System')
            
        ip_addr = request.remote_addr if request else '127.0.0.1'
        
        execute_db(
            """
            INSERT INTO audit_logs (user_id, username, action, entity_type, entity_id, details, ip_address, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, username, action, entity_type, str(entity_id), details or '', ip_addr, datetime.now())
        )
    except Exception as e:
        # Audit failure must not crash the primary flow, but should be logged
        if current_app:
            current_app.logger.error(f"Audit log insertion error: {e}")

def format_currency(val):
    """Format decimal/float into Indian Rupee representation (₹)."""
    try:
        val = float(val or 0)
        return f"₹ {val:,.2f}"
    except (ValueError, TypeError):
        return "₹ 0.00"
