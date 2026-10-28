"""
Database Management Layer for SeemaSetu.
Provides unified access for MySQL with automatic fallback to SQLite for local development.
Enforces parameterized queries to protect against SQL Injection.
"""

import os
import re
import sqlite3
import logging
import datetime
from flask import g, current_app

logger = logging.getLogger(__name__)

# Check if PyMySQL is available
try:
    import pymysql
    import pymysql.cursors
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


def get_db_config():
    """Extract DB configuration from app config or environment variables."""
    return {
        'type': os.getenv('DB_TYPE', 'sqlite').lower(),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'seemasetu_db'),
        'sqlite_path': os.getenv(
            'SQLITE_PATH',
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'seemasetu.db')
        )
    }


def get_db():
    """
    Get or initialize the current request database connection.
    Caches connection in Flask's request context `g`.
    """
    if 'db' not in g:
        config = get_db_config()
        conn = None
        db_type = config['type']

        if db_type == 'mysql' and PYMYSQL_AVAILABLE:
            try:
                conn = pymysql.connect(
                    host=config['host'],
                    port=config['port'],
                    user=config['user'],
                    password=config['password'],
                    database=config['database'],
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=False,
                    charset='utf8mb4'
                )
                g.db_type = 'mysql'
                logger.info("Connected successfully to MySQL database.")
            except Exception as e:
                logger.warning(
                    f"Could not connect to MySQL ({e}). Falling back to SQLite."
                )
                conn = None

        if conn is None:
            # Fallback or default: SQLite
            sqlite_file = config['sqlite_path']
            os.makedirs(os.path.dirname(sqlite_file), exist_ok=True)
            conn = sqlite3.connect(sqlite_file)
            conn.row_factory = sqlite3.Row
            # Enable foreign keys in SQLite
            conn.execute("PRAGMA foreign_keys = ON;")
            g.db_type = 'sqlite'

        g.db = conn

    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(sql, args=(), one=False):
    """
    Execute a parameterized SELECT query and return dictionary-like records.
    Automatically adapts placeholders (%s for MySQL, ? for SQLite).
    """
    db = get_db()
    db_type = getattr(g, 'db_type', 'sqlite')

    if db_type == 'sqlite':
        # Translate MySQL %s placeholders to SQLite ?
        translated_sql = sql.replace('%s', '?')
        clean_args = [
            a.strftime('%Y-%m-%d %H:%M:%S') if isinstance(a, datetime.datetime)
            else a.strftime('%Y-%m-%d') if isinstance(a, datetime.date)
            else a for a in args
        ]
        cursor = db.cursor()
        cursor.execute(translated_sql, clean_args)
        rows = cursor.fetchall()
        cursor.close()
        # Convert sqlite3.Row to standard dicts
        result = [dict(row) for row in rows]
    else:
        with db.cursor() as cursor:
            cursor.execute(sql, args)
            result = cursor.fetchall()

    return (result[0] if result else None) if one else result


def execute_db(sql, args=(), commit=True):
    """
    Execute an INSERT, UPDATE, or DELETE parameterized query.
    Returns the lastrowid or affected rows.
    """
    db = get_db()
    db_type = getattr(g, 'db_type', 'sqlite')
    last_id = None
    rowcount = 0

    if db_type == 'sqlite':
        translated_sql = sql.replace('%s', '?')
        clean_args = [
            a.strftime('%Y-%m-%d %H:%M:%S') if isinstance(a, datetime.datetime)
            else a.strftime('%Y-%m-%d') if isinstance(a, datetime.date)
            else a for a in args
        ]
        cursor = db.cursor()
        cursor.execute(translated_sql, clean_args)
        last_id = cursor.lastrowid
        rowcount = cursor.rowcount
        cursor.close()
        if commit:
            db.commit()
    else:
        with db.cursor() as cursor:
            cursor.execute(sql, args)
            last_id = cursor.lastrowid
            rowcount = cursor.rowcount
        if commit:
            db.commit()

    return last_id if last_id is not None and last_id > 0 else rowcount


def init_db(app=None):
    """
    Initialize database schema and populate seed demonstration data if needed.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    schema_path = os.path.join(base_dir, 'database', 'schema.sql')
    seed_path = os.path.join(base_dir, 'database', 'seed_data.sql')

    config = get_db_config()
    db_type = config['type']

    if db_type == 'mysql' and PYMYSQL_AVAILABLE:
        try:
            conn = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                autocommit=True
            )
            with conn.cursor() as cursor:
                # Read schema
                with open(schema_path, 'r', encoding='utf-8') as f:
                    statements = f.read().split(';')
                    for stmt in statements:
                        if stmt.strip():
                            cursor.execute(stmt)
                # Check if seed required
                cursor.execute("SELECT COUNT(*) FROM users;")
                count = cursor.fetchone()[0]
                if count == 0 and os.path.exists(seed_path):
                    with open(seed_path, 'r', encoding='utf-8') as f:
                        seed_stmts = f.read().split(';')
                        for stmt in seed_stmts:
                            if stmt.strip():
                                cursor.execute(stmt)
            conn.close()
            logger.info("MySQL database initialized successfully.")
            return True
        except Exception as e:
            logger.warning(f"MySQL initialization failed ({e}), falling back to SQLite setup.")

    # SQLite Setup
    sqlite_file = config['sqlite_path']
    os.makedirs(os.path.dirname(sqlite_file), exist_ok=True)
    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()

    # Convert MySQL schema to SQLite compatible DDL
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Transformations for SQLite compatibility
    sqlite_schema = schema_sql
    sqlite_schema = re.sub(r'INT AUTO_INCREMENT PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', sqlite_schema, flags=re.IGNORECASE)
    sqlite_schema = re.sub(r'ENGINE=InnoDB[^;]*', '', sqlite_schema, flags=re.IGNORECASE)
    sqlite_schema = re.sub(r'ON UPDATE CURRENT_TIMESTAMP', '', sqlite_schema, flags=re.IGNORECASE)

    cursor.executescript(sqlite_schema)

    # Check if seed data needed
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM issues;")
    issue_count = cursor.fetchone()[0]

    if (user_count == 0 or issue_count == 0) and os.path.exists(seed_path):
        with open(seed_path, 'r', encoding='utf-8') as f:
            seed_sql = f.read()
        try:
            cursor.executescript(seed_sql)
        except Exception as ex:
            logger.debug(f"Seed statement notice: {ex}")

    conn.commit()
    conn.close()
    logger.info(f"SQLite database initialized at {sqlite_file}.")
    return True
