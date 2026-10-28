"""
SeemaSetu — Border Infrastructure Monitoring and Maintenance System.
Flask Application Factory & Core Initialization.
"""

import os
import datetime
import logging
from flask import Flask, render_template, session
from app.config import Config
from app.db import close_db, init_db
from app.utils import generate_csrf_token, format_currency

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """
    Application factory for SeemaSetu.
    Configures explicit static/template paths, security headers, Jinja filters, and blueprints.
    """
    basedir = os.path.abspath(os.path.dirname(__file__))
    static_folder = os.path.join(basedir, 'static')
    template_folder = os.path.join(basedir, 'templates')

    app = Flask(
        __name__,
        static_folder=static_folder,
        static_url_path='/static',
        template_folder=template_folder
    )
    app.config.from_object(config_class)

    # Ensure upload directory exists safely (handles read-only serverless filesystems)
    upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(static_folder, 'uploads'))
    try:
        os.makedirs(upload_folder, exist_ok=True)
    except OSError as err:
        # Graceful fallback for read-only cloud environments like Vercel
        fallback_upload = os.path.join('/tmp', 'seemasetu_uploads')
        try:
            os.makedirs(fallback_upload, exist_ok=True)
            app.config['UPLOAD_FOLDER'] = fallback_upload
            logger.info(f"Read-only filesystem detected; upload folder redirected to {fallback_upload}")
        except Exception:
            logger.warning(f"Could not initialize local upload directory: {err}")

    # Register DB teardown
    app.teardown_appcontext(close_db)

    # Context Processors for Templates
    @app.context_processor
    def inject_global_template_vars():
        return {
            'csrf_token': generate_csrf_token,
            'current_year': datetime.datetime.now().year,
            'app_name': app.config.get('APP_NAME', 'SeemaSetu'),
            'app_tagline': app.config.get('APP_TAGLINE', 'Border Infrastructure Monitoring System'),
            'session_user': session
        }

    # Custom Jinja Filters
    @app.template_filter('currency')
    def currency_filter(val):
        return format_currency(val)

    @app.template_filter('format_datetime')
    def format_datetime_filter(dt_val):
        if not dt_val:
            return '-'
        if isinstance(dt_val, str):
            try:
                dt_val = datetime.datetime.fromisoformat(dt_val.replace(' ', 'T'))
            except Exception:
                return dt_val
        if isinstance(dt_val, (datetime.datetime, datetime.date)):
            return dt_val.strftime('%d %b %Y, %I:%M %p')
        return str(dt_val)

    @app.template_filter('format_date')
    def format_date_filter(d_val):
        if not d_val:
            return '-'
        if isinstance(d_val, str):
            try:
                d_val = datetime.datetime.fromisoformat(d_val).date()
            except Exception:
                return d_val
        if isinstance(d_val, (datetime.datetime, datetime.date)):
            return d_val.strftime('%d %b %Y')
        return str(d_val)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.issues import issues_bp
    from app.routes.work_orders import work_orders_bp
    from app.routes.resources import resources_bp
    from app.routes.audit import audit_bp
    from app.routes.api import api_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(issues_bp)
    app.register_blueprint(work_orders_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(api_bp)

    # Custom HTTP Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    # Initialize Database (verifies/creates schema & seed if needed)
    with app.app_context():
        try:
            init_db(app)
        except Exception as e:
            logger.warning(f"Database initialization deferred or skipped: {e}")

    return app
