# RoadSight-PK: Cross-Domain Generalization and Local Adaptation of Deep Learning Models for Road Damage Detection

---

## 1. Abstract
Automated visual assessment of roadway pavement distress is vital for civil infrastructure longevity and transport safety. While modern deep object detectors achieve competitive accuracy on high-income benchmark datasets, their real-world transferability to developing road networks remains under-explored. This research presents **RoadSight-PK**, a rigorous investigation into the cross-domain generalization and local adaptation of deep learning models for road distress localization and classification. Evaluating both single-stage (Ultralytics YOLO26n) and two-stage (Faster R-CNN with ResNet-50 FPN) architectures, we establish an international baseline on the Crowdsensing-based Road Damage Dataset (RDD2022) with a top validation $\text{mAP@0.5}$ of **0.455** (45.5%) at **8.5 ms** latency (~117 FPS on a Tesla T4 GPU). When deployed zero-shot onto Pakistani roadways, severe domain covariate shift induces a **50.77% performance degradation**, dropping $\text{mAP@0.5}$ to **0.224** (22.4%). We systematically evaluate data-efficient transfer learning with 10%, 25%, 50%, and 100% local Pakistani pavement data, demonstrating that fine-tuning with 100% local imagery achieves an $\text{mAP@0.5}$ of **0.442** (a **+97.32% relative gain** over zero-shot). An integrated full-stack web platform consisting of a FastAPI inference engine and a React/Vite analytics dashboard operationalizes the research findings for scalable infrastructure asset monitoring.

---

## 2. Introduction
Pavement distress monitoring traditionally relies on manual visual inspections or specialized automated road profilers (ARAN vehicles) equipped with expensive LiDAR and stereoscopic cameras. In lower-middle-income countries such as Pakistan, constrained municipal budgets and high operational costs impede regular survey intervals. Recent advances in computer vision provide a cost-effective alternative by processing dashboard camera and smartphone video feeds. However, models trained in high-income regions fail when exposed to developing countries due to unpaved road margins, distinct asphalt aggregates, severe pothole morphology, and extreme tropical lighting variations.

---

## 3. Problem Statement
Despite high reported accuracies in global road damage challenges, standard defect detection models suffer catastrophic accuracy loss when deployed in regions characterized by different geographical, environmental, and infrastructure profiles. Specifically, in Pakistan:
1. Pavement surfaces exhibit high visual variance (e.g., uneven bituminous patches, dirt road shoulders).
2. Lighting conditions feature high-contrast shadow lines from roadside vegetation and intense midday solar glare.
3. Crack morphologies are frequently obscured by fine dust or mud deposits.
Without systematic quantification of this domain gap and targeted transfer learning strategies, computer vision models cannot be reliably integrated into local road asset management programs.

---

## 4. Research Objectives
This study addresses four primary research objectives:
- **RO1:** Establish a reproducible baseline on the multi-country RDD2022 benchmark across one-stage and two-stage detector paradigms.
- **RO2:** Quantify performance drop resulting from cross-country domain shift using Leave-One-Country-Out (LOCO) cross-validation and zero-shot Pakistani evaluation.
- **RO3:** Map the sample efficiency learning curve for localized Pakistani road transfer learning across deterministic subsets (10%, 25%, 50%, and 100%).
- **RO4:** Develop and deploy an end-to-end, reproducible microservices architecture combining FastAPI, SQLite persistence, and an interactive React/Recharts dashboard.

---

## 5. Literature Review
Pavement distress detection has progressed from classical morphological edge filtering and Gabor wavelet transforms to deep Convolutional Neural Networks (CNNs). Early deep learning approaches framed road inspection as an image classification task, categorizing image patches into cracked or non-cracked surfaces (Zhang et al., 2016). The release of the Road Damage Dataset series (Arya et al., 2020; RDD2022) shifted the benchmark toward bounding-box localization. While YOLOv5, YOLOv8, and Faster R-CNN achieved solid results on RDD2020/2022, recent studies highlight that convolutional feature extractors overfit to country-specific background textures and camera mounting angles. Domain adaptation techniques—such as adversarial domain alignment and sample-efficient fine-tuning—have emerged as essential requirements for cross-regional deployment.

---

## 6. Dataset Description
The experimental pipeline integrates two datasets:
1. **RDD2022 International Benchmark:** Contains over 47,000 pavement images captured in Japan, India, Czech Republic, Norway, and the United States via vehicle-mounted smartphones.
2. **Pakistani Road Pavement Dataset:** Curated road imagery captured across major highways, urban arterials (Lahore, Karachi, Gujranwala), and secondary rural routes in Pakistan under variable solar lighting.

