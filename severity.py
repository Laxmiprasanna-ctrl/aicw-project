"""
severity.py — estimates visible diseased leaf area using OpenCV.

Usage:
    from severity import estimate_severity
    result = estimate_severity(pil_image)
"""
import numpy as np
from PIL import Image


def estimate_severity(pil_image: Image.Image) -> dict:
    """
    Uses HSV colour segmentation to estimate the proportion of the leaf
    that shows disease symptoms (brown/yellow/dark lesions).

    NOTE: This is a visual estimate only — not a clinical measurement.

    Returns:
        {
            "affected_area_pct": float,
            "severity": "Low" | "Moderate" | "High" | "Very High",
            "is_estimate": True,
        }
    """
    try:
        import cv2

        img_rgb = np.array(pil_image.convert("RGB").resize((224, 224)))
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        hsv     = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # ── Leaf mask (green pixels) ──────────────────────────────────────────
        lower_green = np.array([25,  30,  30])
        upper_green = np.array([90, 255, 255])
        leaf_mask   = cv2.inRange(hsv, lower_green, upper_green)

        # ── Diseased mask (brown / yellow / dark lesions) ─────────────────────
        lower_brown1 = np.array([0,  40,  20])
        upper_brown1 = np.array([20, 255, 200])
        lower_brown2 = np.array([160, 40, 20])
        upper_brown2 = np.array([180, 255, 200])
        lower_yellow = np.array([20, 40, 100])
        upper_yellow = np.array([35, 255, 255])

        disease_mask = (
            cv2.inRange(hsv, lower_brown1, upper_brown1) |
            cv2.inRange(hsv, lower_brown2, upper_brown2) |
            cv2.inRange(hsv, lower_yellow, upper_yellow)
        )

        # Only count diseased pixels that are on the leaf
        combined_mask = cv2.bitwise_and(disease_mask, disease_mask, mask=leaf_mask)

        leaf_pixels    = int(np.sum(leaf_mask > 0))
        disease_pixels = int(np.sum(combined_mask > 0))

        if leaf_pixels < 100:
            # Fallback: use whole image
            total = img_rgb.shape[0] * img_rgb.shape[1]
            pct   = (disease_pixels / total) * 100
        else:
            pct = (disease_pixels / leaf_pixels) * 100

        pct = min(pct, 100.0)

        if pct <= 10:
            severity = "Low"
        elif pct <= 30:
            severity = "Moderate"
        elif pct <= 60:
            severity = "High"
        else:
            severity = "Very High"

        return {
            "affected_area_pct": round(pct, 1),
            "severity":          severity,
            "is_estimate":       True,
        }

    except ImportError:
        # OpenCV not installed — return safe default
        return {
            "affected_area_pct": None,
            "severity":          "Unknown",
            "is_estimate":       True,
            "error":             "opencv-python not installed",
        }
    except Exception as e:
        return {
            "affected_area_pct": None,
            "severity":          "Unknown",
            "is_estimate":       True,
            "error":             str(e),
        }
