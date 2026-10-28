from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import query_db, execute_db
from app.utils import log_audit, validate_csrf, login_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
        
    if request.method == 'POST':
        # CSRF check
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
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                return render_template('auth/login.html')
                
            # Set session
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            session['department'] = user['department']
            session['badge_number'] = user['badge_number']
            session.permanent = True
            
            log_audit('USER_LOGIN', 'User', user['id'], f"User logged in from {request.remote_addr}", user['id'], user['username'])
            flash(f"Welcome back, {user['full_name']} ({user['role'].title()}).", 'success')
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password. Please check your credentials.', 'danger')
            
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
        role = 'user'  # Public registrations default to user (field reporter)
        
        # Validation
        if not (username and email and full_name and password):
            flash('Please fill in all required fields.', 'warning')
            return render_template('auth/register.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'warning')
            return render_template('auth/register.html')
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('auth/register.html')
            
        # Check existing
        existing = query_db(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email),
            one=True
        )
        if existing:
            flash('Username or Email already registered in the system.', 'warning')
            return render_template('auth/register.html')
            
        hashed = generate_password_hash(password)
        
        user_id = execute_db(
            """
            INSERT INTO users (username, email, password_hash, full_name, role, department, badge_number, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """,
            (username, email, hashed, full_name, role, department, badge_number)
        )
        
        log_audit('USER_REGISTERED', 'User', user_id, f"Self-registered new account: {username}", user_id, username)
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
