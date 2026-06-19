"""
Create users in the database.

Usage:
    python scripts/seed_users.py
    # Follows prompts for username, password, role

    # Or create multiple:
    python scripts/seed_users.py --username admin --password admin123 --role admin
    python scripts/seed_users.py --username alice --password pass123 --role editor
"""

import sys
import uuid
import os
import argparse

# Ensure parent directory (/app) is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, SQLModel, select

from app.config import settings
from app.database import SessionFactory
from app.models.user import User
from app.services.auth_service import hash_password


def create_user(username: str, password: str, role: str = "editor") -> User:
    with SessionFactory() as db:
        # Check if user exists
        existing = db.exec(select(User).where(User.username == username)).first()
        if existing:
            print(f"User '{username}' already exists. Skipping.")
            return existing

        user = User(
            id=uuid.uuid4(),
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"✅ Created user: {user.username} (role: {user.role})")
        return user


def interactive_seed():
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    role = input("Role (editor/admin) [editor]: ").strip() or "editor"
    return create_user(username, password, role)


def main():
    # Ensure tables exist
    SQLModel.metadata.create_all(SessionFactory.kw["bind"])

    parser = argparse.ArgumentParser(description="Create dashboard users")
    parser.add_argument("--username", "-u", help="Username")
    parser.add_argument("--password", "-p", help="Password")
    parser.add_argument("--role", "-r", default="editor", help="Role (editor/admin)")
    args = parser.parse_args()

    if args.username and args.password:
        create_user(args.username, args.password, args.role)
    else:
        print("No username/password provided. Enter interactively:\n")
        interactive_seed()


if __name__ == "__main__":
    main()
