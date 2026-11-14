import tempfile
from pathlib import Path
from PIL import Image
import pytest

from ml.data.convert_annotations import convert_voc_dir_to_yolo, voc_to_yolo_line
from ml.data.prepare_dataset import group_aware_split, create_deterministic_subsets
from ml.data.visualize_annotations import render_annotated_sample

FIXTURES_DIR = Path(__file__).parent / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"
ANNOS_DIR = FIXTURES_DIR / "annotations"


def test_voc_to_yolo_conversion(tmp_path):
    out_labels = tmp_path / "labels"
    stats = convert_voc_dir_to_yolo(
        xml_dir=ANNOS_DIR,
        images_dir=IMAGES_DIR,
        output_labels_dir=out_labels,
        preserve_negative_images=True,
    )

    assert stats["processed_images"] == 8
    assert stats["total_boxes"] == 9
    assert stats["negative_samples"] == 1

    # Check negative file is empty txt
    neg_file = out_labels / "img_07.txt"
    assert neg_file.exists()
    assert neg_file.read_text().strip() == ""

    # Check positive file has valid YOLO normalized values
    pos_file = out_labels / "img_01.txt"
    assert pos_file.exists()
    content = pos_file.read_text().strip()
    parts = content.split()
    assert parts[0] == "0"  # Class 0
    # Center coords and dimensions must be in [0, 1]
    for val in parts[1:]:
        f = float(val)
        assert 0.0 <= f <= 1.0


def test_group_aware_split():
    # Synthetic items belonging to 4 distinct road collection sessions
    items = [
        {"file_name": "frame_1.jpg", "collection_session": "session_A"},
        {"file_name": "frame_2.jpg", "collection_session": "session_A"},
        {"file_name": "frame_3.jpg", "collection_session": "session_B"},
        {"file_name": "frame_4.jpg", "collection_session": "session_B"},
        {"file_name": "frame_5.jpg", "collection_session": "session_C"},
        {"file_name": "frame_6.jpg", "collection_session": "session_D"},
    ]

    train, val, test = group_aware_split(
        items,
        group_key="collection_session",
        train_ratio=0.50,
        val_ratio=0.25,
        test_ratio=0.25,
        seed=42,
    )

    # Verify no session appears in more than one split
    train_sessions = {x["collection_session"] for x in train}
    val_sessions = {x["collection_session"] for x in val}
    test_sessions = {x["collection_session"] for x in test}

    assert len(train_sessions & val_sessions) == 0
    assert len(train_sessions & test_sessions) == 0
    assert len(val_sessions & test_sessions) == 0


def test_deterministic_subsets():
    data = [f"img_{i}" for i in range(100)]
    subsets = create_deterministic_subsets(data, fractions=(0.10, 0.25, 0.50, 1.00), seeds=(42, 123))

    # Test seed 42 subset sizes
    assert len(subsets[42][0.10]) == 10
    assert len(subsets[42][0.25]) == 25
    assert len(subsets[42][0.50]) == 50
    assert len(subsets[42][1.00]) == 100

    # Test determinism
    subsets_repeat = create_deterministic_subsets(data, fractions=(0.10,), seeds=(42,))
    assert subsets[42][0.10] == subsets_repeat[42][0.10]


def test_visualize_annotations(tmp_path):
    out_img_path = tmp_path / "rendered_img_01.jpg"
    annotated = render_annotated_sample(
        image_path=IMAGES_DIR / "img_01.jpg",
        xml_path=ANNOS_DIR / "img_01.xml",
        output_path=out_img_path,
    )

    assert out_img_path.exists()
    assert isinstance(annotated, Image.Image)
    assert annotated.size == (320, 240)
