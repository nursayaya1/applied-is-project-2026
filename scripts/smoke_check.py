"""Check authenticated API + UI against an isolated seeded database."""
import os
import subprocess
import sys
import requests
from streamlit.testing.v1 import AppTest
from scripts.test_server import ROOT, test_server, stop_process


def main():
    with test_server(18001) as (url, token, api):
        assert requests.get(url + "/docs", timeout=5).status_code == 200
        page = AppTest.from_file(str(ROOT / "frontend/app.py"), default_timeout=30)
        os.environ["BACKEND_URL"] = url
        page.session_state["access_token"] = token
        page.session_state["user"] = {"username": "load_admin", "role": "admin"}
        page.run()
        assert not page.exception and not page.error
        assert len(page.tabs) == 4 and len(page.metric) == 4
        ui = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "frontend/app.py",
                               "--server.port", "18501", "--server.address", "127.0.0.1",
                               "--server.headless", "true", "--browser.gatherUsageStats", "false"], cwd=ROOT)
        try:
            import time
            for _ in range(100):
                if ui.poll() is not None:
                    raise RuntimeError("Streamlit exited")
                try:
                    if requests.get("http://127.0.0.1:18501/_stcore/health", timeout=1).status_code == 200:
                        break
                except requests.RequestException:
                    pass
                time.sleep(.2)
            else:
                raise RuntimeError("Streamlit startup timed out")
            print("PASS: authenticated API, Swagger, UI rendering and Streamlit health")
        finally:
            stop_process(ui)


if __name__ == "__main__":
    main()
