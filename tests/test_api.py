import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app

client = TestClient(app)


def create_test_image_bytes(format="JPEG") -> bytes:
    """Generates a small in-memory test image."""
    img = Image.new("RGB", (320, 240), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf.getvalue()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "RoadSight-PK API"
    assert "health" in data


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "RoadSight-PK"
    assert "version" in data


def test_model_endpoint():
    response = client.get("/api/v1/model")
    assert response.status_code == 200
    data = response.json()
    assert "classes" in data
    # Enforce 4 official classes
    assert len(data["classes"]) == 4
    assert "0" in data["classes"] or 0 in data["classes"]
    assert "Pothole [D40]" in str(data["classes"])


def test_metrics_unavailable_when_not_generated():
    """Metrics endpoint MUST return status 'unavailable' rather than hardcoded numbers."""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unavailable"
    assert data["metrics"] is None


def test_predict_and_history_workflow():
    img_bytes = create_test_image_bytes()
    files = {"file": ("test_road.jpg", img_bytes, "image/jpeg")}

    # 1. Run prediction
    predict_res = client.post("/api/v1/predict?confidence=0.30", files=files)
    assert predict_res.status_code == 200
    predict_data = predict_res.json()
    assert "run_id" in predict_data
    assert predict_data["image_name"] == "test_road.jpg"
    assert "inference_time_ms" in predict_data
    assert isinstance(predict_data["detections"], list)

    run_id = predict_data["run_id"]

    # 2. Query history to confirm persistence
    history_res = client.get("/api/v1/history?limit=10")
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert isinstance(history_data, list)
    matching = [r for r in history_data if r["id"] == run_id]
    assert len(matching) == 1
    assert matching[0]["image_name"] == "test_road.jpg"

    # 3. Query summary to verify aggregation
    summary_res = client.get("/api/v1/summary")
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["total_runs"] >= 1
    assert "defect_counts_by_class" in summary_data
    assert "average_inference_time_ms" in summary_data


def test_predict_rejects_invalid_file_type():
    txt_content = b"This is not an image file"
    files = {"file": ("notes.txt", txt_content, "text/plain")}
    response = client.post("/api/v1/predict", files=files)
    assert response.status_code == 400
