from pathlib import Path
import pytest

from ml.data.parse_voc import parse_voc_xml, RDD_CLASS_MAPPING
from ml.data.audit_dataset import audit_dataset_split, compute_file_hash

FIXTURES_DIR = Path(__file__).parent / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"
ANNOS_DIR = FIXTURES_DIR / "annotations"


def test_parse_voc_classes():
    # Test Class 0 (Longitudinal Crack D00)
    parsed_01 = parse_voc_xml(ANNOS_DIR / "img_01.xml")
    assert parsed_01["has_defects"] is True
    assert len(parsed_01["boxes"]) == 1
    assert parsed_01["boxes"][0]["class_code"] == "D00"
    assert parsed_01["boxes"][0]["class_id"] == 0
    assert "Longitudinal" in parsed_01["boxes"][0]["class_name"]

    # Test Class 3 (Pothole D40)
    parsed_04 = parse_voc_xml(ANNOS_DIR / "img_04.xml")
    assert parsed_04["has_defects"] is True
    assert parsed_04["boxes"][0]["class_code"] == "D40"
    assert parsed_04["boxes"][0]["class_id"] == 3


def test_parse_voc_clipping():
    # img_08 has coordinates xmin=-20, xmax=350 on a 320x240 image
    parsed_08 = parse_voc_xml(ANNOS_DIR / "img_08.xml")
    assert parsed_08["has_defects"] is True
    box = parsed_08["boxes"][0]
    assert box["xmin"] == 0.0  # Clipped from -20 to 0
    assert box["xmax"] == 320.0  # Clipped from 350 to width 320


def test_parse_voc_negative_sample():
    # img_07 is a negative sample with no defect boxes
    parsed_07 = parse_voc_xml(ANNOS_DIR / "img_07.xml")
    assert parsed_07["has_defects"] is False
    assert len(parsed_07["boxes"]) == 0


def test_audit_dataset():
    report = audit_dataset_split(IMAGES_DIR, ANNOS_DIR, annotation_type="voc")
    summary = report["summary"]

    assert summary["total_images"] == 8
    assert summary["corrupt_images"] == 0
    assert summary["negative_images"] == 1
    assert summary["images_with_defects"] == 7
    # Total boxes across img 1-6 and 8: 1+1+1+1+2+2+1 = 9 boxes
    assert summary["total_boxes"] == 9
    assert report["class_distribution"]["Longitudinal Crack [D00]"] >= 3
    assert report["class_distribution"]["Pothole [D40]"] >= 2
