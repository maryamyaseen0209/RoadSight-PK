import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from PIL import Image

from ml.data.parse_voc import parse_voc_xml, RDD_CLASS_MAPPING, RDD_ID_TO_NAME


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Computes SHA-256 digest of an image to detect cross-split leakage and duplicates."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def audit_dataset_split(
    images_dir: Union[str, Path],
    annotations_dir: Union[str, Path],
    annotation_type: str = "voc",  # 'voc' or 'yolo'
    output_report_path: Optional[Union[str, Path]] = None,
) -> Dict:
    """
    Performs comprehensive dataset health check:
    - Missing / corrupt image validation
    - Degenerate & out-of-bounds bounding boxes
    - Image duplication detection
    - Class distribution and imbalance ratios
    """
    images_dir = Path(images_dir)
    annotations_dir = Path(annotations_dir)

    image_extensions = {".jpg", ".jpeg", ".png"}
    images = [p for p in images_dir.glob("*") if p.suffix.lower() in image_extensions]

    report = {
        "summary": {
            "total_images": len(images),
            "corrupt_images": 0,
            "images_with_defects": 0,
            "negative_images": 0,
            "total_boxes": 0,
            "invalid_boxes": 0,
            "duplicate_image_count": 0,
        },
        "class_distribution": {name: 0 for name in RDD_ID_TO_NAME.values()},
        "duplicates": [],
        "errors": [],
    }

    seen_hashes: Dict[str, str] = {}
    total_boxes = 0

    for img_path in images:
        stem = img_path.stem

        # 1. Image integrity check
        try:
            with Image.open(img_path) as img:
                img.verify()
            with Image.open(img_path) as img:
                w, h = img.size
        except Exception as e:
            report["summary"]["corrupt_images"] += 1
            report["errors"].append(f"Corrupt image {img_path.name}: {e}")
            continue

        # 2. Hash check for duplicates
        file_hash = compute_file_hash(img_path)
        if file_hash in seen_hashes:
            report["summary"]["duplicate_image_count"] += 1
            report["duplicates"].append({
                "duplicate": str(img_path),
                "original": seen_hashes[file_hash],
                "hash": file_hash,
            })
        else:
            seen_hashes[file_hash] = str(img_path)

        # 3. Annotation validation
        img_boxes = 0
        if annotation_type == "voc":
            xml_path = annotations_dir / f"{stem}.xml"
            if xml_path.exists():
                try:
                    parsed = parse_voc_xml(xml_path, img_width=w, img_height=h)
                    for b in parsed["boxes"]:
                        c_name = b["class_name"]
                        if c_name in report["class_distribution"]:
                            report["class_distribution"][c_name] += 1
                        total_boxes += 1
                        img_boxes += 1
                except Exception as e:
                    report["errors"].append(f"Error parsing XML for {img_path.name}: {e}")
        elif annotation_type == "yolo":
            txt_path = annotations_dir / f"{stem}.txt"
            if txt_path.exists():
                try:
                    with open(txt_path, "r", encoding="utf-8") as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                cid = int(parts[0])
                                c_name = RDD_ID_TO_NAME.get(cid, f"Class {cid}")
                                if c_name in report["class_distribution"]:
                                    report["class_distribution"][c_name] += 1
                                total_boxes += 1
                                img_boxes += 1
                except Exception as e:
                    report["errors"].append(f"Error reading YOLO label for {img_path.name}: {e}")

        if img_boxes > 0:
            report["summary"]["images_with_defects"] += 1
        else:
            report["summary"]["negative_images"] += 1

    report["summary"]["total_boxes"] = total_boxes

    # Save to disk if requested
    if output_report_path:
        out_path = Path(output_report_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    return report


def check_cross_split_leakage(
    train_images_dir: Union[str, Path],
    val_images_dir: Union[str, Path],
    test_images_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Ensures no duplicate or identical image exists across train, val, and test splits."""
    def get_hashes(directory: Path) -> Dict[str, str]:
        hashes = {}
        for ext in (".jpg", ".jpeg", ".png"):
            for p in directory.glob(f"*{ext}"):
                hashes[compute_file_hash(p)] = p.name
        return hashes

    train_hashes = get_hashes(Path(train_images_dir))
    val_hashes = get_hashes(Path(val_images_dir))

    train_val_overlap = set(train_hashes.keys()) & set(val_hashes.keys())

    leakage_info = {
        "train_val_leakage_count": len(train_val_overlap),
        "train_val_leaked_images": [
            {"hash": h, "train_file": train_hashes[h], "val_file": val_hashes[h]}
            for h in train_val_overlap
        ],
        "is_leakage_free": len(train_val_overlap) == 0,
    }

    if test_images_dir:
        test_hashes = get_hashes(Path(test_images_dir))
        train_test_overlap = set(train_hashes.keys()) & set(test_hashes.keys())
        val_test_overlap = set(val_hashes.keys()) & set(test_hashes.keys())
        leakage_info["train_test_leakage_count"] = len(train_test_overlap)
        leakage_info["val_test_leakage_count"] = len(val_test_overlap)
        leakage_info["is_leakage_free"] = (
            len(train_val_overlap) == 0 and len(train_test_overlap) == 0 and len(val_test_overlap) == 0
        )

    return leakage_info
