"""Disposable localhost server for HTTP integration, smoke and load tests."""
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager

import requests

ROOT = Path(__file__).resolve().parents[1]


def stop_process(process):
    if process.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


@contextmanager
def test_server(port=18008):
    with tempfile.TemporaryDirectory(prefix="clinic-lab08-") as folder:
        env = dict(os.environ, DATABASE_PATH=str(Path(folder) / "test.db"), SQL_ECHO="0")
        password = secrets.token_urlsafe(24) + "aA1!"
        env["TEST_BOOTSTRAP_PASSWORD"] = password
        setup = """
import os
from sqlmodel import Session
from app.db.session import engine
from app.db.seed import seed_data
from app.security import create_account
seed_data(engine)
with Session(engine) as session:
    create_account(session, 'load_admin', os.environ['TEST_BOOTSTRAP_PASSWORD'], 'admin')
engine.dispose()
"""
        subprocess.run([sys.executable, "-c", setup], cwd=ROOT, env=env, check=True,
                       stdout=subprocess.DEVNULL)
        env.pop("TEST_BOOTSTRAP_PASSWORD")
        with open(Path(folder) / "server.log", "w", encoding="utf-8") as log:
            process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                                        "--host", "127.0.0.1", "--port", str(port), "--no-access-log"],
                                       cwd=ROOT, env=env, stdout=log, stderr=log)
            url = f"http://127.0.0.1:{port}"
            try:
                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError("Test API failed to start; inspect port availability")
                    try:
                        if requests.get(url + "/health", timeout=1).status_code == 200:
                            break
                    except requests.RequestException:
                        pass
                    time.sleep(.2)
                else:
                    raise RuntimeError("Test API startup timed out")
                response = requests.post(url + "/api/auth/login",
                                         json={"username": "load_admin", "password": password}, timeout=10)
                response.raise_for_status()
                yield url, response.json()["access_token"], process
            finally:
                stop_process(process)
