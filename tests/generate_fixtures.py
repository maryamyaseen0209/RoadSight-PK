import io
from pathlib import Path
from PIL import Image

def generate_fixtures(base_dir: Path):
    images_dir = base_dir / "images"
    annos_dir = base_dir / "annotations"
    images_dir.mkdir(parents=True, exist_ok=True)
    annos_dir.mkdir(parents=True, exist_ok=True)

    fixtures_def = [
        ("img_01", [("D00", 50, 30, 80, 200)]),
        ("img_02", [("D10", 40, 100, 280, 130)]),
        ("img_03", [("D20", 80, 60, 240, 180)]),
        ("img_04", [("D40", 120, 90, 200, 160)]),
        ("img_05", [("D00", 30, 20, 60, 180), ("D40", 150, 100, 220, 160)]),
        ("img_06", [("D10", 20, 80, 260, 110), ("D20", 90, 130, 210, 220)]),
        ("img_07", []),  # Negative image with 0 defects
        ("img_08", [("D00", -20, 40, 350, 190)]),  # Out-of-bounds to test clipping
    ]

    for name, boxes in fixtures_def:
        img_path = images_dir / f"{name}.jpg"
        im = Image.new("RGB", (320, 240), color=(100, 100, 100))
        im.save(img_path, "JPEG")

        xml_lines = [
            "<annotation>",
            f"  <filename>{name}.jpg</filename>",
            "  <size>",
            "    <width>320</width>",
            "    <height>240</height>",
            "    <depth>3</depth>",
            "  </size>",
        ]
        for ccode, xmin, ymin, xmax, ymax in boxes:
            xml_lines.extend([
                "  <object>",
                f"    <name>{ccode}</name>",
                "    <bndbox>",
                f"      <xmin>{xmin}</xmin>",
                f"      <ymin>{ymin}</ymin>",
                f"      <xmax>{xmax}</xmax>",
                f"      <ymax>{ymax}</ymax>",
                "    </bndbox>",
                "  </object>",
            ])
        xml_lines.append("</annotation>")

        xml_path = annos_dir / f"{name}.xml"
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write("\n".join(xml_lines) + "\n")

if __name__ == "__main__":
    generate_fixtures(Path(__file__).parent / "fixtures")
    print("Fixtures generated.")
