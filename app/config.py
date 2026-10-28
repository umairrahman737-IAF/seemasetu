import os
from datetime import timedelta
from dotenv import load_dotenv

# Load variables from .env if present
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(basedir), '.env'))

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'seemasetu-border-secure-key-2026-prod-unclassified')
    
    # Database Settings
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'seemasetu_db')
    
    # Upload Settings
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB maximum file upload
    
    # Security Settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # App Information
    APP_NAME = "SeemaSetu"
    APP_TAGLINE = "Border Infrastructure Monitoring and Maintenance System"
    APP_VERSION = "1.0.0"
