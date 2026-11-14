from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont

from ml.data.parse_voc import parse_voc_xml, RDD_ID_TO_NAME

CLASS_COLORS = {
    0: (59, 130, 246),   # Longitudinal: Blue
    1: (16, 185, 129),  # Transverse: Emerald
    2: (245, 158, 11),  # Alligator: Amber
    3: (239, 68, 68),   # Pothole: Red
}


def draw_bounding_boxes(
    image: Image.Image,
    boxes: List[Dict],
    line_width: int = 3,
) -> Image.Image:
    """Draws colored bounding boxes and class label tags onto a PIL Image."""
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)

    for b in boxes:
        cid = b.get("class_id", -1)
        color = CLASS_COLORS.get(cid, (255, 255, 255))
        label = b.get("class_name") or RDD_ID_TO_NAME.get(cid, f"Class {cid}")

        xmin = b["xmin"]
        ymin = b["ymin"]
        xmax = b["xmax"]
        ymax = b["ymax"]

        # Draw rectangle
        draw.rectangle([xmin, ymin, xmax, ymax], outline=color, width=line_width)

        # Draw label background header
        tag_text = label.split("[")[0].strip()
        draw.rectangle([xmin, max(0, ymin - 16), xmin + len(tag_text) * 7 + 8, ymin], fill=color)
        draw.text((xmin + 4, max(0, ymin - 14)), tag_text, fill=(255, 255, 255))

    return canvas


def render_annotated_sample(
    image_path: Union[str, Path],
    xml_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
) -> Image.Image:
    """Parses Pascal VOC XML and renders bounding boxes directly on the input image."""
    image_path = Path(image_path)
    xml_path = Path(xml_path)

    with Image.open(image_path) as im:
        img_w, img_h = im.size
        parsed = parse_voc_xml(xml_path, img_width=img_w, img_height=img_h)
        annotated = draw_bounding_boxes(im.convert("RGB"), parsed["boxes"])

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        annotated.save(out_p)

    return annotated
