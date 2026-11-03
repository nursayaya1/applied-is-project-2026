"""Generate the veterinary clinic ER diagram as PNG and editable draw.io."""
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "docs"
OUT.mkdir(exist_ok=True)
tables = [
    ("owner", "Owner / Иесі", 60, 150, ["PK  id : INTEGER", "name : TEXT", "phone : TEXT"]),
    ("pet", "Pet / Жануар", 560, 150, ["PK  id : INTEGER", "name : TEXT", "species : TEXT", "age_years : INTEGER", "FK  owner_id : INTEGER"]),
    ("veterinarian", "Veterinarian / Ветеринар", 60, 600, ["PK  id : INTEGER", "name : TEXT", "specialty : TEXT"]),
    ("appointment", "Appointment / Қабылдау", 560, 600, ["PK  id : INTEGER", "FK  pet_id : INTEGER", "FK  veterinarian_id : INTEGER", "starts_at : DATETIME", "reason : TEXT"]),
]
links = [("owner", "pet"), ("pet", "appointment"), ("veterinarian", "appointment")]
doc = ET.Element("mxfile", host="app.diagrams.net")
diagram = ET.SubElement(doc, "diagram", name="Veterinary Clinic ER", id="clinic-er")
model = ET.SubElement(diagram, "mxGraphModel", grid="1", page="1", pageWidth="1060", pageHeight="1110")
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")
for key, title, x, y, fields in tables:
    cell = ET.SubElement(root, "mxCell", id=key, value=title + "\n\n" + "\n".join(fields),
                         style="rounded=1;whiteSpace=wrap;html=0;fillColor=#f0fdfa;strokeColor=#0f766e;fontSize=18;align=left;spacing=16;", vertex="1", parent="1")
    ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": "420", "height": "330", "as": "geometry"})
for source, target in links:
    cell = ET.SubElement(root, "mxCell", id=source+"-"+target, value="1 : 0..N", edge="1", parent="1", source=source, target=target,
                         style="edgeStyle=orthogonalEdgeStyle;startArrow=ERone;endArrow=ERmany;html=0;fontSize=16;")
    ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
ET.indent(doc)
ET.ElementTree(doc).write(OUT / "er-diagram.drawio", encoding="utf-8", xml_declaration=True)

image = Image.new("RGB", (1060, 1110), "#f8fafc")
draw = ImageDraw.Draw(image)
font_path = "C:/Windows/Fonts/arial.ttf"
font = ImageFont.truetype(font_path, 23)
small = ImageFont.truetype(font_path, 20)
heading = ImageFont.truetype(font_path, 34)
draw.text((60, 35), "Ветеринарлық клиника — ER-диаграмма", font=heading, fill="#134e4a")
draw.text((60, 90), "Иелері, жануарлар, ветеринарлар және қабылдаулар", font=font, fill="#475569")
for key, title, x, y, fields in tables:
    draw.rounded_rectangle((x,y,x+420,y+330), radius=14, fill="white", outline="#0f766e", width=3)
    draw.text((x+18,y+20), title, font=font, fill="#0f766e")
    draw.line((x,y+65,x+420,y+65), fill="#cbd5e1", width=2)
    for index, field in enumerate(fields):
        draw.text((x+18,y+85+index*40), field, font=small, fill="#0f172a")
for y in [315, 765]:
    draw.line((480,y,560,y), fill="#334155", width=3)
    draw.line((495,y-10,495,y+10), fill="#334155", width=2)
    draw.line((540,y,560,y-12), fill="#334155", width=2)
    draw.line((540,y,560,y+12), fill="#334155", width=2)
    draw.text((484,y-38), "1 : 0..N", font=small, fill="#334155")
draw.line((770,480,770,600), fill="#334155", width=3)
draw.line((760,495,780,495), fill="#334155", width=2)
draw.line((770,580,758,600), fill="#334155", width=2)
draw.line((770,580,782,600), fill="#334155", width=2)
draw.text((790,530), "1 : 0..N", font=small, fill="#334155")
draw.text((60, 970), "PK — бастапқы кілт. FK — сыртқы кілт.", font=font, fill="#334155")
draw.text((60, 1010), "1 : 0..N — бір жазбаға нөл немесе бірнеше жазба сәйкес келеді.", font=small, fill="#475569")
draw.text((60, 1050), "Әр қабылдау бір жануарға және бір ветеринарға байланысты.", font=small, fill="#475569")
image.save(OUT / "er-diagram.png")
print("Created veterinary clinic PNG and draw.io diagrams")
