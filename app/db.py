"""
Database Management Layer for SeemaSetu.
Provides unified access for MySQL (via mysql.connector or PyMySQL)
with automatic fallback to SQLite for local development and offline environments.
Enforces parameterized queries to protect against SQL Injection (CWE-89).
"""

import os
import re
import sqlite3
import logging
from flask import g, current_app

logger = logging.getLogger(__name__)

# Check MySQL Connector availability
try:
    import mysql.connector
    from mysql.connector import cursor as mysql_cursor
    MYSQL_CONNECTOR_AVAILABLE = True
except ImportError:
    MYSQL_CONNECTOR_AVAILABLE = False

# Check PyMySQL availability
try:
    import pymysql
    import pymysql.cursors
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


def get_db_config():
    """Extract DB configuration from app config or environment variables."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    # On serverless platforms like Vercel, the app root is read-only.
    # Default to /tmp for SQLite when running on Vercel unless cloud MySQL is specified.
    if os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        default_sqlite = os.path.join('/tmp', 'seemasetu.db')
    else:
        default_sqlite = os.path.join(base_dir, 'database', 'seemasetu.db')

    return {
        'type': os.getenv('DB_TYPE', 'sqlite').lower(),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'seemasetu_db'),
        'sqlite_path': os.getenv('SQLITE_PATH', default_sqlite)
    }


def get_db():
    """
    Get or initialize the current request database connection.
    Caches the active connection in Flask's request context `g`.
    """
    if 'db' not in g:
        config = get_db_config()
        conn = None
        db_type = config['type']

        if db_type == 'mysql':
            # Attempt 1: mysql-connector-python (official MySQL driver)
            if MYSQL_CONNECTOR_AVAILABLE:
                try:
                    conn = mysql.connector.connect(
                        host=config['host'],
                        port=config['port'],
                        user=config['user'],
                        password=config['password'],
                        database=config['database'],
                        charset='utf8mb4',
                        autocommit=False
                    )
                    g.db_type = 'mysql_connector'
                    logger.info("Connected successfully to MySQL via mysql-connector-python.")
                except Exception as err:
                    logger.warning(f"mysql.connector connection attempt failed ({err}). Trying PyMySQL...")
                    conn = None

            # Attempt 2: PyMySQL (pure-Python fallback)
            if conn is None and PYMYSQL_AVAILABLE:
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
                    g.db_type = 'pymysql'
                    logger.info("Connected successfully to MySQL via PyMySQL.")
                except Exception as err:
                    logger.warning(f"PyMySQL connection attempt failed ({err}). Falling back to SQLite.")
                    conn = None

        if conn is None:
            # Fallback or default: SQLite
            sqlite_file = config['sqlite_path']
            os.makedirs(os.path.dirname(sqlite_file), exist_ok=True)
            conn = sqlite3.connect(sqlite_file)
            conn.row_factory = sqlite3.Row
            # Enforce foreign key constraints in SQLite
            conn.execute("PRAGMA foreign_keys = ON;")
            g.db_type = 'sqlite'

        g.db = conn

    return g.db


def close_db(e=None):
    """Close the active database connection at the end of the request context."""
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception as err:
            logger.debug(f"Error closing DB connection: {err}")


def query_db(sql, args=(), one=False):
    """
    Execute a parameterized SELECT query and return dictionary records.
    Automatically adapts query placeholders (%s for MySQL, ? for SQLite).
    """
    db = get_db()
    db_type = getattr(g, 'db_type', 'sqlite')

    if db_type == 'sqlite':
        translated_sql = sql.replace('%s', '?')
        cursor = db.cursor()
        try:
            cursor.execute(translated_sql, args)
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
        finally:
            cursor.close()
    elif db_type == 'mysql_connector':
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(sql, args)
            result = cursor.fetchall()
        finally:
            cursor.close()
    else:  # pymysql
        with db.cursor() as cursor:
            cursor.execute(sql, args)
            result = cursor.fetchall()

    return (result[0] if result else None) if one else result


def execute_db(sql, args=(), commit=True):
    """
    Execute an INSERT, UPDATE, or DELETE parameterized query.
    Employs transactions with automatic rollback on error.
    Returns the lastrowid or affected rows.
    """
    db = get_db()
    db_type = getattr(g, 'db_type', 'sqlite')
    last_id = None
    rowcount = 0

    try:
        if db_type == 'sqlite':
            translated_sql = sql.replace('%s', '?')
            cursor = db.cursor()
            try:
                cursor.execute(translated_sql, args)
                last_id = cursor.lastrowid
                rowcount = cursor.rowcount
            finally:
                cursor.close()
            if commit:
                db.commit()

        elif db_type == 'mysql_connector':
            cursor = db.cursor()
            try:
                cursor.execute(sql, args)
                last_id = cursor.lastrowid
                rowcount = cursor.rowcount
            finally:
                cursor.close()
            if commit:
                db.commit()

        else:  # pymysql
            with db.cursor() as cursor:
                cursor.execute(sql, args)
                last_id = cursor.lastrowid
                rowcount = cursor.rowcount
            if commit:
                db.commit()

        return last_id if last_id is not None and last_id > 0 else rowcount

    except Exception as exc:
        if commit and hasattr(db, 'rollback'):
            try:
                db.rollback()
                logger.error(f"Transaction rolled back due to error: {exc}")
            except Exception:
                pass
        raise exc


def init_db(app=None):
    """
    Initialize database schema and populate demonstration seed records if needed.
    Works for both MySQL and SQLite.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    schema_path = os.path.join(base_dir, 'database', 'schema.sql')
    if not os.path.exists(schema_path):
        schema_path = os.path.join(base_dir, 'sql', 'schema.sql')

    seed_path = os.path.join(base_dir, 'database', 'seed_data.sql')

    config = get_db_config()
    db_type = config['type']

    if db_type == 'mysql':
        # Try MySQL Connector first, then PyMySQL
        conn = None
        if MYSQL_CONNECTOR_AVAILABLE:
            try:
                conn = mysql.connector.connect(
                    host=config['host'],
                    port=config['port'],
                    user=config['user'],
                    password=config['password'],
                    database=config['database'],
                    charset='utf8mb4',
                    autocommit=True
                )
            except Exception:
                conn = None

        if conn is None and PYMYSQL_AVAILABLE:
            try:
                conn = pymysql.connect(
                    host=config['host'],
                    port=config['port'],
                    user=config['user'],
                    password=config['password'],
                    database=config['database'],
                    autocommit=True,
                    charset='utf8mb4'
                )
            except Exception:
                conn = None

        if conn is not None:
            try:
                cursor = conn.cursor()
                with open(schema_path, 'r', encoding='utf-8') as f:
                    statements = f.read().split(';')
                    for stmt in statements:
                        if stmt.strip():
                            cursor.execute(stmt)

                # Check if seed required
                cursor.execute("SELECT COUNT(*) FROM users;")
                row = cursor.fetchone()
                count = row[0] if isinstance(row, tuple) else row['COUNT(*)']
                if count == 0 and os.path.exists(seed_path):
                    with open(seed_path, 'r', encoding='utf-8') as f:
                        seed_stmts = f.read().split(';')
                        for stmt in seed_stmts:
                            if stmt.strip():
                                cursor.execute(stmt)

                cursor.close()
                conn.close()
                logger.info("MySQL database schema and baseline verified.")
                return True
            except Exception as e:
                logger.warning(f"MySQL initialization encountered error ({e}); proceeding with SQLite fallback.")

    # SQLite Setup & Conversion
    sqlite_file = config['sqlite_path']
    os.makedirs(os.path.dirname(sqlite_file), exist_ok=True)
    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Adapt MySQL DDL for SQLite compatibility
    sqlite_schema = schema_sql
    sqlite_schema = re.sub(r'INT AUTO_INCREMENT PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', sqlite_schema, flags=re.IGNORECASE)
    sqlite_schema = re.sub(r'ENGINE=InnoDB[^;]*', '', sqlite_schema, flags=re.IGNORECASE)
    sqlite_schema = re.sub(r'ON UPDATE CURRENT_TIMESTAMP', '', sqlite_schema, flags=re.IGNORECASE)

    for stmt in sqlite_schema.split(';'):
        if stmt.strip():
            cursor.execute(stmt)

    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]

    if user_count == 0 and os.path.exists(seed_path):
        with open(seed_path, 'r', encoding='utf-8') as f:
            seed_sql = f.read()
        for stmt in seed_sql.split(';'):
            if stmt.strip():
                try:
                    cursor.execute(stmt)
                except Exception as ex:
                    logger.debug(f"Seed statement notice: {ex}")

    conn.commit()
    conn.close()
    logger.info(f"SQLite database initialized at: {sqlite_file}")
    return True
