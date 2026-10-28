"""
SeemaSetu — Configuration Module.
Loads environment variables and sets operational thresholds.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Load variables from .env located at the project root
load_dotenv(os.path.join(os.path.dirname(basedir), '.env'))


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'seemasetu-border-secure-key-2026-prod-unclassified')

    # Database Configuration
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'seemasetu_db')
    SQLITE_PATH = os.getenv(
        'SQLITE_PATH',
        os.path.join(os.path.dirname(basedir), 'database', 'seemasetu.db')
    )

    # File Upload Settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(basedir, 'static', 'uploads'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))  # 5MB max upload

    # Azure Cloud Storage (Optional Persistent Object Storage for Production)
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
    AZURE_CONTAINER_NAME = os.getenv('AZURE_CONTAINER_NAME', 'seemasetu-uploads')

    # Security & Session Hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Application Metadata
    APP_NAME = "SeemaSetu"
    APP_TAGLINE = "Border Infrastructure Monitoring and Maintenance System"
    APP_VERSION = "1.0.0"
