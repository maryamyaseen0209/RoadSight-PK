from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import xml.etree.ElementTree as ET

# Official 4-class RDD2022 defect mapping
RDD_CLASS_MAPPING: Dict[str, int] = {
    "D00": 0,  # Longitudinal Crack
    "D10": 1,  # Transverse Crack
    "D20": 2,  # Alligator Crack
    "D40": 3,  # Pothole
}

RDD_ID_TO_NAME: Dict[int, str] = {
    0: "Longitudinal Crack [D00]",
    1: "Transverse Crack [D10]",
    2: "Alligator Crack [D20]",
    3: "Pothole [D40]",
}


def parse_voc_xml(
    xml_path: Union[str, Path],
    img_width: Optional[int] = None,
    img_height: Optional[int] = None,
    enforce_known_classes_only: bool = True,
) -> Dict:
    """
    Parses a Pascal VOC XML annotation file, extracting image metadata and bounding boxes.
    Enforces the official 4-class defect mapping and clips bounding boxes to image dimensions.

    Args:
        xml_path: Path to the Pascal VOC XML file.
        img_width: Optional width override (if XML size tag is 0 or missing).
        img_height: Optional height override.
        enforce_known_classes_only: If True, ignores labels outside {D00, D10, D20, D40}.

    Returns:
        Dict containing filename, width, height, and list of parsed bounding boxes.
    """
    xml_path = Path(xml_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    filename = root.findtext("filename", default=xml_path.stem + ".jpg")

    size_elem = root.find("size")
    if size_elem is not None:
        try:
            width = int(size_elem.findtext("width", "0"))
            height = int(size_elem.findtext("height", "0"))
        except (ValueError, TypeError):
            width = img_width or 0
            height = img_height or 0
    else:
        width = img_width or 0
        height = img_height or 0

    if width <= 0 and img_width is not None:
        width = img_width
    if height <= 0 and img_height is not None:
        height = img_height

    boxes: List[Dict] = []

    for obj in root.findall("object"):
        raw_name = obj.findtext("name", "").strip()
        # Extract class code if full string provided (e.g., 'D00' or 'D00 - Longitudinal')
        clean_code = raw_name.split()[0].upper()

        if enforce_known_classes_only and clean_code not in RDD_CLASS_MAPPING:
            continue

        class_id = RDD_CLASS_MAPPING.get(clean_code, -1)

        bndbox = obj.find("bndbox")
        if bndbox is None:
            continue

        try:
            xmin = float(bndbox.findtext("xmin", "0"))
            ymin = float(bndbox.findtext("ymin", "0"))
            xmax = float(bndbox.findtext("xmax", "0"))
            ymax = float(bndbox.findtext("ymax", "0"))
        except (ValueError, TypeError):
            continue

        # Clip coordinates to image boundaries if dimensions are known
        if width > 0:
            xmin = max(0.0, min(float(width), xmin))
            xmax = max(0.0, min(float(width), xmax))
        if height > 0:
            ymin = max(0.0, min(float(height), ymin))
            ymax = max(0.0, min(float(height), ymax))

        # Discard degenerate bounding boxes where min >= max
        if xmax <= xmin or ymax <= ymin:
            continue

        boxes.append({
            "class_code": clean_code,
            "class_id": class_id,
            "class_name": RDD_ID_TO_NAME.get(class_id, clean_code),
            "xmin": xmin,
            "ymin": ymin,
            "xmax": xmax,
            "ymax": ymax,
        })

    return {
        "xml_path": str(xml_path),
        "filename": filename,
        "width": width,
        "height": height,
        "has_defects": len(boxes) > 0,
        "boxes": boxes,
    }
