"""Run from the project root: python seed.py. SQL logs are enabled by default."""
import os
import sys

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

os.environ.setdefault("SQL_ECHO", "1")

from app.db.seed import seed_data

if __name__ == "__main__":
    print("New demo records:", seed_data())
