"""
SeemaSetu — Secure Initial Administrator Account Provisioning CLI.
Creates or upgrades an administrator account without hardcoding credentials in source code.
Usage:
  python create_admin.py
  (or via environment variables: ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL, ADMIN_NAME)
"""

import os
import sys
import getpass
from werkzeug.security import generate_password_hash
from app import create_app
from app.db import query_db, execute_db
from app.utils import log_audit


def main():
    print("=" * 72)
    print("  SeemaSetu — Administrator Provisioning Utility")
    print("  Border Infrastructure Monitoring and Maintenance System")
    print("=" * 72)

    app = create_app()
    with app.app_context():
        # Check environment variables first (for headless CI/CD), otherwise prompt interactively
        username = os.environ.get('ADMIN_USERNAME')
        if not username:
            try:
                username = input("Enter admin username [default: admin]: ").strip() or "admin"
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled.")
                sys.exit(1)

        email = os.environ.get('ADMIN_EMAIL')
        if not email:
            try:
                email = input(f"Enter admin email [default: {username}@seemasetu.gov.in]: ").strip() or f"{username}@seemasetu.gov.in"
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled.")
                sys.exit(1)

        full_name = os.environ.get('ADMIN_NAME')
        if not full_name:
            try:
                full_name = input("Enter administrator full name [default: Chief Infrastructure Officer]: ").strip() or "Chief Infrastructure Officer"
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled.")
                sys.exit(1)

        password = os.environ.get('ADMIN_PASSWORD')
        if not password:
            try:
                password = getpass.getpass("Enter secure password (min 8 characters): ").strip()
                confirm = getpass.getpass("Confirm secure password: ").strip()
                if password != confirm:
                    print("Error: Passwords do not match. Aborting.")
                    sys.exit(1)
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled.")
                sys.exit(1)

        if len(password) < 8:
            print("Error: Administrator password must be at least 8 characters in length for security.")
            sys.exit(1)

        # Hash password using scrypt
        password_hash = generate_password_hash(password)

        # Check existing user
        existing = query_db("SELECT id, username, role FROM users WHERE username = %s OR email = %s", (username, email), one=True)
        if existing:
            print(f"User '{existing['username']}' already exists (ID: {existing['id']}, Current Role: {existing['role']}).")
            try:
                update_choice = input("Promote/update existing account to 'admin' and update password? (y/N): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled.")
                sys.exit(1)

            if update_choice in ('y', 'yes'):
                execute_db(
                    """
                    UPDATE users 
                    SET password_hash = %s, role = 'admin', is_active = 1, full_name = %s
                    WHERE id = %s
                    """,
                    (password_hash, full_name, existing['id'])
                )
                log_audit('ADMIN_UPDATED', 'User', existing['id'], f"Administrator credentials updated for @{username}", existing['id'], username)
                print(f"[SUCCESS] User '{username}' promoted to Administrator with updated credentials.")
            else:
                print("No changes made. Exiting.")
                sys.exit(0)
        else:
            user_id = execute_db(
                """
                INSERT INTO users (username, email, password_hash, full_name, role, department, badge_number, is_active)
                VALUES (%s, %s, %s, %s, 'admin', 'Border Infrastructure Command HQ', 'HQ-CMD-01', 1)
                """,
                (username, email, password_hash, full_name)
            )
            log_audit('ADMIN_CREATED', 'User', user_id, f"Initial Administrator account created: @{username}", user_id, username)
            print(f"[SUCCESS] Administrator account '@{username}' successfully created with ID {user_id}.")

        print("=" * 72)
        print("  Database is ready. You may now sign in at /auth/login.")
        print("=" * 72)


if __name__ == '__main__':
    main()