### Standardized 4-Class Taxonomy
To ensure academic consistency, annotations adhere to the official RDD2022 4-class taxonomy:
- **Class 0 (`D00`):** Longitudinal Crack (parallel to centerline)
- **Class 1 (`D10`):** Transverse Crack (perpendicular to centerline)
- **Class 2 (`D20`):** Alligator / Fatigue Crack (interconnected polygonal network)
- **Class 3 (`D40`):** Pothole (bowl-shaped structural depression)

---

## 7. Methodology
The research methodology is partitioned into four modular stages:
1. **Dataset Engineering:** VOC XML parsing, coordinate clipping, negative control preservation, and group-aware splitting.
2. **Model Training:** Training YOLO26n and Faster R-CNN ResNet-50 FPN on the international benchmark on a Tesla T4 GPU.
3. **Cross-Domain Evaluation:** LOCO testing and zero-shot deployment onto Pakistani pavement test splits.
4. **Local Adaptation & Profiling:** Transfer learning with frozen backbones and speed/latency profiling.

---

## 8. Data Preprocessing
- **Coordinate Clipping:** Bounding boxes exceeding image boundaries $[0, W]$ and $[0, H]$ are clamped. Degenerate boxes ($x_{\min} \ge x_{\max}$) are purged.
- **Negative Sample Preservation:** Images devoid of surface distress are retained with empty `.txt` label files to train the background class and prevent runaway false-positive rates.
- **Group-Aware Splitting:** Road datasets often consist of consecutive video frames. To eliminate spatial-temporal leakage, frames from the same `collection_session` are constrained exclusively to one split (Train, Val, or Test).

---

## 9. Model Architectures
- **Ultralytics YOLO26n / YOLO11n:** Single-stage dense detector utilizing a CSPDarknet backbone, Path Aggregation Network (PANet) neck, and decoupled anchor-free detection heads with Complete IoU (CIoU) loss.
- **Faster R-CNN ResNet-50 FPN V2:** Two-stage detector. An initial Region Proposal Network (RPN) generates region proposals; RoIAlign extracts fixed-size feature maps, and fully connected heads classify proposals into 5 classes (4 defect classes + background).

---

## 10. Experimental Design

| Experiment ID | Model Architecture | Training Data | Evaluation Data | Objective |
|:---|:---|:---|:---|:---|
| **Exp 1** | YOLO26n vs Faster R-CNN | RDD2022 Multi-Country | RDD2022 Test Split | Establish baseline benchmark |
| **Exp 2** | YOLO26n (LOCO) | $N-1$ Countries | Excluded Country | Measure geographic domain shift |
| **Exp 3** | YOLO26n Baseline | RDD2022 Multi-Country | Pakistani Road Test | Measure zero-shot domain drop |
| **Exp 4** | YOLO26n Transfer | 10%, 25%, 50%, 100% PK Data | Pakistani Road Test | Evaluate transfer learning curve |
| **Exp 5** | YOLO vs Faster R-CNN | Pretrained Checkpoints | Synthetic Stream | Latency, FPS & Pareto frontier |
| **Exp 6** | YOLO26n Fine-Tuned | Pakistani 100% Checkpoint | Error Test Subset | Qualitative error analysis |

---

## 11. Evaluation Metrics
- **Mean Average Precision ($\text{mAP@0.5}$ and $\text{mAP@0.5:0.95}$)**
- **Precision, Recall, and $F_1$-Score**
- **Domain Gap Percentage:**
  $$\text{Domain Gap (\%)} = \frac{\text{mAP}_{\text{in-domain}} - \text{mAP}_{\text{cross-domain}}}{\text{mAP}_{\text{in-domain}}} \times 100$$
- **Fine-Tuning Improvement:**
  $$\text{Gain (\%)} = \frac{\text{mAP}_{\text{fine-tuned}} - \text{mAP}_{\text{zero-shot}}}{\text{mAP}_{\text{zero-shot}}} \times 100$$

---

## 12. Results

### Summary of Experimental Metrics

| Experiment | Model | Split / Target | mAP@0.5 | Latency (ms) | Throughput (FPS) |
|:---|:---|:---|:---:|:---:|:---:|
| **Exp 1 (YOLO)** | YOLO26n | RDD2022 Test | **0.455** | **8.5 ms** | **117.6 FPS** |
| **Exp 1 (FRCNN)** | Faster R-CNN | RDD2022 Test | 0.385 | 42.0 ms | 23.8 FPS |
| **Exp 3 (Zero-Shot)** | YOLO26n Baseline | Pakistani Test | 0.224 | 8.5 ms | 117.6 FPS |
| **Exp 4 (10% Data)** | YOLO26n Transfer | Pakistani Test | 0.258 | 8.5 ms | 117.6 FPS |
| **Exp 4 (25% Data)** | YOLO26n Transfer | Pakistani Test | 0.312 | 8.5 ms | 117.6 FPS |
| **Exp 4 (50% Data)** | YOLO26n Transfer | Pakistani Test | 0.384 | 8.5 ms | 117.6 FPS |
| **Exp 4 (100% Data)**| YOLO26n Transfer | Pakistani Test | **0.442** | **8.5 ms** | **117.6 FPS** |

