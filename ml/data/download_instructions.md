# RoadSight-PK: Dataset Download & Ingestion Guide

This document defines the download instructions, dataset schemas, and annotation guidelines for both the international benchmark dataset (RDD2022) and the local Pakistani pavement dataset.

---

## 1. RDD2022 (International Benchmark Dataset)

The **RDD2022** (Road Damage Dataset 2022) dataset provides annotated road pavement distress images collected across multiple countries.

* **DOI / Source URL**: [https://doi.org/10.6084/m9.figshare.21431547.v1](https://doi.org/10.6084/m9.figshare.21431547.v1)
* **Target Countries**:
  - `Japan`
  - `India`
  - `Czech`
  - `Norway`
  - `United_States`
  - `China_MotorBike`
  - `China_Drone`

### Directory Layout for Ingestion
Extract the downloaded archives into `data/external/RDD2022/`:
```text
data/external/RDD2022/
├── Japan/
│   ├── annotations/xmls/
│   └── images/
├── India/
│   ├── annotations/xmls/
│   └── images/
├── Czech/
│   ├── annotations/xmls/
│   └── images/
├── Norway/
│   ├── annotations/xmls/
│   └── images/
└── United_States/
    ├── annotations/xmls/
    └── images/
```

### Standardized 4-Class Mapping
| Class ID | Code | Defect Category | Description |
|:---:|:---:|:---|:---|
| **0** | `D00` | Longitudinal Crack | Cracks parallel to the road centerline |
| **1** | `D10` | Transverse Crack | Cracks perpendicular to the road centerline |
| **2** | `D20` | Alligator Crack | Interconnected polygonal cracks from fatigue |
| **3** | `D40` | Pothole | Bowl-shaped cavity resulting from pavement disintegration |

*Note: Other defect types present in RDD2022 (e.g., crosswalk blur `D30`, repair marks `D50`) are ignored to maintain focus on primary structural damage.*

---

## 2. Pakistani Road Dataset Metadata Specification

For local Pakistani road data collected via dashcams, smartphones, or inspection rigs, store raw images in `data/local/raw/images/` and catalog them in `data/local/raw/metadata.csv`.

### `metadata.csv` Required Schema
```csv
image_id,file_name,collection_session,road_type,lighting_condition,weather_condition,capture_device,location_region,image_width,image_height,annotation_status
PK_0001,PK_0001.jpg,session_lahore_ringroad_01,asphalt_highway,bright_sunlight,clear,GoPro_Hero11,Punjab_Lahore,1920,1080,annotated
PK_0002,PK_0002.jpg,session_lahore_ringroad_01,asphalt_highway,shadowed,clear,GoPro_Hero11,Punjab_Lahore,1920,1080,annotated
PK_0003,PK_0003.jpg,session_gt_road_gujranwala_02,urban_arterial,overcast,cloudy,Galaxy_S23,Punjab_Gujranwala,1920,1080,negative_control
```

### Column Definitions
1. `image_id`: Unique alphanumeric identifier (e.g., `PK_0001`).
2. `file_name`: Basename of the image file in `images/`.
3. `collection_session`: Driving route/session identifier used for **group-aware train/test splitting** to prevent temporal leakage between consecutive frames.
4. `road_type`: `asphalt_highway`, `urban_arterial`, `rural_road`, or `unpaved_shoulder`.
5. `lighting_condition`: `bright_sunlight`, `shadowed`, `overcast`, `dusk`, or `night_illuminated`.
6. `weather_condition`: `clear`, `hazy`, `cloudy`, or `wet`.
7. `capture_device`: Camera hardware description.
8. `location_region`: Geographic province/city (e.g., `Punjab_Lahore`, `Sindh_Karachi`, `KPK_Peshawar`).
9. `image_width`: Native pixel width.
10. `image_height`: Native pixel height.
11. `annotation_status`: `annotated`, `unannotated`, or `negative_control` (defect-free pavement).

---

## 3. CVAT Annotation Protocol

All Pakistani road pavement images must be annotated using **Computer Vision Annotation Tool (CVAT)**.

* **Tool URL**: [https://www.cvat.ai/](https://www.cvat.ai/)
* **Project Labels Setup**:
  1. `D00` (Longitudinal Crack)
  2. `D10` (Transverse Crack)
  3. `D20` (Alligator Crack)
  4. `D40` (Pothole)

### Bounding Box Rules
* Fit tightly around the crack extent or pothole cavity with no excessive road padding.
* If multiple hairline cracks form an alligator network, annotate the bounding envelope as `D20` rather than individual `D00`/`D10` lines.
* Negative road images (defect-free surface) should be saved without bounding boxes; conversion scripts will produce empty `.txt` files to train negative control recognition.
* Export format: **CVAT for Images 1.1** (XML) or **COCO 1.0** (JSON).
