"""
Authentication & User Administration Blueprint for SeemaSetu.
Handles secure login, registration, logout, profile view,
and administrative user management (role assignments and account activation).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import query_db, execute_db
from app.utils import log_audit, validate_csrf, login_required, role_required, admin_required, normalize_role

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

VALID_ROLES = ['admin', 'engineer', 'maintenance', 'viewer']


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        token = request.form.get('csrf_token')
        if not validate_csrf(token):
            flash('Security token invalid or expired. Please try again.', 'danger')
            return render_template('auth/login.html')

        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username_or_email or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('auth/login.html')

        # Parameterized query to prevent SQL Injection
        user = query_db(
            """
            SELECT id, username, email, password_hash, full_name, role, department, badge_number, is_active
            FROM users
            WHERE username = %s OR email = %s
            """,
            (username_or_email, username_or_email),
            one=True
        )

        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                flash('This account has been deactivated. Please contact an administrator.', 'danger')
                return render_template('auth/login.html')

            # Populate session
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = normalize_role(user['role'])
            session['department'] = user['department']
            session['badge_number'] = user['badge_number']
            session.permanent = True

            log_audit(
                'USER_LOGIN', 'User', user['id'],
                f"User authenticated from IP {request.remote_addr}",
                user['id'], user['username']
            )
            flash(f"Welcome back, {user['full_name']} ({session['role'].title()}).", 'success')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password. Please verify your credentials.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        token = request.form.get('csrf_token')
        if not validate_csrf(token):
            flash('Security token invalid. Please refresh the page.', 'danger')
            return render_template('auth/register.html')

        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        department = request.form.get('department', '').strip() or 'Border Field Patrol & Civil Works'
        badge_number = request.form.get('badge_number', '').strip()
        role = 'viewer'  # Public self-registration defaults to viewer/reporter role

        # Input Validations
        if not (username and email and full_name and password):
            flash('Please complete all mandatory registration fields.', 'warning')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'warning')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must contain at least 6 characters.', 'warning')
            return render_template('auth/register.html')

        # Check existing username or email
        existing = query_db(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email),
            one=True
        )
        if existing:
            flash('Username or Email is already registered in the system.', 'warning')
            return render_template('auth/register.html')

        hashed = generate_password_hash(password)

        user_id = execute_db(
            """
            INSERT INTO users (username, email, password_hash, full_name, role, department, badge_number, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """,
            (username, email, hashed, full_name, role, department, badge_number)
        )

        log_audit(
            'USER_REGISTERED', 'User', user_id,
            f"Self-registered account: {username} ({role})",
            user_id, username
        )
        flash('Account registered successfully! You may now sign in with your credentials.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    uid = session.get('user_id')
    uname = session.get('username')
    if uid:
        log_audit('USER_LOGOUT', 'User', uid, "User logged out voluntarily", uid, uname)
    session.clear()
    flash('You have been signed out safely.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    user = query_db("SELECT * FROM users WHERE id = %s", (session['user_id'],), one=True)
    activity = query_db(
        "SELECT * FROM audit_logs WHERE user_id = %s ORDER BY created_at DESC LIMIT 15",
        (session['user_id'],)
    )
    my_issues_count = query_db(
        "SELECT COUNT(*) as cnt FROM issues WHERE reported_by = %s",
        (session['user_id'],),
        one=True
    )['cnt']

    return render_template('auth/profile.html', user=user, activity=activity, my_issues_count=my_issues_count)


# =========================================================================
# User Administration Endpoints (Admin Only)
# =========================================================================

@auth_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """List all registered system users and manage roles and permissions."""
    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()

    query = "SELECT id, username, email, full_name, role, department, badge_number, is_active, created_at FROM users WHERE 1=1"
    params = []

    if search:
        query += " AND (username LIKE %s OR email LIKE %s OR full_name LIKE %s OR department LIKE %s)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term, like_term])

    if role_filter:
        query += " AND role = %s"
        params.append(role_filter)

    query += " ORDER BY id ASC"
    users = query_db(query, tuple(params))

    # Summary counts
    total_users = query_db("SELECT COUNT(*) as c FROM users", one=True)['c']
    active_users = query_db("SELECT COUNT(*) as c FROM users WHERE is_active = 1", one=True)['c']

    return render_template(
        'auth/admin_users.html',
        users=users,
        valid_roles=VALID_ROLES,
        total_users=total_users,
        active_users=active_users,
        current_search=search,
        current_role=role_filter
    )


@auth_bp.route('/admin/users/<int:target_user_id>/update-role', methods=['POST'])
@login_required
@admin_required
def admin_update_role(target_user_id):
    token = request.form.get('csrf_token')
    if not validate_csrf(token):
        flash('Security check failed.', 'danger')
        return redirect(url_for('auth.admin_users'))

    new_role = request.form.get('role', '').strip().lower()
    if new_role not in VALID_ROLES:
        flash('Invalid role specified.', 'warning')
        return redirect(url_for('auth.admin_users'))

    target_user = query_db("SELECT id, username, role FROM users WHERE id = %s", (target_user_id,), one=True)
    if not target_user:
        flash('Target user not found.', 'danger')
        return redirect(url_for('auth.admin_users'))

    # Prevent demoting the last active admin
    if target_user['role'] == 'admin' and new_role != 'admin':
        admin_count = query_db("SELECT COUNT(*) as c FROM users WHERE role = 'admin' AND is_active = 1", one=True)['c']
        if admin_count <= 1:
            flash('Operation rejected: Cannot demote the sole active administrator account.', 'danger')
            return redirect(url_for('auth.admin_users'))

    old_role = target_user['role']
    execute_db("UPDATE users SET role = %s WHERE id = %s", (new_role, target_user_id))

    log_audit(
        'USER_ROLE_CHANGED', 'User', target_user_id,
        f"Admin changed role of @{target_user['username']} from '{old_role}' to '{new_role}'"
    )
    flash(f"Role for user @{target_user['username']} updated to '{new_role.title()}'.", 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:target_user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def admin_toggle_status(target_user_id):
    token = request.form.get('csrf_token')
    if not validate_csrf(token):
        flash('Security check failed.', 'danger')
        return redirect(url_for('auth.admin_users'))

    if target_user_id == session.get('user_id'):
        flash('Operation rejected: You cannot deactivate your own administrative account.', 'danger')
        return redirect(url_for('auth.admin_users'))

    target_user = query_db("SELECT id, username, is_active FROM users WHERE id = %s", (target_user_id,), one=True)
    if not target_user:
        flash('Target user not found.', 'danger')
        return redirect(url_for('auth.admin_users'))

    new_status = 0 if target_user['is_active'] else 1
    execute_db("UPDATE users SET is_active = %s WHERE id = %s", (new_status, target_user_id))

    status_str = "activated" if new_status else "deactivated"
    log_audit(
        'USER_STATUS_TOGGLED', 'User', target_user_id,
        f"Admin {status_str} account for @{target_user['username']}"
    )
    flash(f"Account for @{target_user['username']} has been {status_str}.", 'info')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/create', methods=['POST'])
@login_required
@admin_required
def admin_create_user():
    token = request.form.get('csrf_token')
    if not validate_csrf(token):
        flash('Security check failed.', 'danger')
        return redirect(url_for('auth.admin_users'))

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    full_name = request.form.get('full_name', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'viewer').strip().lower()
    department = request.form.get('department', '').strip() or 'Border Infrastructure Command'
    badge_number = request.form.get('badge_number', '').strip()

    if not (username and email and full_name and password):
        flash('Please fill in all mandatory fields.', 'warning')
        return redirect(url_for('auth.admin_users'))

    if role not in VALID_ROLES:
        role = 'viewer'

    if len(password) < 6:
        flash('Password must contain at least 6 characters.', 'warning')
        return redirect(url_for('auth.admin_users'))

    existing = query_db("SELECT id FROM users WHERE username = %s OR email = %s", (username, email), one=True)
    if existing:
        flash(f"User with username '{username}' or email '{email}' already exists.", 'warning')
        return redirect(url_for('auth.admin_users'))

    hashed = generate_password_hash(password)
    user_id = execute_db(
        """
        INSERT INTO users (username, email, password_hash, full_name, role, department, badge_number, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
        """,
        (username, email, hashed, full_name, role, department, badge_number)
    )

    log_audit(
        'USER_CREATED_BY_ADMIN', 'User', user_id,
        f"Administrator created user @{username} with role '{role}'"
    )
    flash(f"New user @{username} ({full_name}) created successfully with role '{role.title()}'.", 'success')
    return redirect(url_for('auth.admin_users'))
