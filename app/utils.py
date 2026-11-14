"""
Utility helpers for SeemaSetu.
Encompasses RBAC decorators, CSRF token generation/validation,
secure file uploads (with optional Azure Blob Storage integration),
audit logging, and currency formatting.
"""

import os
import secrets
import logging
from functools import wraps
from datetime import datetime
from flask import session, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app.db import execute_db

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Canonical roles recognized in SeemaSetu:
# - 'admin': Border Command Headquarters (full privileges)
# - 'engineer': Sector Lead Engineers / Officers (work order issuance, priority re-scoring, status management)
# - 'maintenance': Field Maintenance Units / Contractors (progress sliders, actual costs, resource deduction)
# - 'viewer': Field Reporters / Observers (defect reporting, read-only tracking)

ROLE_ALIASES = {
    'officer': 'engineer',
    'user': 'viewer'
}


def normalize_role(role_name):
    """Normalize legacy or alias role strings into canonical roles."""
    if not role_name:
        return 'viewer'
    role_lower = str(role_name).strip().lower()
    return ROLE_ALIASES.get(role_lower, role_lower)


def login_required(f):
    """Ensure user has an active authenticated session before accessing view."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """
    Ensure current user holds one of the authorized roles or is an administrator.
    Correctly enforces Role-Based Access Control (RBAC) with zero escalation bypass.
    """
    # Build full set of authorized roles including aliases
    authorized_set = set()
    for r in allowed_roles:
        r_norm = normalize_role(r)
        authorized_set.add(r_norm)
        # Add aliases for backward compatibility
        if r_norm == 'engineer':
            authorized_set.add('officer')
        elif r_norm == 'viewer':
            authorized_set.add('user')

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))

            user_role = session.get('role', 'viewer')
            user_role_norm = normalize_role(user_role)

            # Administrators have universal operational access
            if user_role_norm == 'admin' or user_role == 'admin':
                return f(*args, **kwargs)

            # Check if user's role matches any allowed role
            if user_role_norm not in authorized_set and user_role not in authorized_set:
                flash('Access Denied: You do not have the required administrative role for this operation.', 'danger')
                return redirect(url_for('dashboard.index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Shortcut decorator for endpoints strictly restricted to administrators."""
    return role_required('admin')(f)


def generate_csrf_token():
    """Generate or retrieve a cryptographically secure CSRF token for the active session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(24)
    return session['_csrf_token']


def validate_csrf(token):
    """Validate submitted CSRF token against session state using constant-time comparison."""
    session_token = session.get('_csrf_token')
    return bool(session_token and token and secrets.compare_digest(session_token, token))


def allowed_file(filename):
    """Verify that an uploaded filename bears a whitelisted image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, destination_dir):
    """
    Sanitize filename and save uploaded image safely.
    Supports Azure Blob Storage if configured, or local persistent storage.
    Returns relative filename or public URL.
    """
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None

    orig_name = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    rand_suffix = secrets.token_hex(4)
    filename = f"issue_{timestamp}_{rand_suffix}_{orig_name}"

    # Check for Azure Blob Storage configuration
    azure_conn_str = current_app.config.get('AZURE_STORAGE_CONNECTION_STRING') if current_app else os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    azure_container = current_app.config.get('AZURE_CONTAINER_NAME', 'seemasetu-uploads') if current_app else 'seemasetu-uploads'

    if azure_conn_str:
        try:
            from azure.storage.blob import BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(azure_conn_str)
            container_client = blob_service_client.get_container_client(azure_container)
            if not container_client.exists():
                container_client.create_container()
            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(file.read(), overwrite=True)
            logger.info(f"Image uploaded successfully to Azure Blob Storage: {filename}")
            return filename
        except Exception as e:
            logger.warning(f"Azure Blob Storage upload failed ({e}); falling back to local storage.")
            file.seek(0)

    # Local filesystem storage
    try:
        os.makedirs(destination_dir, exist_ok=True)
        filepath = os.path.join(destination_dir, filename)
        file.save(filepath)
        return filename
    except OSError as err:
        # Serverless fallback (e.g., Vercel /tmp)
        tmp_dir = os.path.join('/tmp', 'seemasetu_uploads')
        os.makedirs(tmp_dir, exist_ok=True)
        filepath = os.path.join(tmp_dir, filename)
        file.save(filepath)
        logger.info(f"Saved upload to serverless /tmp directory: {filepath}")
        return filename


def log_audit(action, entity_type, entity_id, details=None, user_id=None, username=None):
    """
    Insert an audit log entry tracking operational and security actions.
    Uses parameterized queries exclusively to prevent SQL injection.
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
        logger.error(f"Audit log recording error: {e}")


def format_currency(val):
    """Format decimal/float into standard Indian Rupee notation (₹)."""
    try:
        val = float(val or 0)
        return f"₹ {val:,.2f}"
    except (ValueError, TypeError):
        return "₹ 0.00"
