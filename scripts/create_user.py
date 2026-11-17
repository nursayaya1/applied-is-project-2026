"""Create accounts locally; passwords are entered invisibly, never CLI arguments."""
import argparse
from getpass import getpass
from sqlmodel import Session
from app.db.session import engine, init_db
from app.security import create_account


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--role", choices=["admin", "viewer"], default="viewer")
    args = parser.parse_args()
    password = getpass("Password (12+ characters, a-z, A-Z, digit, symbol): ")
    if password != getpass("Repeat password: "):
        raise SystemExit("Passwords do not match")
    init_db()
    try:
        with Session(engine) as session:
            create_account(session, args.username, password, args.role)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print(f"Created {args.username} ({args.role})")


if __name__ == "__main__":
    main()
