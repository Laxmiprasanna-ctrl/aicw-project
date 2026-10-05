"""Match local crop nutrient records without inventing soil or product data."""
import csv
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, "data", "fertilizer_database.csv")
CROP_INFO_PATH = os.path.join(BASE, "data", "crop_information.csv")


def _normalise(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _canonical_crop(value):
    key = _normalise(value)
    return {"cornmaize": "corn", "maize": "corn", "corn": "corn"}.get(key, key)


def _rows(path):
    try:
        with open(path, encoding="utf-8-sig", newline="") as source:
            return list(csv.DictReader(source))
    except OSError:
        return []


def _stage_match(timing, growth_stage):
    """Return True only when the stored timing explicitly names this stage."""
    timing_key = _normalise(timing)
    stage_key = _normalise(growth_stage)
    if not timing_key or not stage_key:
        return False
    aliases = {
        "seedling": ("seedling", "sowing", "sowing", "transplanting"),
        "vegetative": ("vegetative", "hilling", "topdress"),
        "flowering": ("flowering", "bloom", "prebloom"),
        "fruiting": ("fruiting", "fruit", "berry"),
        "maturity": ("maturity", "harvest", "ripening"),
    }
    return any(_normalise(alias) in timing_key for alias in aliases.get(growth_stage, (stage_key,)))


def get_fertilizer_recommendation(crop: str, disease: str = None, growth_stage: str = None,
                                  soil_n=None, soil_p=None, soil_k=None,
                                  soil_ph=None, soil_moisture=None) -> dict:
    """Use exact crop+disease CSV rows first, then crop reference rows.

    The bundled CSV contains crop/disease NPK records but no measured soil values
    and no explicit growth-stage column. Optional soil inputs are displayed as
    farmer-provided context and are never treated as verified deficiencies.
    """
    # Backwards compatibility for prior class-name calls.
    if disease is None and crop:
        if "___" in crop:
            crop, disease = crop.split("___", 1)
            crop = crop.replace("_", " ")
            disease = disease.replace("_", " ")
        else:
            parts = str(crop).split("_", 1)
            if len(parts) == 2:
                crop, disease = parts[0], parts[1].replace("_", " ")
    disease = disease or "Healthy"
    crop_key, disease_key = _canonical_crop(crop), _normalise(disease)
    rows = _rows(DB_PATH)
    crop_rows = [r for r in rows if _canonical_crop(r.get("crop")) == crop_key]
    exact = [r for r in crop_rows if _normalise(r.get("disease")) == disease_key]
    if not exact and disease_key:
        exact = [r for r in crop_rows if disease_key in _normalise(r.get("disease")) or _normalise(r.get("disease")) in disease_key]
    fallback_level = "exact crop and disease" if exact else "crop reference"
    selected = exact[:1]
    if not selected:
        selected = [r for r in crop_rows if _normalise(r.get("disease")) == "healthy"][:1]
    if not selected and crop_rows:
        selected = crop_rows[:1]
    if not selected:
        return {
            "found": False, "crop": crop, "disease": disease,
            "growth_stage": growth_stage, "fertilizer_name": None,
            "npk": None, "nutrients": None, "purpose": None,
            "matched_by": None, "stage_match": False,
            "soil_context": {},
            "message": "Insufficient fertilizer data for this supported crop. Consult a local soil-testing lab or extension service.",
        }

    row = selected[0]
    nutrients = {
        "N": row.get("nitrogen", ""),
        "P": row.get("phosphorus", ""),
        "K": row.get("potassium", ""),
    }
    crop_info = next((r for r in _rows(CROP_INFO_PATH)
                      if _canonical_crop(r.get("crop")) == crop_key), None)
    soil_context = {}
    if soil_ph not in (None, "") and crop_info:
        try:
            value = float(soil_ph)
            low, high = float(crop_info["ph_min"]), float(crop_info["ph_max"])
            soil_context["pH"] = {
                "value": value, "range": f"{low:g}?{high:g}",
                "status": "within crop reference range" if low <= value <= high else "outside crop reference range",
            }
        except (ValueError, KeyError, TypeError):
            pass
    if soil_moisture and crop_info:
        soil_context["moisture"] = {
            "value": str(soil_moisture),
            "crop_reference": crop_info.get("water_requirement", "not listed"),
        }
    entered_npk = {k: v for k, v in {"N": soil_n, "P": soil_p, "K": soil_k}.items()
                   if v not in (None, "")}
    if entered_npk:
        soil_context["soil_npk"] = entered_npk

    stage_match = _stage_match(row.get("timing", ""), growth_stage)
    return {
        "found": True,
        "crop": crop,
        "disease": disease,
        "growth_stage": growth_stage,
        "fertilizer_name": row.get("fertilizer_name"),
        "npk": f"{nutrients['N']}-{nutrients['P']}-{nutrients['K']}",
        "nutrients": nutrients,
        "purpose": row.get("notes", ""),
        "timing": row.get("timing", ""),
        "source": "data/fertilizer_database.csv",
        "matched_by": fallback_level,
        "stage_match": stage_match,
        "soil_context": soil_context,
        "soil_reference": crop_info,
        "message": None,
    }
