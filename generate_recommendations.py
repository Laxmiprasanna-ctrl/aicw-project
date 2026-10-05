"""Run this once: python generate_recommendations.py"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))

def rec(treatment, fertilizer, natural, monitoring):
    return {"treatment": treatment, "fertilizer": fertilizer,
            "natural_options": natural, "monitoring": monitoring}

def stages(low_t, low_f, low_n, mod_t, mod_f, high_t, high_f, monitoring_low, monitoring_mod, monitoring_high):
    return {
        "Low": {
            s: rec(low_t, low_f, low_n, monitoring_low)
            for s in ["Seedling","Vegetative","Flowering","Fruiting"]
        },
        "Moderate": {
            s: rec(mod_t, mod_f, [], monitoring_mod)
            for s in ["Seedling","Vegetative","Flowering","Fruiting"]
        },
        "High": {
            s: rec(high_t, high_f, [], monitoring_high)
            for s in ["Seedling","Vegetative","Flowering","Fruiting"]
        },
        "Very High": {
            s: rec(
                ["Consult agricultural extension officer immediately",
                 "Remove and destroy all heavily infected plants",
                 "Plan crop rotation for next season"],
                ["No further fertilizer investment in severely infected crop"],
                [],
                ["Daily inspection", "Assess total crop loss"]
            )
            for s in ["Seedling","Vegetative","Flowering","Fruiting"]
        }
    }

HEALTHY = {
    s: rec(
        ["No disease treatment needed"],
        ["Apply balanced NPK as per crop growth stage","Use compost or vermicompost for soil health"],
        ["Neem cake soil application","Compost tea as soil drench"],
        ["Scout weekly for early signs of disease","Check undersides of leaves for pests"]
    )
    for s in ["Seedling","Vegetative","Flowering","Fruiting"]
}

data = {
  "Tomato": {
    "Healthy": HEALTHY,
    "Bacterial Spot": stages(
      ["Apply copper-based bactericide (copper hydroxide) spray","Remove infected leaves immediately"],
      ["Balanced NPK 10-10-10 at standard rate","Avoid high nitrogen fertilizers"],
      ["Neem oil spray (5 ml/L) every 7 days","Garlic extract spray"],
      ["Copper hydroxide + mancozeb tank mix every 5-7 days","Remove all infected plant material"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate to strengthen plants"],
      ["Copper + streptomycin bactericide every 4-5 days","Remove all infected plants","Disinfect tools with 1% bleach"],
      ["No nitrogen — apply potassium sulfate only","Soil-test-based correction"],
      ["Recheck after 5-7 days","Monitor spread to neighbouring plants"],
      ["Recheck every 3-5 days","Track percentage of infected leaves"],
      ["Daily inspection","Recheck every 2-3 days"]
    ),
    "Early Blight": stages(
      ["Apply mancozeb (2 g/L) spray every 7-10 days","Remove infected lower leaves"],
      ["Balanced NPK 19-19-19 at standard rate","Avoid excess nitrogen"],
      ["Neem oil (5 ml/L) spray","Neem leaf extract","Vermicompost side dressing"],
      ["Mancozeb + azoxystrobin spray every 5-7 days","Remove all infected leaves","Improve air circulation"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate to strengthen plants"],
      ["Tebuconazole (1 ml/L) spray every 4-5 days","Remove all infected leaves and stems","Improve air circulation urgently"],
      ["No nitrogen — apply potassium sulfate only","Potassium and calcium to support recovery"],
      ["Recheck after 5-7 days","Monitor lower leaves first"],
      ["Recheck every 3-5 days","Track upward spread of disease"],
      ["Daily inspection","Recheck every 2-3 days"]
    ),
    "Late Blight": stages(
      ["Apply metalaxyl + mancozeb (Ridomil Gold) immediately","Remove infected leaves","Avoid overhead irrigation"],
      ["Balanced NPK at standard rate","Avoid excess nitrogen"],
      ["Copper-based fungicide as organic option","Neem oil as supplementary spray"],
      ["Metalaxyl + mancozeb every 4-5 days urgently","Remove all infected plant material","Improve air circulation"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate to strengthen plants"],
      ["Emergency metalaxyl + cymoxanil spray every 3-4 days","Remove and destroy all infected plants","Consult agricultural extension officer immediately"],
      ["Soil-test-based NPK for surviving plants only","No nitrogen"],
      ["Recheck every 3-5 days — Late Blight spreads within 24-48 hours","Monitor weather forecast"],
      ["Recheck every 2-3 days","Monitor neighbouring plants for spread"],
      ["Daily inspection","Assess crop viability"]
    ),
    "Leaf Mold": stages(
      ["Apply chlorothalonil (2 g/L) spray every 7-10 days","Improve ventilation immediately","Remove infected leaves"],
      ["Balanced NPK 19-19-19 at standard rate","Avoid excess nitrogen"],
      ["Neem oil (5 ml/L) spray","Neem leaf extract","Vermicompost side dressing"],
      ["Chlorothalonil + azoxystrobin spray every 5-7 days","Remove all infected leaves","Prune for maximum air circulation"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate to strengthen plants"],
      ["Tebuconazole spray every 4-5 days","Remove all infected leaves and stems","Urgently improve air circulation"],
      ["No nitrogen — apply potassium sulfate only","Potassium and calcium to support recovery"],
      ["Recheck after 5-7 days","Monitor humidity — keep below 85%"],
      ["Recheck every 3-5 days","Monitor humidity levels daily"],
      ["Daily inspection","Recheck every 2-3 days"]
    ),
    "Septoria Leaf Spot": stages(
      ["Apply mancozeb (2 g/L) or chlorothalonil spray","Remove infected lower leaves"],
      ["Balanced NPK at standard rate","Avoid excess nitrogen"],
      ["Neem oil spray","Copper-based fungicide as organic option"],
      ["Mancozeb + copper fungicide tank mix every 5-7 days","Remove all infected leaves"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate"],
      ["Tebuconazole or azoxystrobin spray every 4-5 days","Remove all infected plant material"],
      ["No nitrogen — potassium sulfate only","Potassium and calcium"],
      ["Recheck after 5-7 days","Monitor lower leaves first"],
      ["Recheck every 3-5 days"],
      ["Daily inspection","Recheck every 2-3 days"]
    ),
    "Spider Mites": stages(
      ["Apply miticide (abamectin) or neem oil spray","Increase humidity around plants","Remove heavily infested leaves"],
      ["Balanced NPK at standard rate","Ensure adequate water — drought stress increases mite susceptibility"],
      ["Neem oil (5 ml/L) spray every 5-7 days","Insecticidal soap spray","Increase humidity"],
      ["Abamectin or spiromesifen miticide spray every 5-7 days","Remove heavily infested leaves"],
      ["Balanced NPK — ensure adequate potassium","Maintain soil moisture"],
      ["Intensive miticide program every 3-4 days","Remove all heavily infested plant material"],
      ["Balanced NPK — ensure adequate potassium and water"],
      ["Recheck after 5-7 days","Check undersides of leaves"],
      ["Recheck every 3-5 days","Monitor for resistance — rotate miticides"],
      ["Daily inspection","Recheck every 2-3 days"]
    ),
    "Target Spot": stages(
      ["Apply azoxystrobin or chlorothalonil spray","Remove infected leaves"],
      ["Balanced NPK at standard rate","Avoid excess nitrogen"],
      ["Neem oil spray","Copper-based fungicide"],
      ["Azoxystrobin + mancozeb tank mix every 5-7 days","Remove all infected leaves"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate"],
      ["Tebuconazole spray every 4-5 days","Remove all infected plant material"],
      ["No nitrogen — potassium sulfate only","Potassium and calcium"],
      ["Recheck after 5-7 days"],
      ["Recheck every 3-5 days"],
      ["Daily inspection","Recheck every 2-3 days"]
    ),
    "Mosaic Virus": stages(
      ["Remove and destroy infected plants immediately — no chemical cure","Control aphid vectors with insecticide","Disinfect tools"],
      ["Balanced NPK to support plant immunity","Avoid excess nitrogen"],
      ["Neem oil spray to control aphid vectors","Reflective mulch to deter aphids"],
      ["Remove all infected plants","Intensive aphid control program","Use virus-resistant varieties for replanting"],
      ["Balanced NPK — potassium to support stressed plants"],
      ["Remove all infected plants immediately","Consult extension officer","Plan replanting with resistant varieties"],
      ["Minimal supportive nutrition for surviving plants"],
      ["Recheck after 5-7 days","Monitor for aphid colonies"],
      ["Recheck every 3-5 days","Monitor aphid populations"],
      ["Daily inspection","Assess crop loss"]
    ),
    "Yellow Leaf Curl Virus": stages(
      ["Remove and destroy infected plants immediately","Control whitefly vectors with imidacloprid","Use yellow sticky traps"],
      ["Balanced NPK to support plant immunity","Avoid excess nitrogen"],
      ["Neem oil spray to control whitefly","Reflective mulch to deter whitefly","Yellow sticky traps"],
      ["Remove all infected plants","Intensive whitefly control program","Use virus-resistant varieties for replanting"],
      ["Balanced NPK — potassium to support stressed plants"],
      ["Remove all infected plants immediately","Consult extension officer","Plan replanting with resistant varieties"],
      ["Minimal supportive nutrition for surviving plants"],
      ["Recheck after 5-7 days","Monitor for whitefly colonies"],
      ["Recheck every 3-5 days","Monitor whitefly populations"],
      ["Daily inspection","Assess crop loss"]
    ),
  },
  "Potato": {
    "Healthy": HEALTHY,
    "Early Blight": stages(
      ["Apply mancozeb (2 g/L) spray every 7-10 days","Remove infected lower leaves","Avoid overhead irrigation"],
      ["Balanced NPK with high potassium","Avoid excess nitrogen"],
      ["Neem oil spray","Copper-based fungicide as organic option"],
      ["Mancozeb + azoxystrobin spray every 5-7 days","Remove all infected leaves","Improve air circulation"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate"],
      ["Tebuconazole spray every 4-5 days","Remove all infected plant material"],
      ["No nitrogen — potassium sulfate only","Potassium and calcium"],
      ["Recheck after 5-7 days","Monitor lower leaves first"],
      ["Recheck every 3-5 days"],
      ["Daily inspection","Recheck every 2-3 days"]
    ),
    "Late Blight": stages(
      ["Apply metalaxyl + mancozeb immediately — Late Blight is an emergency","Remove infected leaves","Avoid overhead irrigation"],
      ["Balanced NPK at standard rate","Avoid excess nitrogen"],
      ["Copper-based fungicide as organic option"],
      ["Metalaxyl + mancozeb every 4-5 days urgently","Remove all infected plant material"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate"],
      ["Emergency metalaxyl + cymoxanil spray every 3-4 days","Remove and destroy all infected plants","Consult agricultural extension officer"],
      ["Soil-test-based NPK for surviving plants only","No nitrogen"],
      ["Recheck every 3-5 days — Late Blight spreads rapidly","Monitor weather"],
      ["Recheck every 2-3 days","Monitor neighbouring plants"],
      ["Daily inspection","Assess crop viability"]
    ),
  },
  "Corn/Maize": {
    "Healthy": HEALTHY,
    "Gray Leaf Spot": stages(
      ["Apply strobilurin fungicide (azoxystrobin) at early signs","Remove infected lower leaves"],
      ["Balanced NPK with adequate nitrogen for corn","Split nitrogen application"],
      ["Neem oil spray as supplementary measure"],
      ["Azoxystrobin + propiconazole tank mix every 7-10 days","Remove infected leaves"],
      ["Balanced NPK — split nitrogen application","Potassium sulfate"],
      ["Intensive fungicide program every 5-7 days","Remove all infected plant material"],
      ["Soil-test-based NPK","No excess nitrogen"],
      ["Recheck after 7-10 days","Monitor lower leaves first"],
      ["Recheck every 5-7 days"],
      ["Daily inspection","Recheck every 3-5 days"]
    ),
    "Common Rust": stages(
      ["Apply propiconazole or tebuconazole fungicide at early signs","Monitor weather — rust spreads rapidly in cool humid conditions"],
      ["Balanced NPK with high potassium for rust resistance","Avoid excess nitrogen"],
      ["Neem oil spray as supplementary measure"],
      ["Propiconazole + mancozeb spray every 7 days","Remove heavily infected leaves"],
      ["Balanced NPK — high potassium","Avoid excess nitrogen"],
      ["Intensive fungicide program every 5-7 days","Remove all infected plant material"],
      ["Soil-test-based NPK","High potassium"],
      ["Recheck after 7 days","Monitor weather forecast"],
      ["Recheck every 5-7 days"],
      ["Daily inspection","Recheck every 3-5 days"]
    ),
    "Northern Leaf Blight": stages(
      ["Apply azoxystrobin or propiconazole fungicide","Remove infected lower leaves"],
      ["Balanced NPK with adequate nitrogen","Split nitrogen application"],
      ["Neem oil spray as supplementary measure"],
      ["Azoxystrobin + propiconazole tank mix every 7-10 days","Remove infected leaves"],
      ["Balanced NPK — split nitrogen","Potassium sulfate"],
      ["Intensive fungicide program every 5-7 days","Remove all infected plant material"],
      ["Soil-test-based NPK","No excess nitrogen"],
      ["Recheck after 7-10 days","Monitor lower leaves first"],
      ["Recheck every 5-7 days"],
      ["Daily inspection","Recheck every 3-5 days"]
    ),
  },
  "Apple": {
    "Healthy": HEALTHY,
    "Apple Scab": stages(
      ["Apply captan or myclobutanil fungicide at pre-bloom","Remove fallen infected leaves"],
      ["Balanced NPK for apple — high potassium","Avoid excess nitrogen"],
      ["Neem oil spray","Copper-based fungicide as organic option","Compost to improve soil health"],
      ["Myclobutanil + captan tank mix every 7-10 days","Remove all infected leaves and fruit"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate"],
      ["Intensive fungicide program every 5-7 days","Remove all infected plant material"],
      ["Soil-test-based NPK","No excess nitrogen"],
      ["Recheck after 7-10 days","Monitor after rain events"],
      ["Recheck every 5-7 days"],
      ["Daily inspection","Recheck every 3-5 days"]
    ),
    "Black Rot": stages(
      ["Prune infected wood immediately","Apply copper fungicide","Remove mummified fruit"],
      ["Balanced NPK for apple","Avoid excess nitrogen"],
      ["Neem oil spray","Copper-based fungicide"],
      ["Copper + captan spray every 7-10 days","Remove all infected wood and fruit"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate"],
      ["Intensive fungicide program every 5-7 days","Remove all infected plant material"],
      ["Soil-test-based NPK","No excess nitrogen"],
      ["Recheck after 7-10 days"],
      ["Recheck every 5-7 days"],
      ["Daily inspection","Recheck every 3-5 days"]
    ),
    "Cedar Apple Rust": stages(
      ["Apply myclobutanil fungicide at pre-bloom","Remove nearby cedar/juniper trees if possible"],
      ["Balanced NPK for apple","Avoid excess nitrogen"],
      ["Neem oil spray","Copper-based fungicide as organic option"],
      ["Myclobutanil spray every 7-10 days during wet weather","Remove infected leaves"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate"],
      ["Intensive fungicide program every 5-7 days","Remove all infected plant material"],
      ["Soil-test-based NPK","No excess nitrogen"],
      ["Recheck after 7-10 days","Monitor after rain events"],
      ["Recheck every 5-7 days"],
      ["Daily inspection","Recheck every 3-5 days"]
    ),
  },
  "Grape": {
    "Healthy": HEALTHY,
    "Black Rot": stages(
      ["Apply mancozeb or myclobutanil fungicide at pre-bloom","Remove mummified berries","Prune for air circulation"],
      ["Balanced NPK for grape — high potassium","Avoid excess nitrogen"],
      ["Neem oil spray","Copper-based fungicide as organic option"],
      ["Myclobutanil + mancozeb spray every 7-10 days","Remove all infected berries and leaves"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate"],
      ["Intensive fungicide program every 5-7 days","Remove all infected plant material"],
      ["Soil-test-based NPK","No excess nitrogen"],
      ["Recheck after 7-10 days","Monitor after rain events"],
      ["Recheck every 5-7 days"],
      ["Daily inspection","Recheck every 3-5 days"]
    ),
    "Esca / Black Measles": stages(
      ["Remove infected wood immediately","Apply wound sealant to pruning cuts","No effective chemical cure — management only"],
      ["Balanced NPK for grape","Avoid water stress — maintain consistent irrigation"],
      ["Compost to improve soil health","Trichoderma soil application"],
      ["Remove all infected wood","Apply wound sealant","Consult viticulture extension officer"],
      ["Balanced NPK — avoid water and nutrient stress","Potassium sulfate"],
      ["Remove all infected vines","Consult extension officer","Assess replanting"],
      ["Minimal supportive nutrition for surviving vines"],
      ["Recheck after 7-10 days","Monitor for new wood infections"],
      ["Recheck every 5-7 days"],
      ["Daily inspection","Assess crop viability"]
    ),
    "Leaf Blight": stages(
      ["Apply copper-based fungicide spray","Remove infected leaves","Improve air circulation"],
      ["Balanced NPK for grape","Avoid excess nitrogen"],
      ["Neem oil spray","Copper-based fungicide as organic option"],
      ["Copper + mancozeb spray every 7-10 days","Remove all infected leaves"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate"],
      ["Intensive fungicide program every 5-7 days","Remove all infected plant material"],
      ["Soil-test-based NPK","No excess nitrogen"],
      ["Recheck after 7-10 days"],
      ["Recheck every 5-7 days"],
      ["Daily inspection","Recheck every 3-5 days"]
    ),
  },
  "Chili": {
    "Healthy": HEALTHY,
    "Bacterial Spot": stages(
      ["Apply copper-based bactericide spray","Remove infected leaves immediately","Avoid overhead irrigation"],
      ["Balanced NPK 10-10-10 at standard rate","Avoid high nitrogen fertilizers"],
      ["Neem oil spray (5 ml/L) every 7 days","Garlic extract spray"],
      ["Copper hydroxide + mancozeb tank mix every 5-7 days","Remove all infected plant material"],
      ["Balanced NPK — avoid excess nitrogen","Potassium sulfate to strengthen plants"],
      ["Copper + streptomycin bactericide every 4-5 days","Remove all infected plants","Disinfect tools"],
      ["No nitrogen — apply potassium sulfate only","Soil-test-based correction"],
      ["Recheck after 5-7 days","Monitor spread to neighbouring plants"],
      ["Recheck every 3-5 days"],
      ["Daily inspection","Recheck every 2-3 days"]
    ),
  },
}

out = os.path.join(BASE, "data", "recommendations.json")
with open(out, "w") as f:
    json.dump(data, f, indent=2)
print(f"Saved: {out}")
print(f"Crops: {list(data.keys())}")
