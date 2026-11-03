"""Generate matching editable draw.io and PNG diagrams. Requires Pillow."""
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
OUT.mkdir(exist_ok=True)
tables = [
    ("category", "Category / Санат", 60, 160, ["PK  id : INTEGER", "name : TEXT"]),
    ("product", "Product / Тауар", 540, 160, ["PK  id : INTEGER", "name : TEXT", "price_tiyn : INTEGER", "quantity : INTEGER", "FK  category_id : INTEGER", "FK  supplier_id : INTEGER"]),
    ("supplier", "Supplier / Жеткізуші", 1030, 160, ["PK  id : INTEGER", "name : TEXT", "phone : TEXT"]),
]
doc = ET.Element("mxfile", host="app.diagrams.net")
diagram = ET.SubElement(doc, "diagram", name="Warehouse ER", id="warehouse-er")
model = ET.SubElement(diagram, "mxGraphModel", grid="1", page="1", pageWidth="1500", pageHeight="700")
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")
for key, title, x, y, fields in tables:
    cell = ET.SubElement(root, "mxCell", id=key, value=title + "\n\n" + "\n".join(fields),
                         style="rounded=1;whiteSpace=wrap;html=0;fillColor=#eff6ff;strokeColor=#2563eb;fontSize=18;align=left;spacing=16;", vertex="1", parent="1")
    ET.SubElement(cell, "mxGeometry", {"x":str(x), "y":str(y), "width":"370", "height":"330", "as":"geometry"})
for key, source in [("category-product", "category"), ("supplier-product", "supplier")]:
    cell = ET.SubElement(root, "mxCell", id=key, value="1 : 0..N", edge="1", parent="1", source=source, target="product",
                         style="edgeStyle=orthogonalEdgeStyle;startArrow=ERone;endArrow=ERmany;html=0;fontSize=16;")
    ET.SubElement(cell, "mxGeometry", {"relative":"1", "as":"geometry"})
ET.indent(doc)
ET.ElementTree(doc).write(OUT / "er-diagram.drawio", encoding="utf-8", xml_declaration=True)

image = Image.new("RGB", (1460, 650), "#f8fafc")
draw = ImageDraw.Draw(image)
font_path = Path("C:/Windows/Fonts/arial.ttf")
font = ImageFont.truetype(str(font_path), 22)
small = ImageFont.truetype(str(font_path), 20)
heading = ImageFont.truetype(str(font_path), 34)
draw.text((60, 40), "Қоймадағы тауарларды есепке алу — ER-диаграмма", font=heading, fill="#0f172a")
draw.text((60, 95), "Әр тауар бір санатқа және бір жеткізушіге тиесілі", font=font, fill="#475569")
for key, title, x, y, fields in tables:
    draw.rounded_rectangle((x,y,x+370,y+330), radius=14, fill="white", outline="#2563eb", width=3)
    draw.text((x+18,y+20), title, font=font, fill="#1e40af")
    draw.line((x,y+65,x+370,y+65), fill="#cbd5e1", width=2)
    for index, field in enumerate(fields):
        draw.text((x+18,y+85+index*36), field, font=small, fill="#0f172a")
for x1,x2 in [(430,540),(1030,910)]:
    draw.line((x1,325,x2,325), fill="#334155", width=3)
    direction=1 if x2>x1 else -1
    draw.line((x2-direction*18,325,x2,312), fill="#334155", width=2)
    draw.line((x2-direction*18,325,x2,338), fill="#334155", width=2)
    draw.text((min(x1,x2)+6,283), "1 : 0..N", font=small, fill="#334155")
draw.text((60, 545), "PK — бастапқы кілт     FK — сыртқы кілт     1 : 0..N — бірден нөл не көпке байланыс", font=font, fill="#334155")
draw.text((60, 590), "Баға тиынмен сақталады: 35000 тиын = 350 теңге. Саны мен бағасы теріс болмайды.", font=small, fill="#475569")
image.save(OUT / "er-diagram.png")
print("Created docs/er-diagram.drawio and docs/er-diagram.png")
