import json
from pathlib import Path
from typing import Dict, List, Optional, Union
import xml.etree.ElementTree as ET
from PIL import Image

from ml.data.parse_voc import parse_voc_xml, RDD_CLASS_MAPPING, RDD_ID_TO_NAME


def voc_to_yolo_line(
    class_id: int,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    img_width: int,
    img_height: int,
) -> Optional[str]:
    """Converts pixel coordinates to normalized YOLO format: <class> <x_center> <y_center> <width> <height>."""
    if img_width <= 0 or img_height <= 0:
        return None

    # Calculate center and dimensions
    w = xmax - xmin
    h = ymax - ymin
    cx = xmin + (w / 2.0)
    cy = ymin + (h / 2.0)

    # Normalize to [0, 1]
    norm_cx = max(0.0, min(1.0, cx / img_width))
    norm_cy = max(0.0, min(1.0, cy / img_height))
    norm_w = max(0.0, min(1.0, w / img_width))
    norm_h = max(0.0, min(1.0, h / img_height))

    return f"{class_id} {norm_cx:.6f} {norm_cy:.6f} {norm_w:.6f} {norm_h:.6f}"


def convert_voc_dir_to_yolo(
    xml_dir: Union[str, Path],
    images_dir: Union[str, Path],
    output_labels_dir: Union[str, Path],
    preserve_negative_images: bool = True,
) -> Dict[str, int]:
    """
    Converts a directory of Pascal VOC XML annotations into Ultralytics YOLO txt files.
    Preserves negative images as empty txt files so YOLO learns defect-free pavement.
    """
    xml_dir = Path(xml_dir)
    images_dir = Path(images_dir)
    output_labels_dir = Path(output_labels_dir)
    output_labels_dir.mkdir(parents=True, exist_ok=True)

    xml_files = {p.stem: p for p in xml_dir.glob("*.xml")}
    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg"))

    processed = 0
    total_boxes = 0
    negatives = 0

    for img_path in image_files:
        stem = img_path.stem
        label_out = output_labels_dir / f"{stem}.txt"

        # Determine dimensions
        img_w, img_h = 0, 0
        try:
            with Image.open(img_path) as im:
                img_w, img_h = im.size
        except Exception:
            pass

        if stem in xml_files:
            parsed = parse_voc_xml(xml_files[stem], img_width=img_w, img_height=img_h)
            if img_w == 0:
                img_w = parsed["width"]
            if img_h == 0:
                img_h = parsed["height"]

            lines = []
            for b in parsed["boxes"]:
                line = voc_to_yolo_line(
                    class_id=b["class_id"],
                    xmin=b["xmin"],
                    ymin=b["ymin"],
                    xmax=b["xmax"],
                    ymax=b["ymax"],
                    img_width=img_w,
                    img_height=img_h,
                )
                if line:
                    lines.append(line)
                    total_boxes += 1

            with open(label_out, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + ("\n" if lines else ""))

            if len(lines) == 0:
                negatives += 1
        elif preserve_negative_images:
            # Create empty txt label for negative sample
            with open(label_out, "w", encoding="utf-8") as f:
                f.write("")
            negatives += 1

        processed += 1

    return {
        "processed_images": processed,
        "total_boxes": total_boxes,
        "negative_samples": negatives,
    }


def convert_coco_json_to_yolo(
    coco_json_path: Union[str, Path],
    output_labels_dir: Union[str, Path],
    preserve_negative_images: bool = True,
) -> Dict[str, int]:
    """
    Converts CVAT COCO 1.0 JSON annotations to Ultralytics YOLO format.
    Maps COCO categories to RDD2022 4 classes and preserves empty label files.
    """
    coco_json_path = Path(coco_json_path)
    output_labels_dir = Path(output_labels_dir)
    output_labels_dir.mkdir(parents=True, exist_ok=True)

    with open(coco_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Map category id -> official class id
    cat_map: Dict[int, int] = {}
    for cat in data.get("categories", []):
        cat_name = cat.get("name", "").split()[0].upper()
        if cat_name in RDD_CLASS_MAPPING:
            cat_map[cat["id"]] = RDD_CLASS_MAPPING[cat_name]

    # Map image id -> info
    images_map = {img["id"]: img for img in data.get("images", [])}
    # Group annotations by image_id
    annos_by_img: Dict[int, List] = {img_id: [] for img_id in images_map}
    for ann in data.get("annotations", []):
        img_id = ann.get("image_id")
        if img_id in annos_by_img:
            annos_by_img[img_id].append(ann)

    total_boxes = 0
    negatives = 0

    for img_id, img_info in images_map.items():
        file_name = img_info.get("file_name", f"{img_id}.jpg")
        stem = Path(file_name).stem
        label_out = output_labels_dir / f"{stem}.txt"
        img_w = img_info.get("width", 0)
        img_h = img_info.get("height", 0)

        lines = []
        for ann in annos_by_img[img_id]:
            cat_id = ann.get("category_id")
            if cat_id not in cat_map:
                continue
            official_class_id = cat_map[cat_id]
            # COCO bbox: [x, y, width, height]
            bbox = ann.get("bbox", [])
            if len(bbox) != 4:
                continue
            x, y, w, h = bbox
            xmin, ymin, xmax, ymax = x, y, x + w, y + h

            line = voc_to_yolo_line(
                class_id=official_class_id,
                xmin=xmin,
                ymin=ymin,
                xmax=xmax,
                ymax=ymax,
                img_width=img_w,
                img_height=img_h,
            )
            if line:
                lines.append(line)
                total_boxes += 1

        with open(label_out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))

        if len(lines) == 0:
            negatives += 1

    return {
        "processed_images": len(images_map),
        "total_boxes": total_boxes,
        "negative_samples": negatives,
    }
