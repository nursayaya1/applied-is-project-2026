"""Check actual API startup and Streamlit rendering, then stop both servers."""
import os
from pathlib import Path
import subprocess
import sys
import time
import tempfile

import requests
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def wait_for(url, process):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError(f"Server exited with {process.returncode}")
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return response
        except requests.RequestException:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"Server did not become ready: {url}")


if __name__ == "__main__":
    processes = []
    temporary = tempfile.TemporaryDirectory(prefix="clinic-smoke-")
    os.environ["DATABASE_PATH"] = str(Path(temporary.name) / "clinic.db")
    os.environ["BACKEND_URL"] = "http://127.0.0.1:18001"
    try:
        api = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "18001"], cwd=ROOT)
        processes.append(api)
        assert wait_for("http://127.0.0.1:18001/health", api).json() == {"status": "ok"}
        assert requests.get("http://127.0.0.1:18001/docs", timeout=5).status_code == 200
        os.environ["API_URL"] = "http://127.0.0.1:18001"
        page = AppTest.from_file(str(ROOT / "frontend/app.py")).run(timeout=30)
        assert not page.exception, page.exception
        assert not page.error, page.error
        assert len(page.tabs) == 4
        assert len(page.metric) == 4
        ui = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "frontend/app.py",
                               "--server.port", "18501", "--server.address", "127.0.0.1", "--server.headless", "true",
                               "--browser.gatherUsageStats", "false"], cwd=ROOT)
        processes.append(ui)
        assert wait_for("http://127.0.0.1:18501/_stcore/health", ui).text == "ok"
        print("PASS: API startup, Swagger docs, Streamlit render and server health")
    finally:
        for process in processes:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            else:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        temporary.cleanup()