---

## 13. Cross-Domain Generalization Analysis
Leave-One-Country-Out experiments revealed consistent cross-border performance penalties. When evaluated on China Motorbike data with all other countries in training, performance reached $\text{mAP@0.5} = 0.355$. When tested on India data, performance dropped to $\text{mAP@0.5} = 0.312$.
The zero-shot evaluation on Pakistani pavement exhibited the most severe drop:
$$\text{Domain Gap} = \frac{0.455 - 0.224}{0.455} \times 100 = 50.77\%$$
This confirms that deep feature representations trained on foreign roads cannot be deployed zero-shot without severe reliability risks.

---

## 14. Transfer Learning Analysis
Fine-tuning the international YOLO checkpoint with incremental proportions of localized Pakistani road imagery produced strong monotonic recovery:
- At **10% data**, $\text{mAP@0.5}$ recovered to **0.258** (+15.2% over zero-shot).
- At **25% data**, $\text{mAP@0.5}$ reached **0.312** (+39.3% over zero-shot).
- At **50% data**, $\text{mAP@0.5}$ reached **0.384** (+71.4% over zero-shot).
- At **100% data**, $\text{mAP@0.5}$ reached **0.442** (+97.32% over zero-shot), almost completely closing the domain gap back to the international baseline level (0.455).

---

## 15. Error Analysis
Diagnostic error analysis on false positive and false negative predictions showed:
1. **False Positives (38%):** Induced predominantly by harsh solar shadow boundaries (tree limbs, electrical poles) mimicking longitudinal cracks (`D00`).
2. **Missed Defects (42%):** Faint hairline transverse cracks (`D10`) and dusty alligator networks (`D20`) obscured by low contrast with surrounding pavement.
3. **Bounding Box Misalignment (20%):** Large amorphous potholes (`D40`) with shallow edges where ground-truth annotation bounds diverged at $\text{IoU} \ge 0.5$.

---

## 16. Discussion
The empirical findings establish that single-stage anchor-free architectures (YOLO26n) dominate the accuracy-latency Pareto frontier for mobile infrastructure monitoring. Operating at **8.5 ms** (~117 FPS), YOLO26n delivers nearly $5\times$ higher throughput than Faster R-CNN (42.0 ms) while achieving **+7.0% higher baseline accuracy** (0.455 vs 0.385). Furthermore, the sample-efficiency curve demonstrates that developing transport authorities need not collect hundreds of thousands of local images; annotating a representative subset of a few hundred locally captured route sessions yields near-optimal performance recovery.

---

## 17. Limitations
1. **2D Visual Limitations:** Bounding-box detection cannot measure physical pothole depth or sub-base volumetric displacement.
2. **Adverse Weather:** The current dataset primarily captures clear and overcast daytime conditions; nocturnal driving with headlamp illumination remains a challenge.
3. **Regulatory Scope:** The system is an academic screening prototype and does not substitute for certified ASTM D6433 Pavement Condition Index (PCI) structural surveys.

---

## 18. Conclusion
RoadSight-PK demonstrates that deep learning models for road defect detection suffer a significant domain gap (~50.8%) when transferred internationally without adaptation. However, sample-efficient transfer learning with localized target data restores performance to 0.442 mAP@0.5 (+97.3% relative gain). The integrated FastAPI and React platform provides an end-to-end blueprint for cost-effective, real-time infrastructure maintenance in Pakistan and other developing regions.

---

## 19. Future Work
1. Incorporating monocular depth estimation to estimate pothole volume and severe structural cavitation.
2. Expanding the dataset to nocturnal routes and monsoon wet pavement conditions.
3. Quantizing models via TensorRT and CoreML for direct on-device dashcam execution.

---

## 20. References
1. Arya, D., Maeda, H., Ghosh, S. K., Toshniwal, D., Mraz, A., Kashiyama, T., & Sekimoto, Y. (2020). Transfer learning-based road damage detection for multiple countries. *Computer-Aided Civil and Infrastructure Engineering*, 35(4), 390-415.
2. Arya, D., et al. (2022). Crowdsensing-based Road Damage Detection Challenge (RDD2022). *Figshare Dataset*, DOI: 10.6084/m9.figshare.21431547.v1.
3. Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). You only look once: Unified, real-time object detection. *CVPR*, 779-788.
4. Ren, S., He, K., Girshick, R., & Sun, J. (2015). Faster R-CNN: Towards real-time object detection with region proposal networks. *NeurIPS*, 28.
5. Zhang, L., Yang, F., Zhang, Y. D., & Zhu, Y. J. (2016). Road crack detection using deep convolutional neural networks. *ICIP*, 3708-3712.
