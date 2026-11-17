"""Render measured load data and a local pytest results page for the report."""
import html
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def main():
    output = Path("docs/reports/lab08")
    report = json.loads((output / "load/summary.json").read_text(encoding="utf-8"))
    rows = report["scenarios"]
    assert len(rows) == 4 and not report["quick"], "Full measurements must finish first"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    users = [row["users"] for row in rows]
    for axis, key, title in zip(axes.flat, ["mean_ms", "p95_ms", "rps", "backend_cpu_mean"],
        ["Mean response (ms)", "95th percentile (ms)", "Throughput (requests/s)", "Backend CPU mean (%) — 100% = one core"]):
        values = [row[key] for row in rows]
        axis.plot(users, values, "o-", color="#235c79", linewidth=2)
        axis.set_title(title, fontsize=11)
        axis.set_xticks(users)
        axis.set_xlabel("Virtual users")
        axis.grid(alpha=.2)
        for x, y in zip(users, values):
            axis.annotate(f"{y:.1f}", (x, y), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=9)
        axis.margins(y=.25)
    fig.savefig(output / "load-chart.png", dpi=180)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(10, 4.2))
    axis.set(xlim=(0, 10), ylim=(0, 4.2))
    axis.axis("off")
    boxes = [(0.1,2.3,2.0,1.2,"Browser\nStreamlit forms"), (2.9,2.3,2.2,1.2,"FastAPI\nCRUD + validation"),
             (6.0,2.3,3.8,1.2,"SQLModel → SQLite\nOwner / Pet / Veterinarian\nAppointment / Account / LoginSession"),
             (2.9,.2,2.2,1.2,"Authentication\nBearer + admin/viewer"),
             (6.0,.2,3.8,1.2,"GitHub Actions\npytest / Bandit / Locust\nDocker build + HTTP checks")]
    for x,y,w,h,label in boxes:
        axis.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02",linewidth=1,edgecolor="#235c79",facecolor="#f1f5f8"))
        axis.text(x+w/2,y+h/2,label,ha="center",va="center",fontsize=10)
    for start,end,label,pos in [((2.1,2.9),(2.9,2.9),"HTTP\nJSON",(2.5,3.4)),
                                ((5.1,2.9),(6,2.9),"Session\nSQL",(5.55,3.4)),
                                ((4,2.3),(4,1.4),"Depends",(4.7,1.85))]:
        axis.annotate("",xy=end,xytext=start,arrowprops={"arrowstyle":"<->","color":"#235c79"})
        axis.text(*pos,label,ha="center",va="center",fontsize=9)
    fig.tight_layout()
    fig.savefig(output / "architecture.png",dpi=180)
    plt.close(fig)

    suite = ET.parse(output / "pytest.xml").getroot().find("testsuite")
    tests = list(suite.iter("testcase"))
    failures = int(suite.attrib["failures"]) + int(suite.attrib["errors"])
    body = "".join(f"<tr><td>{html.escape(case.attrib['classname'])}</td><td>{html.escape(case.attrib['name'])}</td><td>{'FAIL' if case.find('failure') is not None else 'PASS'}</td></tr>" for case in tests)
    (output / "pytest-results.html").write_text(f'''<!doctype html><html lang="kk"><meta charset="utf-8"><title>Pytest нәтижелері</title>
<style>body{{font:16px Arial;margin:40px;color:#172b3a}}h1{{font-size:30px}}.summary{{font-size:24px;color:#166534}}table{{border-collapse:collapse;width:100%}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}tr:nth-child(even){{background:#f5f8fa}}td:last-child{{color:#166534}}</style>
<h1>Ветеринарлық клиника — №8 тест нәтижелері</h1><p>Жұматай Нұрсая · ИС 24 А1</p>
<p class="summary">{len(tests)} тест · {failures} қате · {float(suite.attrib['time']):.2f} секунд</p>
<p>Нақты жергілікті pytest.xml нәтижесінен жасалған есеп. Тест базалары негізгі деректерден бөлек.</p>
<table><tr><th>Модуль</th><th>Тест</th><th>Нәтиже</th></tr>{body}</table></html>''', encoding="utf-8")
    print("Figures and pytest HTML created from measured evidence")


if __name__ == "__main__":
    main()
