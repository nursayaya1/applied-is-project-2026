"""Run mandated 5/20/50/100 user scenarios with actual Locust and CPU/RAM samples."""
import argparse
import csv
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import psutil
from scripts.test_server import ROOT, test_server, stop_process


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="CI smoke: 5 users for 10 seconds, not full lab evidence")
    parser.add_argument("--output", default="docs/reports/lab08/load")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    scenarios = [(5, 10)] if args.quick else [(5, 60), (20, 120), (50, 180), (100, 180)]
    report = {"started_utc": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
              "python": platform.python_version(), "logical_cpus": psutil.cpu_count(),
              "locust": importlib.metadata.version("locust"), "quick": args.quick,
              "workload": "4 browse : 2 filtered search : 1 create/PUT/delete; wait 0.2–0.8s; login excluded",
              "cpu_definition": "Sum of backend process tree CPU%, 100%=one logical core; load generator excluded",
              "scenarios": []}
    with test_server() as (url, token, server):
        env = dict(os.environ, LOAD_TEST_TOKEN=token)
        for users, duration in scenarios:
            prefix = output / f"users_{users}"
            print(f"START: {users} users / {duration}s", flush=True)
            with open(str(prefix) + ".log", "w", encoding="utf-8") as logfile:
                process = subprocess.Popen([sys.executable, "-m", "locust", "-f", "tests/load/locustfile.py",
                    "--headless", "--host", url, "--users", str(users), "--spawn-rate", str(users),
                    "--run-time", f"{duration}s", "--stop-timeout", "10", "--csv", str(prefix),
                    "--csv-full-history", "--html", str(prefix) + ".html", "--only-summary"],
                    cwd=ROOT, env=env, stdout=logfile, stderr=logfile)
                samples, monitored = [], {}
                started = time.monotonic()
                try:
                    while process.poll() is None:
                        if time.monotonic() - started > duration + 90:
                            raise RuntimeError("Locust exceeded bounded run time")
                        root = psutil.Process(server.pid)
                        cpu, rss = 0.0, 0
                        for item in [root, *root.children(recursive=True)]:
                            try:
                                if item.pid not in monitored:
                                    monitored[item.pid] = item
                                    item.cpu_percent()
                                cpu += monitored[item.pid].cpu_percent()
                                rss += item.memory_info().rss
                            except psutil.NoSuchProcess:
                                continue
                        samples.append({"elapsed_s": round(time.monotonic() - started, 2),
                                        "backend_cpu_percent": cpu, "backend_rss_mb": round(rss / 1024**2, 2)})
                        time.sleep(1)
                finally:
                    stop_process(process)
                if process.returncode:
                    raise RuntimeError(f"Locust failed: inspect {prefix}.log")
            with open(str(prefix) + "_resources.csv", "w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(samples[0]))
                writer.writeheader()
                writer.writerows(samples)
            with open(str(prefix) + "_stats.csv", encoding="utf-8") as stream:
                aggregate = next(row for row in csv.DictReader(stream) if row["Name"] == "Aggregated")
            count, failures = int(aggregate["Request Count"]), int(aggregate["Failure Count"])
            report["scenarios"].append({"users": users, "duration_s": duration, "requests": count,
                "failures": failures, "error_percent": round(100 * failures / count, 3) if count else None,
                "mean_ms": float(aggregate["Average Response Time"]), "p95_ms": float(aggregate["95%"]),
                "rps": float(aggregate["Requests/s"]),
                "backend_cpu_mean": statistics.mean(s["backend_cpu_percent"] for s in samples[1:]),
                "backend_cpu_peak": max(s["backend_cpu_percent"] for s in samples),
                "backend_rss_peak_mb": max(s["backend_rss_mb"] for s in samples)})
            (output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"PASS: {users} users, {count} requests, {failures} failures", flush=True)


if __name__ == "__main__":
    main()
