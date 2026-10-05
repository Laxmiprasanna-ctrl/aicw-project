"""
recommendation_engine.py — returns treatment, fertilizer, and monitoring advice.

Usage:
    from recommendation_engine import get_recommendation, get_products
"""
import os, json, re

BASE = os.path.dirname(os.path.abspath(__file__))
REC_PATH  = os.path.join(BASE, "data", "recommendations.json")
PROD_PATH = os.path.join(BASE, "data", "fertilizer_products.json")

_recs  = None
_prods = None
_load_error = None

_RATE_OR_TIMING = re.compile(
    r"\b\d+(?:[.-]\d+)?\s*(?:g|ml|kg)\s*(?:/\s*(?:l|litre|liter)|per\s+(?:l|litre|liter))\b"
    r"|\bper\s+(?:litre|liter)\b|\b(?:pre[- ]harvest|dose|dosage)\b"
    r"|\b(?:every|after)\s+\d", re.IGNORECASE)
_MONITOR_RATE = re.compile(
    r"\b\d+(?:[.-]\d+)?\s*(?:g|ml|kg)\s*(?:/\s*(?:l|litre|liter)|per\s+(?:l|litre|liter))\b"
    r"|\bper\s+(?:litre|liter)\b|\b(?:pre[- ]harvest|dose|dosage)\b", re.IGNORECASE)
_LABEL_ONLY = "Use only locally approved products and follow the product label; FRAM IQ does not provide application rates."

GROWTH_STAGES = ["Seedling", "Vegetative", "Flowering", "Fruiting"]
SEVERITIES    = ["Low", "Moderate", "High", "Very High"]


def _load():
    global _recs, _prods, _load_error
    if _recs is None:
        try:
            with open(REC_PATH, encoding="utf-8") as f:
                _recs = json.load(f)
            with open(PROD_PATH, encoding="utf-8") as f:
                _prods = json.load(f)
            if not isinstance(_recs, dict) or not isinstance(_prods, list):
                raise ValueError("Recommendation data has an unexpected format")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            _load_error = str(exc)
            _recs, _prods = {}, []


def _safe_guidance(items, *, keep_monitoring_intervals=False):
    """Remove rate/timing instructions from legacy data before it reaches UI/history."""
    safe, label_notice_added = [], False
    for item in items or []:
        pattern = _MONITOR_RATE if keep_monitoring_intervals else _RATE_OR_TIMING
        if pattern.search(str(item)):
            if not label_notice_added:
                safe.append(_LABEL_ONLY)
                label_notice_added = True
        else:
            safe.append(str(item))
    return safe


def get_recommendation(crop: str, disease: str, severity: str, growth_stage: str) -> dict:
    """
    Returns:
        {
            "treatment":       [...],
            "fertilizer":      [...],
            "natural_options": [...],
            "monitoring":      [...],
            "found":           bool,
        }
    """
    _load()
    empty = {"treatment": [], "fertilizer": [], "natural_options": [], "monitoring": [], "found": False,
             "error": _load_error}

    crop_data = _recs.get(crop)
    if not crop_data:
        return empty

    disease_data = crop_data.get(disease)
    if not disease_data:
        return empty

    severity_data = disease_data.get(severity)
    if not severity_data:
        # When image severity is unavailable, use the midpoint plan as general
        # decision support, while the UI continues to report severity as unknown.
        preferred = "Moderate" if severity not in SEVERITIES else severity
        severity_data = disease_data.get(preferred)
        if not severity_data:
            severity_data = next((disease_data[s] for s in SEVERITIES if s in disease_data), None)

    # Healthy recommendations are stored directly by growth stage, while
    # disease plans are nested under severity. Support both existing shapes.
    matched_stage = growth_stage
    if severity_data is None and growth_stage in disease_data:
        stage_data = disease_data.get(growth_stage)
    elif isinstance(severity_data, dict):
        stage_data = severity_data.get(growth_stage)
    else:
        stage_data = None
    if not stage_data:
        # The bundled records predate the Maturity option; state the fallback.
        matched_stage = "Vegetative"
        if isinstance(severity_data, dict):
            stage_data = severity_data.get("Vegetative", {})
        else:
            stage_data = disease_data.get("Vegetative", {})

    if not isinstance(stage_data, dict):
        return empty

    treatment = _safe_guidance(stage_data.get("treatment", []))
    fertilizer = _safe_guidance(stage_data.get("fertilizer", []))
    natural = _safe_guidance(stage_data.get("natural_options", []))
    monitoring = _safe_guidance(stage_data.get("monitoring", []), keep_monitoring_intervals=True)
    return {
        "treatment":       treatment,
        "fertilizer":      fertilizer,
        "natural_options": natural,
        "monitoring":      monitoring,
        "found":           bool(treatment or fertilizer or natural or monitoring),
        "matched_growth_stage": matched_stage,
        "error":           None,
    }


def _normalise(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def get_products(crop: str, disease: str, growth_stage: str = None) -> list:
    """Return catalog-backed products matching crop, disease, and stage.

    Price and availability are reference values from the bundled catalog, not
    a live inventory feed. Products never supply dosage advice to the UI.
    """
    _load()
    results = []
    crop_aliases = {
        "cornmaize": {"cornmaize", "corn", "maize"},
        "paddyrice": {"paddyrice", "rice"},
    }
    requested_crop = _normalise(crop)
    accepted_crops = crop_aliases.get(requested_crop, {requested_crop})
    requested_disease = _normalise(disease)
    for p in _prods:
        if _normalise(p.get("crop", "")) not in accepted_crops:
            continue
        stages = p.get("suitable_growth_stage", [])
        if growth_stage and stages and growth_stage not in stages:
            continue
        suitable = p.get("suitable_disease", [])
        if any(_normalise(s).startswith("all") or
               (requested_disease and
                (requested_disease in _normalise(s) or _normalise(s) in requested_disease))
               for s in suitable):
            result = dict(p)
            result["usage_note"] = _LABEL_ONLY
            results.append(result)
    return results


def get_fertilizer_products(crop: str, growth_stage: str = None) -> list:
    """Return only catalog entries that are fertilizer or compost products.

    Crop-protection products such as fungicides and biopesticides are excluded
    so disease treatment is not presented as plant nutrition.
    """
    _load()
    crop_aliases = {
        "cornmaize": {"cornmaize", "corn", "maize"},
        "paddyrice": {"paddyrice", "rice"},
    }
    requested_crop = _normalise(crop)
    accepted_crops = crop_aliases.get(requested_crop, {requested_crop})
    results = []
    for product in _prods:
        if _normalise(product.get("crop", "")) not in accepted_crops:
            continue
        product_type = _normalise(product.get("fertilizer_type", ""))
        if "fertilizer" not in product_type and "compost" not in product_type:
            continue
        stages = product.get("suitable_growth_stage", [])
        if growth_stage and stages and growth_stage not in stages:
            continue
        result = dict(product)
        result["usage_note"] = _LABEL_ONLY
        result["reference_price"] = result.pop("approximate_price", None)
        results.append(result)
    return results
