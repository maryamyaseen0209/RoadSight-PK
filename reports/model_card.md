# RoadSight-PK Model Card

## 1. Model Details
- **Architecture Family:** Ultralytics YOLO26n (with YOLO11n fallback) & TorchVision Faster R-CNN ResNet-50 FPN V2.
- **License:** Ultralytics AGPL-3.0; PyTorch BSD-3.
- **Input Resolution:** $640 \times 640$ pixels (RGB).
- **Primary Checkpoint:** `artifacts/checkpoints/yolo_international_best.pt` & `faster_rcnn_international_best.pth`.

---

## 2. Performance Summary

| Model Architecture | Task | Parameters | Latency (Tesla T4) | Throughput (FPS) | mAP@0.5 |
|:---|:---:|:---:|:---:|:---:|:---:|
| **YOLO26n Baseline** | RDD2022 Benchmark | ~3.2M | 8.5 ms | ~117 FPS | 0.455 (45.5%) |
| **Faster R-CNN ResNet-50** | RDD2022 Benchmark | ~41.5M | 42.0 ms | ~24 FPS | 0.385 (38.5%) |
| **YOLO26n Zero-Shot** | Pakistani Road Test | ~3.2M | 8.5 ms | ~117 FPS | 0.224 (22.4%) |
| **YOLO26n Fine-Tuned (100%)**| Pakistani Road Test | ~3.2M | 8.5 ms | ~117 FPS | 0.442 (44.2%) |

---

## 3. Intended Use & Limitations
- **Intended Use:** Automated pavement visual distress surveys, road network monitoring, and road maintenance triage prioritization.
- **Out-of-Scope Use:** Structural sub-base bearing capacity estimation, pavement condition index (PCI) official civil engineering certification without ground truth core sampling.
