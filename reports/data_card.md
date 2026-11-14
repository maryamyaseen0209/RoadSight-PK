# RoadSight-PK Data Card

## 1. Dataset Summary
RoadSight-PK combines two primary data sources:
1. **RDD2022 (Road Damage Dataset 2022):** An international crowdsensed benchmark containing road imagery across Japan, India, Czech Republic, Norway, and USA.
2. **Pakistani Road Pavement Dataset:** Locally captured dashboard and smartphone imagery spanning urban arterials, asphalt highways, rural roadways, and unpaved shoulders in Pakistan.

---

## 2. Standardized 4-Class Taxonomy

| Class ID | Code | Name | Description |
|:---:|:---:|:---|:---|
| 0 | `D00` | Longitudinal Crack | Cracks aligned parallel to the centerline or traffic flow |
| 1 | `D10` | Transverse Crack | Cracks extending across the pavement perpendicular to centerline |
| 2 | `D20` | Alligator Crack | Interconnected polygonal pattern caused by repeated load fatigue |
| 3 | `D40` | Pothole | Bowl-shaped depression resulting from structural layer disintegration |

---

## 3. Data Integrity & Ingestion Protocol

- **Annotation Format:** Pascal VOC XML, CVAT COCO 1.0 JSON, and Ultralytics YOLO txt.
- **Negative Control Ingestion:** Defect-free pavement frames are ingested as empty `.txt` label files to train the background class and minimize false positives.
- **Group-Aware Splitting:** Images are partitioned by `collection_session` (driving route / video session ID) so that adjacent frames never cross train, validation, and test splits.
- **Quality Audit:** SHA-256 hash checks prevent cross-split leakage; degenerate bounding boxes with $x_{\min} \ge x_{\max}$ or $y_{\min} \ge y_{\max}$ are stripped, and all coordinates are clipped to native image boundaries.
