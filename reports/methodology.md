# RoadSight-PK Research Methodology

## 1. Overview
RoadSight-PK investigates the cross-domain generalization and local transfer learning of object detection models for automated pavement distress detection. By analyzing domain covariate shift between international benchmarks (RDD2022) and Pakistani roadways, this work quantifies performance degradation and models the sample efficiency curve for localized adaptation.

---

## 2. Experimental Framework

### Phase 1: International Baseline Training (Experiment 1)
- **Objective:** Establish global upper-bound feature representations across multi-country asphalt conditions.
- **Architectures:**
  1. **Ultralytics YOLO26n / YOLO11n:** Single-stage dense anchor-free detector optimizing real-time throughput.
  2. **Faster R-CNN ResNet-50 FPN V2:** Two-stage detector utilizing Region Proposal Networks (RPN) and RoIAlign.
- **Dataset:** RDD2022 multi-country subsets (Japan, India, Czech Republic, Norway, United States).
- **Taxonomy:** 4 standardized classes: `Longitudinal Crack [D00]`, `Transverse Crack [D10]`, `Alligator Crack [D20]`, `Pothole [D40]`.

### Phase 2: Cross-Country Generalization (Experiment 2 — LOCO)
- **Objective:** Quantify geographical domain shift by training on $N-1$ countries and testing zero-shot on the excluded $N$-th country.
- **Metric:**
  $$\text{Domain Gap (\%)} = \frac{\text{mAP}_{\text{in-domain}} - \text{mAP}_{\text{cross-domain}}}{\text{mAP}_{\text{in-domain}}} \times 100$$

### Phase 3: Zero-Shot Target Assessment (Experiment 3)
- **Objective:** Measure direct deployment degradation of international baseline models when evaluated on raw Pakistani road pavement images.

### Phase 4: Data-Efficient Transfer Learning (Experiment 4)
- **Objective:** Determine the sample efficiency curve of local adaptation.
- **Subsets:** 10%, 25%, 50%, and 100% of locally curated Pakistani training data across random seeds (42, 123, 999).
- **Group Splitting:** Group-aware division grouped by `collection_session` to prevent temporal data leakage across sequential video frames.
- **Metric:**
  $$\text{Fine-Tuning Gain (\%)} = \frac{\text{mAP}_{\text{fine-tuned}} - \text{mAP}_{\text{zero-shot}}}{\text{mAP}_{\text{zero-shot}}} \times 100$$

### Phase 5: Speed & Efficiency Profiling (Experiment 5)
- **Objective:** Profile latency (ms) and throughput (FPS) across Tesla T4 GPU and CPU runtimes with 10 warmup iterations and 50 timed iterations.

### Phase 6: Qualitative & Error Diagnostics (Experiment 6)
- **Objective:** Categorize detection errors into False Positives (shadow/oil misidentification), Missed Defects (low contrast hairline fissures), and Bounding Box Misalignments ($\text{IoU} < 0.5$).
