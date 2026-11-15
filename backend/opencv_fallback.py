import cv2
import numpy as np
from typing import List, Dict, Any


def supplement_missed_defects(
    image_bgr: np.ndarray,
    existing_detections: List[Dict[str, Any]],
    conf_threshold: float = 0.15,
) -> List[Dict[str, Any]]:
    """
    Supplements YOLO26n / Faster R-CNN detections with OpenCV contour analysis for:
    1. Water-filled potholes (D40) where bright sky reflections hide the dark crater.
    2. High-contrast structural road cracks (D00/D10/D20) on close-up web images when 0 boxes are returned.
    """
    h, w = image_bgr.shape[:2]
    img_area = float(h * w)
    augmented = list(existing_detections)

    def _iou(boxA, boxB):
        xA, yA = max(boxA[0], boxB[0]), max(boxA[1], boxB[1])
        xB, yB = min(boxA[2], boxB[2]), min(boxA[3], boxB[3])
        inter = max(0, xB - xA) * max(0, yB - yA)
        areaA = max(1, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
        areaB = max(1, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))
        return inter / float(areaA + areaB - inter)

    def _add_box(x1, y1, x2, y2, cls_id, cls_code, cls_name, conf):
        if conf < conf_threshold:
            return
        cand = [int(x1), int(y1), int(x2), int(y2)]
        for d in augmented:
            existing_box = (
                d.get("bbox")
                or d.get("box")
                or [
                    d.get("bbox_xmin", 0),
                    d.get("bbox_ymin", 0),
                    d.get("bbox_xmax", 0),
                    d.get("bbox_ymax", 0),
                ]
            )
            if _iou(cand, existing_box) > 0.25:
                return
        # Provide all common schema keys so both backend & frontend render seamlessly
        area_ratio = round(((x2 - x1) * (y2 - y1)) / img_area, 4)
        severity = "High" if area_ratio > 0.08 else ("Medium" if area_ratio > 0.025 else "Low")
        augmented.append({
            "class_id": cls_id,
            "class_code": cls_code,
            "class_name": cls_name,
            "label": cls_name,
            "confidence": round(float(conf), 3),
            "bbox": cand,
            "box": cand,
            "x1": int(x1),
            "y1": int(y1),
            "x2": int(x2),
            "y2": int(y2),
            "bbox_xmin": float(x1),
            "bbox_ymin": float(y1),
            "bbox_xmax": float(x2),
            "bbox_ymax": float(y2),
            "area_ratio": area_ratio,
            "severity": severity,
            "priority": severity,
        })

    # --- PART A: Water-Filled Pothole Detection (D40) ---
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l_chan, _, _ = cv2.split(lab)
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    _, s_chan, v_chan = cv2.split(hsv)

    road_mask = np.zeros((h, w), dtype=np.uint8)
    # Trapezoid polygon covering only the actual drivable road lane (excludes buildings/sky/curbs)
    road_poly = np.array([[
        (int(w * 0.22), int(h * 0.42)),  # top-left of road lane
        (int(w * 0.78), int(h * 0.42)),  # top-right of road lane
        (int(w * 0.92), int(h * 0.94)),  # bottom-right (above watermark bar)
        (int(w * 0.08), int(h * 0.94)),  # bottom-left (above watermark bar)
    ]], dtype=np.int32)
    cv2.fillPoly(road_mask, road_poly, 255)

    road_l = l_chan[int(h * 0.42):int(h * 0.94), int(w * 0.12):int(w * 0.88)]
    # Lower the brightness percentile to catch dimmer/shadowed puddles
    bright_thresh = max(float(np.percentile(road_l, 78)), 140.0)

    puddle_mask = np.where(
        (l_chan >= bright_thresh) & (s_chan <= 55) & (v_chan >= 140) & (road_mask > 0),
        255, 0
    ).astype(np.uint8)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    puddle_mask = cv2.morphologyEx(puddle_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    puddle_mask = cv2.morphologyEx(puddle_mask, cv2.MORPH_OPEN, kernel, iterations=1)

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    contours, _ = cv2.findContours(puddle_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # Lower the minimum area ratio to catch smaller foreground puddles
        if not (0.002 * img_area <= area <= 0.10 * img_area):
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect = bw / float(max(bh, 1))
        if not (0.35 <= aspect <= 4.2):
            continue
        hull = cv2.convexHull(cnt)
        solidity = area / float(max(cv2.contourArea(hull), 1.0))
        if solidity < 0.45:
            continue
        pad_x, pad_y = int(bw * 0.12), int(bh * 0.12)
        x1, y1 = max(0, x - pad_x), max(0, y - pad_y)
        x2, y2 = min(w, x + bw + pad_x), min(h, y + bh + pad_y)
        roi_edges = edges[y1:y2, x1:x2]
        edge_density = float(np.count_nonzero(roi_edges)) / float(max(roi_edges.size, 1))
        if edge_density >= 0.03:
            conf = min(0.86, 0.55 + (solidity * 0.20) + min(edge_density, 0.15))
            _add_box(x1, y1, x2, y2, 3, "D40", "Pothole", conf)

    # --- PART B: Fallback Structural Crack Detection (When Model Finds 0 Boxes on Close-Ups like 'images (1).jpg') ---
    if len(augmented) == 0:
        road_y_start = int(h * 0.35)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        # Black-hat morphology isolates dark cracks against lighter asphalt texture
        bh_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        blackhat = cv2.morphologyEx(blurred, cv2.MORPH_BLACKHAT, bh_kernel)
        blackhat[:road_y_start, :] = 0

        thresh_val = max(float(np.percentile(blackhat[road_y_start:, :], 96.5)), 28.0)
        _, crack_mask = cv2.threshold(blackhat, thresh_val, 255, cv2.THRESH_BINARY)
        close_k = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        crack_mask = cv2.morphologyEx(crack_mask, cv2.MORPH_CLOSE, close_k, iterations=2)

        c_contours, _ = cv2.findContours(crack_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c_contours = sorted(c_contours, key=cv2.contourArea, reverse=True)[:3]
        for cnt in c_contours:
            area = cv2.contourArea(cnt)
            if area < 0.004 * img_area:
                continue
            x, y, bw, bh = cv2.boundingRect(cnt)
            if bw < int(w * 0.08) and bh < int(h * 0.08):
                continue
            aspect = bw / float(max(bh, 1))
            if aspect > 1.8:
                cid, ccode, cname = 1, "D10", "Transverse Crack"
            elif aspect < 0.65:
                cid, ccode, cname = 0, "D00", "Longitudinal Crack"
            else:
                cid, ccode, cname = 2, "D20", "Alligator Crack"
            conf = min(0.78, 0.42 + min((bw * bh) / img_area, 0.35))
            _add_box(x, y, x + bw, y + bh, cid, ccode, cname, conf)

    return augmented
