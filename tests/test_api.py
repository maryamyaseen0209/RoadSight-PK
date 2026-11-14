import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)


def create_in_memory_image(width: int = 320, height: int = 240, color=(128, 128, 128)) -> bytes:
    """Generates a valid JPEG image in memory."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "RoadSight-PK"


def test_model_endpoint():
    response = client.get("/api/v1/model")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "classes" in data
    assert len(data["classes"]) == 4


def test_metrics_endpoint():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("available", "unavailable")
    assert "master_summary" in data
    assert "exp1_baseline" in data
    assert "recorded_experiments" in data


def test_summary_endpoint():
    response = client.get("/api/v1/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_images_analyzed" in data
    assert "total_damage_detections" in data
    assert "defect_counts_by_class" in data
    assert "active_model" in data


def test_predict_valid_image():
    img_bytes = create_in_memory_image(400, 300)
    files = {"file": ("road_surface.jpg", img_bytes, "image/jpeg")}

    response = client.post("/api/v1/predict?confidence_threshold=0.30", files=files)
    assert response.status_code == 200
    data = response.json()

    assert "run_id" in data
    assert data["image_name"] == "road_surface.jpg"
    assert data["output_image_url"].startswith("/outputs/")
    assert "inference_time_ms" in data
    assert isinstance(data["detections"], list)

    # Verify disk artifact exists
    run_id = data["run_id"]
    output_path = settings.outputs_path / f"{run_id}.jpg"
    assert output_path.exists()


def test_predict_zero_detection_image():
    # Plain smooth image with no distress features
    img_bytes = create_in_memory_image(200, 200, color=(200, 200, 200))
    files = {"file": ("clean_asphalt.png", img_bytes, "image/png")}

    response = client.post("/api/v1/predict", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["total_detections"] >= 0
    assert isinstance(data["detections"], list)


def test_predict_corrupt_byte_stream():
    # Corrupt fake image bytes
    corrupt_bytes = b"NotARealImageHeader1234567890abcdef"
    files = {"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")}

    response = client.post("/api/v1/predict", files=files)
    assert response.status_code == 400
    assert "corrupt or not a valid image" in response.json()["detail"].lower()


def test_predict_invalid_extension():
    # Text file rejection
    txt_content = b"This is a text log file, not a road image."
    files = {"file": ("test.txt", txt_content, "text/plain")}

    response = client.post("/api/v1/predict", files=files)
    assert response.status_code == 400
    assert "invalid file extension" in response.json()["detail"].lower()


def test_history_and_detail_workflow():
    img_bytes = create_in_memory_image()
    files = {"file": ("history_test.jpg", img_bytes, "image/jpeg")}

    pred_res = client.post("/api/v1/predict", files=files)
    assert pred_res.status_code == 200
    run_id = pred_res.json()["run_id"]

    # 1. Retrieve history list
    hist_res = client.get("/api/v1/history?limit=10")
    assert hist_res.status_code == 200
    runs = hist_res.json()
    matching = [r for r in runs if r["id"] == run_id]
    assert len(matching) == 1

    # 2. Retrieve detail
    detail_res = client.get(f"/api/v1/history/{run_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == run_id
    assert detail["image_name"] == "history_test.jpg"
    assert "detections" in detail


def test_history_deletion():
    img_bytes = create_in_memory_image()
    files = {"file": ("delete_test.jpg", img_bytes, "image/jpeg")}

    pred_res = client.post("/api/v1/predict", files=files)
    assert pred_res.status_code == 200
    run_id = pred_res.json()["run_id"]

    # Verify output file was created
    annotated_file = settings.outputs_path / f"{run_id}.jpg"
    assert annotated_file.exists()

    # Delete run
    del_res = client.delete(f"/api/v1/history/{run_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Verify file is deleted on disk
    assert not annotated_file.exists()

    # Verify query now returns 404
    get_res = client.get(f"/api/v1/history/{run_id}")
    assert get_res.status_code == 404
