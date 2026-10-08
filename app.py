import os, warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

import streamlit as st
from PIL import Image
import json
from pathlib import Path
from database import init_db, get_predictions, save_prediction
from localization import TELUGU, install_localization, translate

# A running Streamlit process can hold an older localization module while files
# are being saved. Keep startup compatible with that earlier module version.
try:
    from localization import initialize_language, persist_language
except ImportError:
    def initialize_language(streamlit_module):
        if "header_language" not in streamlit_module.session_state:
            streamlit_module.session_state.header_language = "English"

    def persist_language(streamlit_module):
        return None

install_localization(st)

st.set_page_config(
    page_title="FARMIQ",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)
initialize_language(st)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans Telugu', 'Nirmala UI', sans-serif; }
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse at 10% 4%, rgba(220, 252, 231, .85), transparent 34%),
        radial-gradient(ellipse at 94% 90%, rgba(226, 232, 226, .62), transparent 32%),
        linear-gradient(145deg, #f5f8f4 0%, #eef4ed 56%, #f8faf7 100%);
}
[data-testid="stAppViewContainer"]:has(.login-showcase) {
    background:
        radial-gradient(ellipse at 12% 12%, rgba(187, 247, 208, .52), transparent 34%),
        radial-gradient(ellipse at 88% 88%, rgba(163, 230, 183, .24), transparent 30%),
        linear-gradient(135deg, #f5f8f4 0%, #eaf5ec 48%, #f8faf7 100%);
}
[data-testid="stMain"] { background: transparent; }
[data-testid="stHeader"] { background: rgba(245, 248, 244, .9); }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a3a1a 0%, #2d5a27 60%, #1a3a1a 100%);
}
[data-testid="stSidebar"] * { color: #e8f5e9 !important; }
[data-testid="stSidebar"] [data-testid="stButton"] > button {
    width: 100%; min-height: 2.7rem; color: #fff !important;
    background: linear-gradient(100deg, #166534, #22c55e) !important;
    border: 1px solid rgba(255,255,255,.3) !important; border-radius: 12px;
    font-weight: 700; box-shadow: 0 5px 14px rgba(0,0,0,.2);
}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
    color: #fff !important; background: linear-gradient(100deg, #14532d, #166534) !important;
    border-color: rgba(255,255,255,.55) !important;
}

.hero {
    background: radial-gradient(circle at 88% 18%, rgba(255,255,255,.23), transparent 22%),
                linear-gradient(120deg, #14532d 0%, #166534 52%, #22c55e 100%);
    border-radius: 24px; padding: 2.4rem 2.6rem; margin-bottom: 1.5rem;
    color: white; text-align: left; position: relative; overflow: hidden;
    box-shadow: 0 16px 36px rgba(20, 83, 45, .18);
}
.hero::after { content: ""; position: absolute; width: 230px; height: 230px; right: -45px; bottom: -125px;
    border: 1px solid rgba(255,255,255,.24); border-radius: 48% 52% 65% 35%; transform: rotate(-28deg);
    box-shadow: 0 0 0 24px rgba(255,255,255,.05), 0 0 0 50px rgba(255,255,255,.04); }
.hero h1 { font-size: clamp(2rem, 4vw, 3rem); font-weight: 750; margin: 0 0 0.55rem; letter-spacing: -.04em; position: relative; z-index: 1; }
.hero p  { font-size: 1.05rem; opacity: .92; margin: 0; max-width: 720px; position: relative; z-index: 1; }

.login-showcase { min-height: 460px; padding: 3rem; border-radius: 28px; color: #fff;
    background: radial-gradient(circle at 82% 16%, rgba(255,255,255,.25), transparent 24%),
                linear-gradient(145deg, #14532d, #166534 62%, #22c55e);
    box-shadow: 0 22px 55px rgba(20,83,45,.2); position: relative; overflow: hidden; }
.login-showcase::after { content: ""; position: absolute; width: 290px; height: 290px; right: -72px; bottom: -145px;
    border: 1px solid rgba(255,255,255,.28); border-radius: 50% 12% 50% 12%; transform: rotate(-35deg);
    box-shadow: 0 0 0 26px rgba(255,255,255,.06), 0 0 0 55px rgba(255,255,255,.04); }
.brand-mark { display: inline-grid; place-items: center; width: 54px; height: 54px; border-radius: 18px;
    background: linear-gradient(135deg, #dcfce7, #86efac); color: #14532d; font-weight: 800; font-size: 1.2rem; }
.login-eyebrow { margin: 2.2rem 0 .6rem; color: #dcfce7; font-size: .75rem; font-weight: 800; letter-spacing: .16em; }
.login-showcase h1 { max-width: 500px; font-size: clamp(2.2rem, 4vw, 3.6rem); line-height: 1.05; letter-spacing: -.045em; margin: 0 0 1rem; }
.login-showcase p { color: rgba(255,255,255,.86); max-width: 460px; line-height: 1.7; }
.login-pills { display: flex; flex-wrap: wrap; gap: .55rem; margin-top: 1.8rem; }
.login-pills span { border: 1px solid rgba(255,255,255,.32); border-radius: 999px; padding: .45rem .75rem; font-size: .78rem; background: rgba(255,255,255,.1); }
.login-form-title { color: #166534; font-size: 1.7rem; font-weight: 750; letter-spacing: -.03em; margin: .6rem 0 .2rem; }
.login-form-subtitle { color: #52635a; margin-bottom: 1.2rem; }

[data-testid="stMetric"] { background: #fff; border: 1px solid #e0e8df;
    border-top: 4px solid #38a45a; border-radius: 18px; padding: 1rem 1.1rem;
    box-shadow: 0 7px 18px rgba(33, 70, 42, .07); min-height: 106px; }
[data-testid="stMetricLabel"] { color: #58705d; font-weight: 650; }
[data-testid="stMetricValue"] { color: #164b2c; font-weight: 780; }
[data-testid="stVerticalBlockBorderWrapper"] { background: rgba(255,255,255,.96); border: 1px solid #e0e8df;
    border-radius: 22px; padding: .8rem; box-shadow: 0 12px 30px rgba(38,76,48,.07); }
[data-testid="stTextInput"] input, [data-testid="stPasswordInput"] input,
[data-testid="stNumberInput"] input, [data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input { border-radius: 12px; background: #fff; }
[data-baseweb="select"] > div { background: #fff; }
[data-testid="stFileUploader"] section { background: #f8fbf7; border-color: #cbd8ca; }
button[kind="primary"] { border-radius: 12px; background: #166534; border: 0; }
button[kind="primary"]:hover { background: #14532d; border: 0; }
.top-brand { display:flex; align-items:center; gap:.65rem; padding:.45rem .7rem; color:#172018; }
.top-brand-mark { display:grid; place-items:center; width:2.5rem; height:2.5rem; border-radius:.8rem; background:#dcfce7; color:#166534; font-size:1.3rem; }
.top-brand strong { display:block; color:#166534; font-size:1.12rem; letter-spacing:-.03em; }
.top-brand small { display:block; color:#617065; font-size:.72rem; }
[data-testid="stPills"] [role="radiogroup"] { flex-wrap:wrap; gap:.3rem; }
[data-testid="stPills"] button { border-radius:999px; }
[data-testid="stPills"] button[aria-pressed="true"] { background:#dcfce7 !important; color:#166534 !important; border:1px solid #86efac !important; }

.section-header {
    background: linear-gradient(100deg, #e8f5e9, #f5f8f4); border-left: 5px solid #166534;
    border-radius: 0 8px 8px 0; padding: 0.6rem 1rem; margin: 1.2rem 0 0.8rem;
    font-weight: 600; color: #1b5e20; font-size: 1rem;
}

.result-box {
    border-radius: 14px; padding: 1.4rem; margin: 0.8rem 0;
    color: white; text-align: center;
}
.result-box.healthy  { background: linear-gradient(135deg, #2e7d32, #43a047); }
.result-box.diseased { background: linear-gradient(135deg, #b71c1c, #e53935); }
.result-box.low-conf { background: linear-gradient(135deg, #e65100, #ff6d00); }
.result-box h2 { margin: 0 0 0.3rem; font-size: 1.5rem; }
.result-box p  { margin: 0.2rem 0; opacity: 0.92; font-size: 0.95rem; }

.info-card { border-radius: 10px; padding: 0.9rem 1.1rem; margin-bottom: 0.7rem; }
.info-card.blue   { background: #e3f2fd; border-left: 4px solid #1976d2; }
.info-card.orange { background: #fff3e0; border-left: 4px solid #f57c00; }
.info-card.green  { background: #e8f5e9; border-left: 4px solid #2e7d32; }
.info-card.red    { background: #ffebee; border-left: 4px solid #c62828; }
.info-card.purple { background: #e8f5e9; border-left: 4px solid #166534; }
.info-card.teal   { background: #e0f2f1; border-left: 4px solid #00695c; }
.info-card h4 { margin: 0 0 0.4rem; font-size: 0.88rem; font-weight: 600; }
.info-card ul { margin: 0; padding-left: 1.2rem; font-size: 0.86rem; color: #333; }
.info-card li { margin-bottom: 0.2rem; }

.conf-bar-bg   { background: #e0e0e0; border-radius: 8px; height: 12px; margin: 0.4rem 0; }
.conf-bar-fill { height: 12px; border-radius: 8px;
                 background: linear-gradient(90deg, #2e7d32, #66bb6a); }

.severity-badge {
    display: inline-block; border-radius: 20px; padding: 0.3rem 1rem;
    font-weight: 600; font-size: 0.9rem; margin: 0.3rem 0;
}
.sev-low      { background: #e8f5e9; color: #1b5e20; }
.sev-moderate { background: #fff8e1; color: #f57f17; }
.sev-high     { background: #fff3e0; color: #e65100; }
.sev-veryhigh { background: #ffebee; color: #b71c1c; }

.product-card {
    background: #fff; border-radius: 10px; padding: 1rem 1.2rem;
    margin-bottom: 0.8rem; box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    border-top: 3px solid #2e7d32;
}
.product-card h4 { margin: 0 0 0.4rem; color: #1b5e20; font-size: 0.95rem; }
.product-card p  { margin: 0.2rem 0; font-size: 0.84rem; color: #444; }

.warn-box {
    background: #fff8e1; border: 1px solid #f9a825;
    border-radius: 10px; padding: 0.9rem 1.1rem; margin-bottom: 1rem;
    font-size: 0.9rem; color: #5d4037;
}
.login-card {
    display: none;
}
.login-card h2 { color: #1b5e20; margin-bottom: 0.3rem; }
.login-card p  { color: #666; margin-bottom: 1.5rem; font-size: 0.9rem; }
@media (max-width: 760px) {
    .login-showcase { min-height: 0; padding: 2rem; }
    .login-showcase h1 { font-size: 2.2rem; }
    .hero { padding: 1.8rem; }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .75rem; }
    [data-testid="stColumn"] { min-width: min(100%, 245px); flex: 1 1 245px; }
    [data-testid="stPills"] [role="radiogroup"] { justify-content: flex-start; }
}

/* FRAM IQ premium dark agriculture design system */
:root {
    color-scheme: dark;
    --bg: #0B1410; --sidebar: #0F1F17; --card: #14261C; --hover: #1B3526;
    --green: #22C55E; --bright: #4ADE80; --light: #86EFAC; --text: #F0FDF4;
    --muted: #A7B8AC; --border: #234332; --warning: #F59E0B; --danger: #EF4444;
}
html, body, [class*="css"], [data-testid="stAppViewContainer"] { color: var(--text); }
[data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
    background: #0B1410 !important; color: var(--text) !important;
}
[data-testid="stHeader"] { background: rgba(11,20,16,.94) !important; }
[data-testid="stSidebar"] { background: #0F1F17 !important; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {
    display:flex; flex-direction:column; min-height:calc(100dvh - 2rem);
}
[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"]:has(.st-key-sidebar-bottom-section) {
    display:flex; flex-direction:column; min-height:calc(100dvh - 2rem);
}
.st-key-sidebar-bottom-section { order:999; margin-top:auto; position:sticky; bottom:0; z-index:5;
    padding-top:1rem; background:#0F1F17; border-top:1px solid #234332; }
.st-key-sidebar-bottom-section [data-testid="stButton"] button {
    background:transparent !important; border:1px solid transparent !important;
    box-shadow:none !important; color:#A7B8AC !important; justify-content:flex-start;
}
.st-key-sidebar-bottom-section [data-testid="stButton"] button:hover {
    color:#FCA5A5 !important; background:#2b1717 !important; border-color:#7f3333 !important;
}
[data-testid="stSidebar"] [role="radiogroup"] { gap:.22rem; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding:.48rem .62rem; border:1px solid transparent; border-radius:10px;
    color:#A7B8AC !important; transition:background .15s ease, border-color .15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background:#14261C; border-color:#234332; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background:#14261C; border-color:#326347; box-shadow:inset 3px 0 #22C55E;
}
[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stExpander"],
[data-testid="stForm"], [data-testid="stDialog"] > div {
    background: #14261C !important; border: 1px solid var(--border) !important;
    border-radius: 18px !important; box-shadow: 0 12px 28px rgba(0,0,0,.22);
}
[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: #326347 !important; }
[data-testid="stMetric"] {
    background: #14261C !important; border: 1px solid var(--border) !important;
    border-top: 2px solid var(--green) !important; border-radius: 18px !important;
    box-shadow: 0 10px 26px rgba(0,0,0,.22), 0 0 18px rgba(34,197,94,.05) !important;
    transition: transform .18s ease, background .18s ease, border-color .18s ease;
}
[data-testid="stMetric"]:hover { background: #1B3526 !important; transform: translateY(-2px); border-color: #39704e !important; }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { color: #A7B8AC !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * { color: #4ADE80 !important; }
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] label,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] strong { color: var(--text); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: var(--muted) !important; }
[data-testid="stTextInput"] input, [data-testid="stPasswordInput"] input,
[data-testid="stNumberInput"] input, [data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input, [data-baseweb="select"] > div,
[data-testid="stFileUploader"] section, textarea {
    background: #0F1F17 !important; color: var(--text) !important;
    border-color: var(--border) !important; border-radius: 12px !important;
}
[data-baseweb="select"] *, [data-testid="stFileUploader"] *,
[data-testid="stCheckbox"] *, [data-testid="stRadio"] * { color: var(--text) !important; }
[data-baseweb="popover"], [role="listbox"] { background: #14261C !important; border-color: var(--border) !important; }
[role="option"] { color: var(--text) !important; }
button[kind="primary"], [data-testid="stButton"] button[kind="primaryFormSubmit"] {
    background: #22C55E !important; color: #07120B !important; border: 1px solid #4ADE80 !important;
    border-radius: 12px !important; font-weight: 750 !important; box-shadow: 0 0 18px rgba(34,197,94,.15);
}
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button {
    background: #14261C; color: var(--text); border: 1px solid var(--border); border-radius: 12px;
    transition: background .18s ease, transform .18s ease, border-color .18s ease;
}
[data-testid="stButton"] button:hover, [data-testid="stDownloadButton"] button:hover {
    background: #1B3526; color: var(--light); border-color: var(--green); transform: translateY(-1px);
}
[data-testid="stPills"] [role="radiogroup"] { flex-wrap: wrap; gap: .35rem; padding: .5rem;
    border: 1px solid var(--border); border-radius: 16px; background: #0F1F17; }
[data-testid="stPills"] button { background: transparent !important; color: var(--muted) !important; border-radius: 999px !important; }
[data-testid="stPills"] button[aria-pressed="true"] { background: #22C55E !important; color: #07120B !important; border-color: #4ADE80 !important; }
.top-brand { background: #14261C; border: 1px solid var(--border); border-radius: 16px; }
.top-brand-mark { background: #1B3526; color: var(--bright); border: 1px solid #326347; }
.top-brand strong { color: var(--bright); } .top-brand small { color: var(--muted); }
.workflow-steps { display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:.55rem; margin:.9rem 0 1.25rem; }
.workflow-step { min-width:0; display:flex; align-items:center; gap:.55rem; padding:.72rem .8rem; border:1px solid var(--border); border-radius:14px; background:#0F1F17; color:var(--muted); }
.workflow-icon { font-size:1.15rem; }
.workflow-label { font-size:.78rem; font-weight:650; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.workflow-step.active { background:#22C55E; border-color:#4ADE80; color:#07120B; box-shadow:0 0 18px rgba(34,197,94,.18); }
.workflow-step.active .workflow-label { color:#07120B; }
.workflow-step.complete { border-color:#326347; color:#86EFAC; background:#14261C; }
.empty-state { display:flex; flex-direction:column; align-items:center; text-align:center; padding:2rem 1rem; border:1px dashed #326347; border-radius:18px; background:#14261C; }
.empty-state span { font-size:2rem; margin-bottom:.45rem; }
.empty-state strong { color:#F0FDF4; font-size:1.05rem; }
.empty-state p { color:#A7B8AC; max-width:600px; margin:.4rem 0 0; }
/* Supporting actions stay outlined; only explicit primary actions are filled. */
[data-testid="stButton"] button:not([kind="primary"]), [data-testid="stDownloadButton"] button { background:transparent; border-color:#326347; color:#A7B8AC; box-shadow:none; }
[data-testid="stButton"] button:not([kind="primary"]):hover, [data-testid="stDownloadButton"] button:hover { background:#14261C; color:#86EFAC; border-color:#4ADE80; }
[data-testid="stPills"] button[aria-pressed="true"] { box-shadow:inset 0 -3px 0 #86EFAC, 0 0 14px rgba(34,197,94,.12); }
/* Streamlit's primary button test id is stable across releases; keep it above
   the secondary-button selectors so primary actions cannot inherit outlines. */
[data-testid="stButton"] [data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primary"] {
    background:#22C55E !important; color:#FFFFFF !important; border:1px solid #4ADE80 !important;
    border-radius:13px !important; font-weight:800 !important;
    box-shadow:0 7px 20px rgba(34,197,94,.2) !important;
}
[data-testid="stButton"] [data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
    background:#16A34A !important; color:#FFFFFF !important; border-color:#86EFAC !important;
    box-shadow:0 9px 24px rgba(34,197,94,.28) !important; transform:translateY(-1px);
}
.hero, .login-showcase { background: #14261C !important; color: var(--text) !important;
    border: 1px solid var(--border); box-shadow: 0 16px 38px rgba(0,0,0,.28), 0 0 22px rgba(34,197,94,.06); }
.hero h1, .login-showcase h1 { color: var(--text) !important; }
.hero p, .login-showcase p { color: var(--muted) !important; }
.brand-mark { color: #07120B; background: #4ADE80; }
.login-form-title, .login-card h2 { color: var(--bright) !important; }
.login-form-subtitle, .login-card p { color: var(--muted) !important; }
.section-header { background: #14261C; border-left-color: #22C55E; color: var(--light); border-radius: 0 12px 12px 0; }
.result-box { border: 1px solid var(--border); box-shadow: 0 10px 26px rgba(0,0,0,.24); }
.result-box.healthy { background: #14261C; border-color: #22C55E; }
.result-box.diseased { background: #2b1717; border-color: #EF4444; }
.result-box.low-conf { background: #2b2415; border-color: #F59E0B; }
.info-card, .product-card, .warn-box { background: #14261C !important; color: var(--text) !important; border: 1px solid var(--border); border-left: 3px solid var(--green); border-radius: 14px; box-shadow: 0 8px 20px rgba(0,0,0,.18); }
.info-card.blue, .info-card.orange, .info-card.green, .info-card.red, .info-card.purple, .info-card.teal { background: #14261C; }
.info-card h4, .info-card ul, .product-card h4, .product-card p, .warn-box { color: var(--text) !important; }
.conf-bar-bg { background: #234332; } .conf-bar-fill { background: #22C55E; }
.sev-low { background: #163522; color: #86EFAC; } .sev-moderate { background: #382b14; color: #F59E0B; }
.sev-high, .sev-veryhigh { background: #3b1919; color: #EF4444; }
[data-testid="stDataFrame"], [data-testid="stTable"] { border: 1px solid var(--border); border-radius: 14px; overflow: hidden; }
[data-testid="stDataFrame"] * { color: var(--text); }
[data-testid="stAlert"] { background: #14261C; border-color: var(--border); color: var(--text); }
[data-testid="stProgress"] > div > div { background: #22C55E; }
hr { border-color: var(--border) !important; }
svg text { fill: #F0FDF4 !important; }
/* Streamlit's native chart, dataframe, and widget surfaces also use theme tokens. */
[data-testid="stDataFrame"], [data-testid="stTable"], [data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"], [data-testid="stPlotlyChart"],
[data-testid="stDeckGlJsonChart"], [data-testid="stPyplotGlobalUse"] {
    background: #14261C !important; color: #F0FDF4 !important;
    border-color: #234332 !important; color-scheme: dark;
}
[data-testid="stDataFrame"] iframe, [data-testid="stPlotlyChart"] iframe,
[data-testid="stVegaLiteChart"] iframe { background: #14261C !important; }
[data-testid="stTable"] table, [data-testid="stDataFrame"] table { background: #14261C !important; color: #F0FDF4 !important; }
[data-testid="stDataFrame"] th, [data-testid="stDataFrame"] td { background: #14261C !important; color: #F0FDF4 !important; border-color: #234332 !important; }
[data-testid="stToolbar"] { background: #14261C !important; color: #F0FDF4 !important; }
input::placeholder, textarea::placeholder { color: #A7B8AC !important; opacity: 1; }
@media (max-width: 760px) {
    [data-testid="stMainBlockContainer"] { padding-left: 1rem; padding-right: 1rem; }
    [data-testid="stPills"] [role="radiogroup"] { max-height: 9rem; overflow-y: auto; }
    [data-testid="stDataFrame"] { overflow-x: auto; }
    .workflow-steps { grid-template-columns:repeat(2,minmax(0,1fr)); }
    .workflow-step { padding:.6rem; }
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

PAGE_OPTIONS = [
    "🏠 Dashboard", "🔬 Crop Scanner", "🧪 Disease Results", "📋 Plant Records",
    "💊 Treatment & Cure", "🌱 Fertilizer Advisory", "🌦 Weather & Risk",
    "🤖 AI Agronomist", "📅 Seasonal Advisory", "📚 Disease Knowledge",
    "❓ FAQ", "ℹ️ About Project", "📊 Model Performance", "🛒 Market Prices", "⚙️ Settings",
]
PAGE_LABELS = {
    "🏠 Dashboard": "Dashboard", "🔬 Crop Scanner": "New Scan",
    "🧪 Disease Results": "Disease Results", "📋 Plant Records": "Scan History",
    "💊 Treatment & Cure": "Treatment & Cure", "🌱 Fertilizer Advisory": "Fertilizer & Nutrient",
    "🌦 Weather & Risk": "Weather", "🤖 AI Agronomist": "Agronomy",
    "📅 Seasonal Advisory": "Seasonal Advisory", "📚 Disease Knowledge": "Disease Knowledge",
    "❓ FAQ": "FAQ", "ℹ️ About Project": "About", "📊 Model Performance": "AI Benchmark",
    "🛒 Market Prices": "Products", "⚙️ Settings": "Settings",
}


NAV_OPTIONS = PAGE_OPTIONS

def set_active_page(target):
    """Shared callback for dashboard shortcuts and the top navigation."""
    st.session_state["app_navigation"] = target
    st.session_state["sidebar_navigation"] = target


def sync_sidebar_navigation():
    st.session_state["app_navigation"] = st.session_state["sidebar_navigation"]


def sync_header_navigation():
    st.session_state["sidebar_navigation"] = st.session_state["app_navigation"]


def sync_settings_language():
    st.session_state["header_language"] = st.session_state["language_settings"]


def render_top_navigation():
    """Render the brand, hamburger navigation menu, and language selector."""
    if "app_navigation" not in st.session_state:
        st.session_state.app_navigation = PAGE_OPTIONS[0]
    brand_col, language_col, menu_col = st.columns([5, 1.25, 0.55], vertical_alignment="center")
    with brand_col:
        st.markdown(
            '<div class="top-brand"><span class="top-brand-mark">&#127807;</span>'
            '<span><strong>CropCare AI</strong>'
            '<small>PROFESSIONAL AGRICULTURAL INTELLIGENCE</small></span></div>',
            unsafe_allow_html=True,
        )
    with language_col:
        st.selectbox(
            "Language",
            ["English", "\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41", "\u0939\u093f\u0928\u094d\u0926\u0940"],
            label_visibility="collapsed",
            key="header_language",
        )
    with menu_col:
        with st.popover("\u2630", help="Open navigation"):
            st.radio(
                "Application navigation",
                NAV_OPTIONS,
                format_func=format_page_label,
                key="app_navigation",
                label_visibility="visible",
                on_change=sync_header_navigation,
            )
    persist_language(st)
    st.divider()
    return st.session_state.app_navigation


def format_page_label(value):
    label = PAGE_LABELS.get(value, value)
    if st.session_state.get("header_language") == TELUGU:
        return translate(label)
    return label

def render_empty_state(title, message):
    st.markdown(
        f'<div class="empty-state"><span>🌱</span><strong>{title}</strong><p>{message}</p></div>',
        unsafe_allow_html=True,
    )


def render_scan_workflow(active_step):
    """Show progress through scan, diagnosis, care, nutrients, and availability."""
    steps = [
        ("🍃", "Leaf Scan"), ("🔍", "Disease Detection"), ("📊", "Severity"),
        ("🌿", "Treatment"), ("🧪", "Fertilizer"), ("📍", "Availability"),
    ]
    pieces = []
    for index, (icon, label) in enumerate(steps):
        state = "complete" if index < active_step else ("active" if index == active_step else "upcoming")
        pieces.append(
            f'<div class="workflow-step {state}"><span class="workflow-icon">{icon}</span>'
            f'<span class="workflow-label">{label}</span></div>'
        )
    st.markdown('<div class="workflow-steps">' + "".join(pieces) + '</div>', unsafe_allow_html=True)


def render_kpis(items):
    """Render a responsive row of white metric cards."""
    columns = st.columns(len(items))
    for column, item in zip(columns, items):
        label, value, *delta = item
        column.metric(label, value, delta[0] if delta else None)


def render_disease_result_summary(record, include_status=True):
    """Shared summary card for the latest scan and its stored result page."""
    st.subheader(f"{record['crop']} | {record['disease']}")
    items = [
        ("Model confidence", f"{float(record['confidence']):.1%}"),
        ("Visual severity", record.get("severity", "Unknown")),
        ("Growth stage", record.get("growth_stage", "Not recorded")),
        ("Recorded", str(record.get("date", "Not recorded"))[:19].replace("T", " ")),
    ]
    if include_status:
        status = "Healthy" if str(record.get("disease", "")).lower() == "healthy" else "Review recommended"
        items.append(("Status", status))
    render_kpis(items)


def render_fertilizer_card(recommendation, stage_guidance=None, products=None):
    """Render nutrient guidance separately from disease treatment."""
    st.markdown("#### Fertilizer & Nutrient Recommendation")
    if recommendation.get("found"):
        st.markdown(f"**Recommended fertilizer:** {recommendation.get('fertilizer_name') or 'See stage guidance below'}")
        nutrients = recommendation.get("nutrients") or {}
        n, p, k = st.columns(3)
        n.metric("N", str(nutrients.get("N", "Not listed")))
        p.metric("P", str(nutrients.get("P", "Not listed")))
        k.metric("K", str(nutrients.get("K", "Not listed")))
        st.write(f"**NPK reference:** {recommendation.get('npk') or 'Not listed'}")
        st.write(f"**Purpose:** {recommendation.get('purpose') or 'No purpose recorded in the local dataset.'}")
        match_label = "Disease-specific crop record" if recommendation.get("matched_by") == "exact crop and disease" else "Crop-level fallback; no disease-specific fertilizer row was available"
        st.caption(f"Recommendation match: {match_label}.")
        st.caption("NPK values are transcribed from the local crop/disease reference CSV; units and soil thresholds are not specified in that source. Use a current soil test and local extension advice before applying nutrients.")
        if recommendation.get("timing"):
            st.caption(f"Timing in source data: {recommendation['timing']}. Selected growth stage: {recommendation.get('growth_stage') or 'not supplied'}. The fertilizer CSV does not contain an explicit growth-stage field.")
        st.markdown("**Product recommendation (local fertilizer record)**")
        st.write(f"{recommendation.get('fertilizer_name') or 'Fertilizer name not listed'} · NPK {recommendation.get('npk') or 'not listed'}")
        st.caption(f"Suitable crop: {recommendation.get('crop', 'not listed')} · Selected growth stage: {recommendation.get('growth_stage', 'not supplied')} (stage tags are absent from the NPK CSV) · Purpose: {recommendation.get('purpose') or 'not listed'}")
        soil_reference = recommendation.get("soil_reference")
        if soil_reference:
            st.caption(f"Crop soil reference: {soil_reference.get('soil_type', 'not listed')}; pH {soil_reference.get('ph_min', '?')}–{soil_reference.get('ph_max', '?')}; water need {soil_reference.get('water_requirement', 'not listed')}.")
        soil_context = recommendation.get("soil_context") or {}
        if soil_context:
            st.write("**Provided soil-test context:**")
            for label, value in soil_context.items():
                st.write(f"- {label}: {value}")
        if stage_guidance:
            st.markdown("**Growth-stage guidance from the local recommendation library**")
            for item in stage_guidance:
                st.markdown(f"- {item}")
    elif stage_guidance:
        st.markdown("**Recommended fertilizer:** Stage-specific local guidance")
        for item in stage_guidance:
            st.markdown(f"- {item}")
    else:
        render_empty_state("Insufficient fertilizer data", recommendation.get("message") or "No fertilizer recommendation is available yet. Complete a crop and growth-stage assessment first.")

    if products:
        st.markdown("**Fertilizer products in the local catalog**")
        for product in products:
            st.markdown(f"- **{product.get('product_name', 'Fertilizer')}** · Type: {product.get('fertilizer_type', 'not listed')} · NPK: {product.get('NPK', 'not listed')}")
            st.caption(f"Suitable crop: {product.get('crop', 'not listed')} · Suitable stage: {', '.join(product.get('suitable_growth_stage', [])) or 'not specified'} · Purpose: {', '.join(product.get('suitable_disease', [])) or 'not specified'}")
            if product.get("reference_price"):
                st.caption(f"Catalog price reference only (not live): {product['reference_price']} · Catalog availability only (not live): {product.get('availability') or 'not listed'}")

USERS = {"admin": "admin123", "farmer": "crop2024", "demo": "demo"}

# ── LOGIN PAGE ────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("""
        <div class="login-showcase">
            <div class="brand-mark">FI</div>
            <div class="login-eyebrow">SMART FARMING, MADE PRACTICAL</div>
            <h1>Healthier crops begin with an early signal.</h1>
            <p>Detect crop leaf diseases, understand their severity, and find locally stored care guidance in one simple workspace.</p>
            <div class="login-pills"><span>Local AI</span><span>Plant health</span><span>Sustainable care</span></div>
        </div>
        """, unsafe_allow_html=True)
    with right:
        with st.container(border=True):
            st.markdown('<div class="login-form-title">Welcome to FRAM IQ</div><div class="login-form-subtitle">Sign in to your crop health workspace.</div>', unsafe_allow_html=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.sidebar.button("Sign in", width="stretch", type="primary"):
                if username in USERS and USERS[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            st.caption("Demo access: username **demo**, password **demo**")
    st.stop()
# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    if st.session_state.get("app_navigation") not in NAV_OPTIONS:
        st.session_state.app_navigation = PAGE_OPTIONS[0]
    st.session_state.setdefault("sidebar_navigation", st.session_state.app_navigation)
    st.markdown("## 🌱 FARMIQ")
    st.radio(
        "Application navigation", NAV_OPTIONS, format_func=format_page_label,
        key="sidebar_navigation", label_visibility="collapsed", on_change=sync_sidebar_navigation,
    )
    with st.container(key="sidebar-bottom-section"):
        st.markdown(f"👤 **Profile**  ·  {st.session_state.username}")
        if st.button("🚪 Logout", key="sidebar_logout", width="stretch"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state["app_navigation"] = PAGE_OPTIONS[0]
            st.session_state["sidebar_navigation"] = PAGE_OPTIONS[0]
            st.rerun()

page = render_top_navigation()

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.markdown("""
    <div class="hero">
        <h1>🌱 FARMIQ</h1>
        <p>AI-powered crop health and sustainable farming assistant</p>
    </div>
    """, unsafe_allow_html=True)

    from predict import is_model_available, TRAINED_CROPS
    import pandas as pd
    from datetime import datetime, timedelta

    metrics_path = Path(__file__).parent / "models" / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    rows = [dict(row) for row in get_predictions(limit=100000)]
    now = datetime.now().astimezone()
    recent_week = 0
    for row in rows:
        try:
            if datetime.fromisoformat(row["date"]) >= now - timedelta(days=7):
                recent_week += 1
        except (ValueError, TypeError):
            pass

    healthy_rows = [r for r in rows if str(r.get("disease", "")).strip().lower() == "healthy"]
    disease_rows = [r for r in rows if str(r.get("disease", "")).strip().lower() not in {"healthy", "", "unknown"}]
    model_accuracy = f"{metrics['accuracy']:.1%}" if "accuracy" in metrics else "Not evaluated"
    benchmark_note = f"Measured on {metrics['evaluation_split']}" if metrics.get("evaluation_split") else "No evaluation metrics available"
    render_kpis([
        ("Leaf Scans Processed", len(rows), f"+{recent_week} this week" if rows else "No scan history yet"),
        ("AI Benchmark Score", model_accuracy, benchmark_note),
        ("Crops Supported", len(TRAINED_CROPS)),
        ("Diseases Detected", sum(1 for name in json.loads((Path(__file__).parent / "models" / "class_names.json").read_text(encoding="utf-8")) if "healthy" not in name.lower())),
        ("Healthy Plants", len(healthy_rows)),
        ("Farmers / Users", "—"),
    ])

    with st.container(border=True):
        st.markdown("### 🍃 Ready to check a leaf?")
        st.caption("Start with a crop photo to get disease detection, severity, treatment, and nutrient guidance.")

    st.subheader("Recent Leaf Scans")
    if rows:
        recent_rows = []
        for row in rows[:6]:
            status = "Healthy" if str(row.get("disease", "")).lower() == "healthy" else "Review recommended"
            recent_rows.append({
                "Crop": row.get("crop", ""), "Disease": row.get("disease", ""),
                "Confidence": f"{float(row.get('confidence') or 0):.1%}",
                "Severity": row.get("severity", "Unknown"), "Date": row.get("date", "")[:19].replace("T", " "),
                "Status": status,
            })
        st.dataframe(pd.DataFrame(recent_rows), width="stretch", hide_index=True)
    else:
        st.info("No leaf scans yet. Start your first scan to build your crop health history.")

    st.subheader("Crop Health Overview")
    health_counts = {
        "Healthy": len(healthy_rows),
        "Mild": sum(str(r.get("severity", "")).lower() == "low" for r in disease_rows),
        "Moderate": sum(str(r.get("severity", "")).lower() == "moderate" for r in disease_rows),
        "Severe": sum(str(r.get("severity", "")).lower() in {"high", "very high"} for r in disease_rows),
    }
    if rows:
        st.bar_chart(pd.DataFrame({"Scans": health_counts}), color="#22c55e")
    else:
        st.caption("Health overview will populate after the first successful scan.")

    st.subheader("Model Crop Coverage")
    crop_categories = {
        "Cereals": [c for c in TRAINED_CROPS if c == "Corn/Maize"],
        "Vegetables": [c for c in TRAINED_CROPS if c in {"Tomato", "Potato", "Chili"}],
        "Fruits": [c for c in TRAINED_CROPS if c in {"Apple", "Grape"}],
        "Pulses": [],
        "Other model crops": [c for c in TRAINED_CROPS if c not in {"Corn/Maize", "Tomato", "Potato", "Chili", "Apple", "Grape"}],
    }
    category_columns = st.columns(len(crop_categories))
    for column, (category, crops_in_category) in zip(category_columns, crop_categories.items()):
        with column:
            st.markdown(f"**{category}**")
            st.write(", ".join(sorted(crops_in_category)) if crops_in_category else "No model-supported crops")

    st.subheader("Quick Actions")
    actions = [
        ("Start a New Scan", PAGE_OPTIONS[1]), ("View Disease Results", PAGE_OPTIONS[2]),
        ("Fertilizer Advisory", PAGE_OPTIONS[5]), ("Treatment & Cure", PAGE_OPTIONS[4]),
        ("View Scan History", PAGE_OPTIONS[3]),
    ]
    action_columns = st.columns(len(actions))
    for index, ((label, target), column) in enumerate(zip(actions, action_columns)):
        with column:
            st.button(label, key=f"dashboard_action_{index}", width="stretch",
                      on_click=set_active_page, args=(target,))

    if not is_model_available():
        st.warning("Trained model not found. Run python train_model.py to restore the disease scanner.")

elif page == "🔬 Crop Scanner":
    st.markdown("""
    <div class="hero">
        <h1>🔬 Crop Disease Scanner</h1>
        <p>Upload a leaf image for AI-powered disease detection and recommendations</p>
    </div>
    """, unsafe_allow_html=True)

    from predict import predict_disease, is_model_available
    from severity import estimate_severity
    # Streamlit reruns this script in a long-lived process. If this helper was
    # added while the server was already running, Python may still hold an older
    # version of the module in sys.modules. Reload that stale module before
    # binding the recommendation functions.
    import importlib
    import recommendation_engine
    if not hasattr(recommendation_engine, "get_fertilizer_products"):
        recommendation_engine = importlib.reload(recommendation_engine)
    get_recommendation = recommendation_engine.get_recommendation
    get_products = recommendation_engine.get_products
    get_fertilizer_products = recommendation_engine.get_fertilizer_products
    from services.fertilizer_recommendation import get_fertilizer_recommendation

    # ── Step 1: Crop & Growth Stage ───────────────────────────────────────────
    st.markdown('<div class="section-header">Step 1 — Select Crop & Growth Stage</div>',
                unsafe_allow_html=True)

    from predict import TRAINED_CROPS
    SUPPORTED_CROPS = ["Tomato", "Potato", "Corn/Maize", "Apple", "Grape", "Chili"]
    GROWTH_STAGES = ["Seedling", "Vegetative", "Flowering", "Fruiting", "Maturity"]

    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Select Crop", [c for c in SUPPORTED_CROPS if c in TRAINED_CROPS], index=0)
    with col2:
        growth_stage = st.selectbox("Select Growth Stage", GROWTH_STAGES)

    render_scan_workflow(active_step=1)

    soil_n = soil_p = soil_k = soil_ph = soil_moisture = None
    with st.expander("Optional soil-test information"):
        has_soil_test = st.checkbox("I have current soil test values", key="scanner_has_soil_test")
        if has_soil_test:
            soil_cols = st.columns(4)
            soil_n = soil_cols[0].number_input("Soil N (test units)", min_value=0.0, value=0.0, key="scanner_soil_n")
            soil_p = soil_cols[1].number_input("Soil P (test units)", min_value=0.0, value=0.0, key="scanner_soil_p")
            soil_k = soil_cols[2].number_input("Soil K (test units)", min_value=0.0, value=0.0, key="scanner_soil_k")
            soil_ph = soil_cols[3].number_input("Soil pH", min_value=0.0, max_value=14.0, value=6.5, step=0.1, key="scanner_soil_ph")
            soil_moisture = st.selectbox("Soil moisture observation", ["Not recorded", "Low", "Moderate", "High"], key="scanner_soil_moisture")
            if soil_moisture == "Not recorded":
                soil_moisture = None

    if not is_model_available():
        st.markdown("""
        <div class="warn-box">
        ⚠️ <strong>Trained model not found.</strong>
        Run <code>python train_model.py</code> first.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── Step 2: Upload Image ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">Step 2 — Upload Leaf Image</div>',
                unsafe_allow_html=True)

    if "leaf_upload_widget_version" not in st.session_state:
        st.session_state.leaf_upload_widget_version = 0

    def clear_leaf_upload():
        st.session_state.leaf_upload_widget_version += 1

    st.sidebar.button("Remove uploaded image", on_click=clear_leaf_upload)
    uploaded = st.file_uploader(
        "Upload a clear leaf image (JPG / PNG / WEBP)",
        type=["jpg", "jpeg", "png", "webp"],
        max_upload_size=10,
        key=f"leaf_upload_{st.session_state.leaf_upload_widget_version}",
        help="For best results: use a well-lit, close-up photo of a single leaf on a plain background."
    )
    camera_image = st.camera_input("Or take a leaf photo on your device")
    if uploaded is None and camera_image is not None:
        uploaded = camera_image

    uploaded_name = uploaded.name if uploaded else ""
    if not uploaded:
        st.info("Please upload a clear crop leaf image to begin analysis.")
        sample_root = Path(__file__).parent / "static" / "sample_images"
        sample_paths = sorted((p for p in sample_root.iterdir()
                               if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}),
                              key=lambda p: p.name.lower()) if sample_root.exists() else []
        if sample_paths:
            st.markdown("### Try a Sample Image")
            sample = st.selectbox("Choose a local sample", sample_paths, format_func=lambda p: p.stem.replace("_", " "))
            st.image(str(sample), width=240)
            if st.sidebar.button("Analyze selected sample"):
                image = Image.open(sample)
                uploaded_name = sample.name
                uploaded_size = sample.stat().st_size
            else:
                st.stop()
        else:
            st.caption("Add legally reusable examples to `static/sample_images/` to enable sample analysis.")
            st.stop()

    if uploaded:
        uploaded_size = uploaded.size
    if uploaded_size > 10 * 1024 * 1024:
        st.error("Image size must be below 10 MB.")
        st.stop()

    # Validate image
    try:
        if uploaded:
            image = Image.open(uploaded)
            image.verify()
            image = Image.open(uploaded)
        else:
            image.verify()
            image = Image.open(sample)
    except Exception:
        st.error("Invalid or corrupted image. Use JPG, JPEG, PNG, or WEBP.")
        st.stop()
    if min(image.size) < 64:
        st.warning("Image quality may reduce prediction accuracy. Please upload a clear leaf image.")
    if image.width * image.height > 40000000:
        st.error("Image resolution is too large to process safely.")
        st.stop()

    col_img, col_res = st.columns([1, 1.6])

    with col_img:
        st.image(image, caption="Uploaded Leaf Image", width="stretch")
        analyze_disease = st.button(
            "Analyze Disease",
            type="primary",
            key="analyze_disease",
            use_container_width=True,
        )

    if not analyze_disease:
        st.info("Review the preview, then select Analyze Disease to run the local model.")
        st.stop()

    # ── Step 3: Prediction ────────────────────────────────────────────────────
    with col_res:
        st.markdown('<div class="section-header">Step 3 — Disease Detection Result</div>',
                    unsafe_allow_html=True)

        with st.spinner("Analyzing leaf image..."):
            try:
                result = predict_disease(image, selected_crop=crop)
            except ValueError as e:
                st.error(str(e))
                st.stop()
            except Exception as e:
                st.error(f"Prediction error: {e}")
                st.stop()

        if result["low_confidence"]:
            st.markdown(f"""
            <div class="result-box low-conf">
                <h2>⚠️ Low Confidence</h2>
                <p>Confidence: {result['confidence_pct']}</p>
                <p>Please upload a clearer, well-lit leaf image.</p>
            </div>""", unsafe_allow_html=True)
        else:
            css = "healthy" if result["status"] == "Healthy" else "diseased"
            icon = "✅" if result["status"] == "Healthy" else "⚠️"
            st.markdown(f"""
            <div class="result-box {css}">
                <h2>{icon} {result['status']}</h2>
                <p><strong>Crop:</strong> {result['crop']}</p>
                <p><strong>Disease:</strong> {result['disease']}</p>
                <p><strong>Confidence:</strong> {result['confidence_pct']}</p>
            </div>""", unsafe_allow_html=True)

        conf_pct = result["confidence"] * 100
        st.markdown(f"**Confidence: {conf_pct:.2f}%**")
        st.markdown(f"**Selected crop:** {crop} &nbsp; · &nbsp; **Growth stage:** {growth_stage}")
        st.markdown("#### Top predictions")
        for prediction in result.get("top_predictions", []):
            pct = prediction["confidence"] * 100
            st.caption(f"{prediction['crop']} · {prediction['disease']} — {pct:.2f}%")
            st.progress(min(max(float(prediction["confidence"]), 0.0), 1.0))
        st.caption("Disease confidence is calculated among the trained classes for the selected crop.")
        st.markdown(f"""
        <div class="conf-bar-bg">
            <div class="conf-bar-fill" style="width:{min(conf_pct,100):.1f}%"></div>
        </div>""", unsafe_allow_html=True)

        # ── Step 4: Severity ──────────────────────────────────────────────────
        st.markdown('<div class="section-header">Step 4 — Severity Estimate</div>',
                    unsafe_allow_html=True)

        with st.spinner("Estimating severity..."):
            sev_result = estimate_severity(image)

        if result["status"] == "Healthy":
            st.success("No disease detected — severity assessment not applicable.")
            sev_result["severity"] = "N/A"
        elif "error" in sev_result:
            st.warning(f"Severity estimation unavailable ({sev_result['error']}). Severity will be reported as unknown; treatment guidance will use a general baseline plan.")
            sev_result["severity"] = "Unknown"
        else:
            sev = sev_result["severity"]
            pct = sev_result["affected_area_pct"]
            css_map = {"Low": "sev-low", "Moderate": "sev-moderate",
                       "High": "sev-high", "Very High": "sev-veryhigh"}
            st.markdown(f"""
            <span class="severity-badge {css_map.get(sev, 'sev-low')}">
                {sev} Severity
            </span>
            <br><small style="color:#666;">
                ⚠️ Estimated affected leaf area: ~{pct}%
                (visual estimate only — not a clinical measurement)
            </small>""", unsafe_allow_html=True)

    # ── Stop here if low confidence ───────────────────────────────────────────
    if result["low_confidence"]:
        st.stop()

    disease    = result["disease"]
    severity   = sev_result.get("severity", "Unknown")

    # ── Step 5: Recommendations ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-header">Step 5 — Treatment & Fertilizer Recommendations</div>',
                unsafe_allow_html=True)

    rec = get_recommendation(crop, disease, severity, growth_stage)
    nutrient_data = get_fertilizer_recommendation(
        crop, disease, growth_stage,
        soil_n=soil_n, soil_p=soil_p, soil_k=soil_k,
        soil_ph=soil_ph, soil_moisture=soil_moisture,
    )
    fertilizer_catalog = get_fertilizer_products(crop, growth_stage)
    if severity == "Unknown" and rec.get("found"):
        st.info("Severity could not be estimated. The treatment plan below uses general baseline guidance, not a severity-specific assessment.")
    st.markdown("### Scan History")
    st.caption("Successful scans are saved automatically to Plant Records on this device. Add or edit field notes from the saved record.")
    try:
        from werkzeug.utils import secure_filename
        from uuid import uuid4

        upload_dir = Path(__file__).parent / "static" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(uploaded_name).suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            ext = ".jpg"
        safe_name = secure_filename(f"{uuid4().hex}{ext}")
        image_path = upload_dir / safe_name
        fmt = "JPEG" if ext in {".jpg", ".jpeg"} else ("PNG" if ext == ".png" else "WEBP")
        image_to_save = image.convert("RGB") if fmt == "JPEG" else image
        image_to_save.save(image_path, format=fmt)
        fertilizer_history = []
        if nutrient_data.get("found"):
            fertilizer_history.extend([
                f"Fertilizer: {nutrient_data.get('fertilizer_name')}",
                f"NPK reference: {nutrient_data.get('npk')}",
                f"Purpose: {nutrient_data.get('purpose') or 'not listed'}",
                f"Source timing: {nutrient_data.get('timing') or 'not listed'}",
            ])
        else:
            fertilizer_history.extend(rec.get("fertilizer", []))
        if nutrient_data.get("found"):
            fertilizer_history.extend(rec.get("fertilizer", []))
        if fertilizer_catalog:
            fertilizer_history.extend(
                f"Catalog product: {p.get('product_name')} - NPK {p.get('NPK', 'not listed')}"
                for p in fertilizer_catalog
            )
        if nutrient_data.get("soil_context"):
            fertilizer_history.append(f"Farmer-provided soil context: {nutrient_data['soil_context']}")
        saved_record_id = save_prediction(
            crop=crop,
            growth_stage=growth_stage,
            disease=disease,
            confidence=result["confidence"],
            severity=severity,
            image_path=f"static/uploads/{safe_name}",
            treatment=rec.get("treatment", []),
            fertilizer=fertilizer_history,
            notes="",
        )
        st.success(f"Scan saved to Plant Records (record #{saved_record_id}).")
    except Exception as exc:
        st.error(f"Could not save this scan to history: {exc}")

    if not rec["found"]:
        st.warning("No specific treatment entry was found for this combination. General sustainable monitoring guidance is shown where available.")
    treatment_col, nutrient_col = st.columns(2)
    with treatment_col:
        st.markdown("#### Treatment & Cure")
        if rec.get("treatment"):
            st.markdown("**Immediate and disease-management actions**")
            for item in rec["treatment"]:
                st.markdown(f"- {item}")
        if rec.get("natural_options"):
            st.markdown("**Sustainable / botanical options**")
            for item in rec["natural_options"]:
                st.markdown(f"- {item}")
        elif not rec.get("treatment"):
            st.markdown("- Remove infected plant debris and clean tools between plants.")
            st.markdown("- Maintain airflow and avoid unnecessary overhead irrigation where practical.")
            st.markdown("- Consult a local extension officer if symptoms persist or worsen.")
        if rec.get("monitoring"):
            st.markdown("**Monitoring plan**")
            for item in rec["monitoring"]:
                st.markdown(f"- {item}")
        treatment_products = [
            p for p in get_products(crop, disease, growth_stage)
            if "fertilizer" not in str(p.get("fertilizer_type", "")).lower()
            and "compost" not in str(p.get("fertilizer_type", "")).lower()
        ]
        if treatment_products:
            st.markdown("**Disease-treatment products in the local reference catalog**")
            st.caption("Reference listings only. Verify local registration, label directions, current price, and stock with a qualified local source.")
            for product in treatment_products:
                st.write(f"{product.get('product_name')} ({product.get('fertilizer_type', 'type not listed')})")
                st.caption("Price/availability data not live; follow the current locally approved product label.")
    with nutrient_col:
        render_fertilizer_card(nutrient_data, rec.get("fertilizer", []), fertilizer_catalog)

    if st.sidebar.button("View Full Recommendation", key="view_full_recommendation",
                 on_click=set_active_page, args=(PAGE_OPTIONS[2],)):
        pass

    st.markdown("---")
    st.markdown("### Scan Again")
    st.info(f"Re-scan interval in the local guidance: { {'Low': '7-10 days', 'Moderate': '3-5 days', 'High': '2-3 days', 'Very High': 'daily'}.get(severity, '5-7 days') }")
    if st.sidebar.button("🔄 Scan Another Image"):
        st.rerun()

# ── SEASONAL ADVISORY ─────────────────────────────────────────────────────────
elif page == "📅 Seasonal Advisory":
    from services.advisory_service import get_seasonal_advisory, get_regions
    from services.season_service import get_current_season

    st.markdown("""
    <div class="hero">
        <h1>📅 Seasonal Advisory</h1>
        <p>Region and season-specific farming guidance for Indian agriculture</p>
    </div>
    """, unsafe_allow_html=True)

    regions = get_regions()
    current_season = get_current_season()

    col1, col2 = st.columns(2)
    with col1:
        region = st.selectbox("Select Region", regions)
    with col2:
        season = st.selectbox("Select Season", ["Kharif", "Rabi", "Zaid"],
                              index=["Kharif", "Rabi", "Zaid"].index(current_season))

    adv = get_seasonal_advisory(region, season)

    st.markdown(f"""
    <div class="info-card green">
        <h4>📍 {adv.get('region', region)} — {adv.get('season', season)}</h4>
        <p>{adv['advisory']}</p>
    </div>""", unsafe_allow_html=True)

    if "temp_range" in adv:
        c1, c2, c3 = st.columns(3)
        c1.metric("Temperature", adv["temp_range"])
        c2.metric("Humidity", adv["humidity"])
        c3.metric("Rainfall", adv["rainfall"])

    st.markdown("---")
    st.markdown("### Season Guide")
    for s, months, crops_s in [
        ("Kharif", "June – September",  "Rice, Maize, Cotton, Soybean, Groundnut"),
        ("Rabi",   "October – March",   "Wheat, Potato, Mustard, Peas, Gram"),
        ("Zaid",   "April – June",      "Watermelon, Cucumber, Muskmelon, Fodder"),
    ]:
        st.markdown(f"""
        <div class="info-card green">
            <h4>{s} ({months})</h4>
            <p>{crops_s}</p>
        </div>""", unsafe_allow_html=True)

elif page == PAGE_OPTIONS[3]:
    st.title("Plant Records")
    st.caption("Scan history is stored locally in SQLite on this device.")
    try:
        import pandas as pd
        from datetime import date
        rows = [dict(r) for r in get_predictions(limit=100000)]
        if not rows:
            render_empty_state("No leaf scans yet", "Start your first scan to build your crop health history. Successful scans are saved automatically.")
            st.sidebar.button("Start a Crop Scan", on_click=set_active_page, args=(PAGE_OPTIONS[1],))
        else:
            data = pd.DataFrame(rows)
            data["_date"] = pd.to_datetime(data["date"], errors="coerce").dt.date
            filters = st.columns(4)
            crop_filter = filters[0].selectbox("Crop", ["All"] + sorted(data["crop"].dropna().unique().tolist()))
            disease_filter = filters[1].selectbox("Disease", ["All"] + sorted(data["disease"].dropna().unique().tolist()))
            severity_filter = filters[2].selectbox("Severity", ["All"] + sorted(data["severity"].dropna().unique().tolist()))
            valid_dates = data["_date"].dropna()
            date_range = filters[3].date_input("Date range", value=(valid_dates.min(), valid_dates.max()))
            filtered = data.copy()
            if crop_filter != "All":
                filtered = filtered[filtered["crop"] == crop_filter]
            if disease_filter != "All":
                filtered = filtered[filtered["disease"] == disease_filter]
            if severity_filter != "All":
                filtered = filtered[filtered["severity"] == severity_filter]
            if isinstance(date_range, tuple) and len(date_range) == 2:
                filtered = filtered[filtered["_date"].between(date_range[0], date_range[1])]
            filtered["Status"] = filtered["disease"].map(lambda d: "Healthy" if str(d).lower() == "healthy" else "Review recommended")
            filtered["Treatment"] = filtered["treatment"].fillna("").map(lambda value: str(value).splitlines()[0][:64] if str(value).strip() else "Not recorded")
            filtered["Fertilizer"] = filtered["fertilizer"].fillna("").map(lambda value: str(value).splitlines()[0][:64] if str(value).strip() else "Insufficient data")
            display = filtered.rename(columns={
                "date": "Date", "crop": "Crop", "growth_stage": "Growth Stage",
                "disease": "Disease", "confidence": "Confidence", "severity": "Severity",
            })
            display["Confidence"] = display["Confidence"].map(lambda v: f"{float(v):.1%}")
            st.metric("Scans in history", len(rows), f"{len(filtered)} match filters")
            st.dataframe(display[["Date", "Crop", "Growth Stage", "Disease", "Confidence", "Severity", "Treatment", "Fertilizer", "Status"]],
                         width="stretch", hide_index=True)
            if not filtered.empty:
                ids = filtered["id"].astype(int).tolist()
                selected_id = st.selectbox("Open a record", ids, format_func=lambda record_id: f"#{record_id} | {filtered.loc[filtered['id'] == record_id, 'crop'].iloc[0]} | {filtered.loc[filtered['id'] == record_id, 'disease'].iloc[0]}")
                record = next(item for item in rows if int(item["id"]) == int(selected_id))
                left, right = st.columns(2)
                with left:
                    image_path = Path(__file__).parent / str(record.get("image_path") or "")
                    if record.get("image_path") and image_path.exists():
                        st.image(str(image_path), caption="Saved leaf image", width="stretch")
                    else:
                        st.caption("No saved image reference for this record.")
                with right:
                    st.subheader(f"{record['crop']} | {record['disease']}")
                    st.write(f"Growth stage: {record['growth_stage']} | Confidence: {float(record['confidence']):.1%} | Severity: {record['severity']}")
                    st.markdown("**Treatment recommendation**")
                    st.write(record.get("treatment") or "No specific treatment details were stored.")
                    st.markdown("**Fertilizer and nutrient recommendation**")
                    st.write(record.get("fertilizer") or "Insufficient fertilizer data was available for this record.")
                    st.markdown("**Field notes**")
                    note = st.text_area("Notes", value=record.get("notes", ""), key=f"note_{selected_id}")
                    if st.sidebar.button("Update notes", key=f"update_note_{selected_id}"):
                        from database import update_notes
                        update_notes(selected_id, note)
                        st.success("Notes updated.")
    except Exception as exc:
        st.error(f"Plant records are unavailable: {exc}")

elif page == "📊 Model Performance":
    st.title("AI Benchmark · Model Performance")
    st.caption("AI Benchmark Score represents model performance on the available validation/test dataset; it is not a confidence score for an individual leaf.")
    metric_file = Path(__file__).parent / "models" / "metrics.json"
    if not metric_file.exists():
        st.warning("Model evaluation has not been generated yet. Run `python evaluate_model.py`.")
    else:
        metrics = json.loads(metric_file.read_text(encoding="utf-8"))
        render_kpis([
            ("Overall accuracy", f"{metrics['accuracy']:.2%}"),
            ("Precision (macro)", f"{metrics['precision_macro']:.2%}"),
            ("Recall (macro)", f"{metrics['recall_macro']:.2%}"),
            ("F1 (macro)", f"{metrics['f1_macro']:.2%}"),
        ])
        st.caption(f"Evaluated on {metrics['evaluation_split']} · {metrics['samples']} images")
        import pandas as pd
        st.subheader("Class-wise performance")
        class_rows = [{"Class": k, "Precision": v["precision"], "Recall": v["recall"], "F1": v["f1-score"], "Samples": v["support"]}
                      for k, v in metrics["class_wise"].items()]
        st.dataframe(pd.DataFrame(class_rows).style.format({"Precision": "{:.1%}", "Recall": "{:.1%}", "F1": "{:.1%}"}),
                     width="stretch", hide_index=True)
        st.subheader("Confusion matrix")
        labels = metrics["class_names"]
        cm = pd.DataFrame(metrics["confusion_matrix"], index=labels, columns=labels)
        st.dataframe(cm, width="stretch")
        history = Path(__file__).parent / "models" / "training_history.png"
        if history.exists():
            st.subheader("Training Accuracy vs Validation Accuracy · Training Loss vs Validation Loss")
            st.image(str(history), caption="Actual training history saved with the model", width="stretch")
    st.info("Model: MobileNetV2 · Transfer learning · 224 × 224 RGB · outputs are the saved model classes.")

elif page == "📚 Disease Knowledge":
    st.title("Disease Knowledge")
    import pandas as pd
    knowledge_path = Path(__file__).parent / "data" / "disease_information.csv"
    if knowledge_path.exists():
        # The legacy CSV includes a few unquoted commas and malformed tail rows.
        knowledge = pd.read_csv(knowledge_path, engine="python", on_bad_lines="skip").fillna("")
        search = st.text_input("Search crop or disease")
        crop_filter = st.selectbox("Crop", ["All"] + sorted(knowledge["crop"].unique().tolist()))
        if crop_filter != "All":
            knowledge = knowledge[knowledge["crop"] == crop_filter]
        if search:
            mask = knowledge.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
            knowledge = knowledge[mask]
        if knowledge.empty:
            st.info("No matching local article found.")
        for _, item in knowledge.iterrows():
            with st.expander(f"{item['crop']} · {item['disease']}"):
                st.write(f"**Symptoms:** {item['symptoms']}")
                st.write(f"**Possible cause:** {item['causes']}")
                st.write(f"**Management:** {item['treatment']}")
                st.write(f"**Prevention:** {item['prevention']}")
                st.caption("Chemical products, where mentioned, must be locally approved and used strictly according to their label.")
    else:
        st.warning("Local disease reference data is not available.")

elif page == "❓ FAQ":
    st.title("Frequently Asked Questions")
    faq = {
        "How accurate is the AI model?": "Check Model Performance for measured held-out test metrics. Metrics are not shown until the evaluation script has been run.",
        "What image should I upload?": "Use a sharp, well-lit close-up of one leaf. Keep the leaf in focus and avoid strong shadows or busy backgrounds.",
        "Can the AI detect all crop diseases?": "No. The classifier only recognizes the 27 classes used to train it across six supported crops.",
        "Why is confidence sometimes low?": "Blur, lighting, unfamiliar symptoms, crop mismatch, and images outside the training classes can all reduce confidence.",
        "Can I use treatment recommendations directly?": "Treat these as decision support. Confirm diagnosis and local product registration with an agricultural expert; always follow product labels.",
        "What if the disease is not recognized?": "Take another clear image, verify crop selection, and consult a local extension officer if symptoms persist.",
    }
    for question, answer in faq.items():
        with st.expander(question):
            st.write(answer)

elif page == "ℹ️ About Project":
    st.title("FRAM IQ")
    st.subheader("AI-Powered Crop Disease Detection & Sustainable Fertilizer Management")
    st.write("An AI-powered crop disease detection and sustainable agricultural advisory system designed to assist farmers and students in early identification of crop diseases.")
    st.markdown("**Technologies:** Python · TensorFlow · MobileNetV2 · Streamlit · SQLite · HTML/CSS")
    st.markdown("**Architecture:** Image input → validation and preprocessing → MobileNetV2 → disease class and confidence → severity estimate → treatment and nutrient guidance → SQLite plant records")
    st.info("Core diagnosis, recommendations, seasonal guidance, and records run locally without API keys. Weather values are regional seasonal averages, not live forecasts.")

elif page == "🌦 Weather & Risk":
    st.title("Weather & Risk Advisory")
    st.caption("Offline regional seasonal context · not a live weather forecast")
    from services.advisory_service import get_seasonal_advisory, get_regions
    from services.season_service import get_current_season
    region = st.selectbox("Region", get_regions())
    season = st.selectbox("Season", ["Kharif", "Rabi", "Zaid"], index=["Kharif", "Rabi", "Zaid"].index(get_current_season()))
    context = get_seasonal_advisory(region, season)
    if context.get("temp_range"):
        a, b, c, d = st.columns(4)
        a.metric("Typical temperature", context["temp_range"])
        b.metric("Typical humidity", context["humidity"])
        c.metric("Typical rainfall", context["rainfall"])
        d.metric("Wind", "Not available", "No wind data in offline dataset")
    advisory_text = str(context.get("advisory", "")).lower()
    if "very high" in advisory_text:
        risk_label = "Very high (stated in regional advisory)"
    elif "high disease" in advisory_text:
        risk_label = "High (stated in regional advisory)"
    elif "moderate disease" in advisory_text:
        risk_label = "Moderate (stated in regional advisory)"
    elif "disease" in advisory_text or "fungal" in advisory_text or "humidity" in advisory_text:
        risk_label = "Monitor (qualitative note)"
    else:
        risk_label = "Not rated by this dataset"
    st.metric("Regional disease-risk note", risk_label)
    st.write(context.get("advisory", "No regional advisory available."))
    st.warning("These are offline seasonal averages, not live weather. Wind data is unavailable. For immediate irrigation or disease decisions, check a current local forecast and consult your agricultural extension service.")

elif page == PAGE_OPTIONS[7]:
    st.title("AI Agronomy Advisory")
    st.caption("Local, rule-based decision support using saved scans and bundled crop, disease, soil-reference, and seasonal datasets. It is general guidance, not a verified prescription.")
    from predict import TRAINED_CROPS, _DISPLAY
    from recommendation_engine import get_recommendation, get_fertilizer_products
    from services.fertilizer_recommendation import get_fertilizer_recommendation
    from services.advisory_service import get_seasonal_advisory, get_regions
    from services.season_service import get_current_season
    latest_rows = get_predictions(limit=500)
    latest_by_crop = {}
    for row in latest_rows:
        latest_by_crop.setdefault(row["crop"], row)
    crop_options = sorted(TRAINED_CROPS)
    preferred_crop = latest_rows[0]["crop"] if latest_rows and latest_rows[0]["crop"] in crop_options else None
    crop = st.selectbox("Crop", crop_options, index=crop_options.index(preferred_crop) if preferred_crop else 0, key="agronomy_crop")
    previous = latest_by_crop.get(crop)
    stages = ["Seedling", "Vegetative", "Flowering", "Fruiting", "Maturity"]
    preferred_stage = previous["growth_stage"] if previous and previous["growth_stage"] in stages else "Vegetative"
    stage = st.selectbox("Growth stage", stages, index=stages.index(preferred_stage), key="agronomy_stage")
    conditions = sorted({d for class_name in json.loads((Path(__file__).parent / "models" / "class_names.json").read_text(encoding="utf-8"))
                         for c, d in [_DISPLAY.get(class_name, (class_name, "Unknown"))]
                         if c == crop and d != "Healthy"})
    condition_options = ["Healthy"] + conditions
    default_condition = previous["disease"] if previous and previous["disease"] in condition_options else "Healthy"
    condition = st.selectbox("Disease or health condition", condition_options,
                             index=condition_options.index(default_condition), key="agronomy_condition")
    severity = previous["severity"] if previous and previous["disease"] == condition else ("N/A" if condition == "Healthy" else "Unknown")
    confidence = float(previous["confidence"]) if previous and previous["disease"] == condition else None

    with st.expander("Optional soil-test inputs"):
        has_soil = st.checkbox("Include soil information", key="agronomy_has_soil")
        soil_n = soil_p = soil_k = soil_ph = soil_moisture = None
        if has_soil:
            soil_columns = st.columns(4)
            soil_n = soil_columns[0].number_input("Soil N (test units)", min_value=0.0, value=0.0, key="agronomy_soil_n")
            soil_p = soil_columns[1].number_input("Soil P (test units)", min_value=0.0, value=0.0, key="agronomy_soil_p")
            soil_k = soil_columns[2].number_input("Soil K (test units)", min_value=0.0, value=0.0, key="agronomy_soil_k")
            soil_ph = soil_columns[3].number_input("Soil pH", min_value=0.0, max_value=14.0, value=6.5, step=0.1, key="agronomy_soil_ph")
            soil_moisture = st.selectbox("Observed soil moisture", ["Not recorded", "Low", "Moderate", "High"], key="agronomy_soil_moisture")
            if soil_moisture == "Not recorded":
                soil_moisture = None

    region = st.selectbox("Weather region", get_regions(), key="agronomy_region")
    seasons = ["Kharif", "Rabi", "Zaid"]
    current_season = get_current_season()
    season = st.selectbox("Season", seasons, index=seasons.index(current_season), key="agronomy_season")
    weather_context = get_seasonal_advisory(region, season)
    disease_plan = get_recommendation(crop, condition, severity, stage)
    nutrient = get_fertilizer_recommendation(crop, condition, stage, soil_n, soil_p, soil_k, soil_ph, soil_moisture)
    fertilizer_products = get_fertilizer_products(crop, stage)

    st.subheader("Crop Health Status")
    health_columns = st.columns(4)
    health_columns[0].metric("Crop", crop)
    health_columns[1].metric("Growth stage", stage)
    health_columns[2].metric("Condition", condition)
    health_columns[3].metric("Visual severity", severity)
    if confidence is not None:
        st.caption(f"Previous matching scan confidence: {confidence:.1%}. Model confidence is not a guarantee of diagnosis.")
    else:
        st.caption("No matching saved scan is available; severity and confidence have not been measured for this advisory.")

    st.subheader("Disease Risk")
    risk_by_severity = {"N/A": "No disease severity assigned", "Low": "Low visual severity", "Moderate": "Moderate visual severity", "High": "High visual severity", "Very High": "Very high visual severity", "Unknown": "Not assessed"}
    st.write(risk_by_severity.get(severity, "Not assessed"))

    st.subheader("Treatment Guidance")
    if disease_plan.get("treatment"):
        for item in disease_plan["treatment"]:
            st.markdown(f"- {item}")
    else:
        render_empty_state("Insufficient treatment data", "No matching local treatment row exists. Confirm the condition with an agricultural extension service.")
    st.info("Use only locally approved crop-protection products and follow their current labels.")

    st.subheader("Fertilizer / Nutrient Guidance")
    render_fertilizer_card(nutrient, disease_plan.get("fertilizer", []), fertilizer_products)

    st.subheader("Irrigation Guidance")
    soil_reference = nutrient.get("soil_reference") or {}
    if soil_moisture:
        st.write(f"Observed moisture: {soil_moisture}. Crop reference water need: {soil_reference.get('water_requirement', 'not listed')}. Check root-zone moisture and avoid waterlogging or prolonged drought stress.")
    else:
        st.write(f"No soil-moisture reading supplied. Crop reference water need: {soil_reference.get('water_requirement', 'not listed')}. Check root-zone moisture before irrigation.")

    st.subheader("Weather Risk")
    if weather_context.get("temp_range"):
        weather_cols = st.columns(3)
        weather_cols[0].metric("Typical temperature", weather_context["temp_range"])
        weather_cols[1].metric("Typical humidity", weather_context["humidity"])
        weather_cols[2].metric("Typical rainfall", weather_context["rainfall"])
    st.write(weather_context.get("advisory", "No local seasonal advisory found."))
    st.caption("Weather values are regional seasonal averages, not live forecasts; wind data is not available.")

    st.subheader("Monitoring Plan")
    monitoring = disease_plan.get("monitoring", [])
    if monitoring:
        for item in monitoring:
            st.markdown(f"- {item}")
    else:
        st.write("Inspect leaves regularly and record a follow-up scan if symptoms change.")
    st.subheader("Sustainable Farming Recommendation")
    sustainable = disease_plan.get("natural_options", [])
    if sustainable:
        for item in sustainable:
            st.markdown(f"- {item}")
    else:
        st.write("Use sanitation, balanced crop nutrition based on a soil test, and locally suitable rotation or resistant varieties where available.")
    st.caption("This local advisory uses the selected crop/stage and the most recent matching scan when available. Verify actions with a qualified local agricultural professional.")

elif page == PAGE_OPTIONS[4]:
    st.title("Treatment & Cure")
    st.caption("Disease management stays separate from fertilizer and nutrient support.")
    latest = get_predictions(limit=1)
    if latest:
        record = latest[0]
        st.markdown("### Latest scan")
        render_disease_result_summary(dict(record), include_status=False)
        st.markdown("**Treatment saved from the scan**")
        st.write(record["treatment"] or "No specific treatment record was available; consult a local extension officer.")
        st.sidebar.button("Open complete scan result", on_click=set_active_page, args=(PAGE_OPTIONS[2],))
    else:
        render_empty_state("No scan result yet", "Run a crop scan first. You can still use the reference lookup below.")

    with st.expander("Look up another crop and disease"):
        from predict import TRAINED_CROPS
        from recommendation_engine import get_recommendation, get_products
        crop_options = sorted(TRAINED_CROPS)
        crop = st.selectbox("Crop", crop_options, key="treat_crop")
        class_names = json.loads((Path(__file__).parent / "models" / "class_names.json").read_text(encoding="utf-8"))
        from predict import _DISPLAY
        diseases = sorted({d for name in class_names for c, d in [_DISPLAY.get(name, (name, "Unknown"))] if c == crop and d != "Healthy"})
        disease = st.selectbox("Disease", diseases, key="treat_disease")
        stage = st.selectbox("Growth stage", ["Seedling", "Vegetative", "Flowering", "Fruiting", "Maturity"], key="treat_stage")
        if st.sidebar.button("Show treatment reference", key="show_treatment_reference"):
            plan = get_recommendation(crop, disease, "Unknown", stage)
            if plan.get("matched_growth_stage") and plan["matched_growth_stage"] != stage:
                st.caption(f"No {stage} treatment row exists; showing the {plan['matched_growth_stage']} local reference.")
            if plan.get("found"):
                st.markdown("**Immediate and sustainable actions**")
                for item in plan.get("treatment", []) + plan.get("natural_options", []):
                    st.markdown(f"- {item}")
                st.markdown("**Monitoring**")
                for item in plan.get("monitoring", []):
                    st.markdown(f"- {item}")
            else:
                render_empty_state("Insufficient treatment data", "No matching local guidance was found. Consult a local agricultural extension service.")
            products = [p for p in get_products(crop, disease, stage) if "fertilizer" not in str(p.get("fertilizer_type", "")).lower()]
            if products:
                st.markdown("**Disease-treatment catalog references**")
                st.caption("Verify local registration and follow the current product label; catalog price and availability are not live.")
                for item in products:
                    st.write(f"{item.get('product_name')} | {item.get('fertilizer_type')}")

elif page == PAGE_OPTIONS[5]:
    st.title("Fertilizer & Nutrient Advisory")
    st.caption("Crop, growth-stage and local dataset references. Soil-test inputs are optional; this does not diagnose nutrient deficiencies.")
    from predict import TRAINED_CROPS
    from recommendation_engine import get_recommendation, get_fertilizer_products
    from services.fertilizer_recommendation import get_fertilizer_recommendation
    latest_rows = get_predictions(limit=500)
    latest_by_crop = {}
    for row in latest_rows:
        latest_by_crop.setdefault(row["crop"], row)
    crop_options = sorted(TRAINED_CROPS)
    preferred_crop = latest_rows[0]["crop"] if latest_rows and latest_rows[0]["crop"] in crop_options else None
    crop = st.selectbox("Crop", crop_options, index=crop_options.index(preferred_crop) if preferred_crop else 0, key="fert_crop")
    latest_crop_record = latest_by_crop.get(crop)
    stages = ["Seedling", "Vegetative", "Flowering", "Fruiting", "Maturity"]
    preferred_stage = latest_crop_record["growth_stage"] if latest_crop_record and latest_crop_record["growth_stage"] in stages else "Vegetative"
    stage = st.selectbox("Growth stage", stages, index=stages.index(preferred_stage), key="fert_stage")
    disease = latest_crop_record["disease"] if latest_crop_record else "Healthy"
    severity = latest_crop_record["severity"] if latest_crop_record else "Low"
    if latest_crop_record:
        st.info(f"Using latest saved scan for this crop: {disease} | {severity} severity. Change crop/stage above to review another combination.")
    else:
        st.caption("No scan is stored for this crop; showing the healthy-crop nutrient reference.")
    soil_n = soil_p = soil_k = soil_ph = soil_moisture = None
    with st.expander("Optional soil-test information"):
        has_soil = st.checkbox("Enter current soil-test information", key="fert_has_soil")
        if has_soil:
            cols = st.columns(4)
            soil_n = cols[0].number_input("Soil N (test units)", min_value=0.0, value=0.0, key="fert_soil_n")
            soil_p = cols[1].number_input("Soil P (test units)", min_value=0.0, value=0.0, key="fert_soil_p")
            soil_k = cols[2].number_input("Soil K (test units)", min_value=0.0, value=0.0, key="fert_soil_k")
            soil_ph = cols[3].number_input("Soil pH", min_value=0.0, max_value=14.0, value=6.5, step=0.1, key="fert_soil_ph")
            soil_moisture = st.selectbox("Observed soil moisture", ["Not recorded", "Low", "Moderate", "High"], key="fert_soil_moisture")
            if soil_moisture == "Not recorded":
                soil_moisture = None
    nutrient = get_fertilizer_recommendation(crop, disease, stage, soil_n, soil_p, soil_k, soil_ph, soil_moisture)
    stage_plan = get_recommendation(crop, disease, severity, stage)
    products = get_fertilizer_products(crop, stage)
    render_fertilizer_card(nutrient, stage_plan.get("fertilizer", []), products)

elif page == "🧪 Disease Results":
    st.title("Disease Results")
    st.caption("Review your most recently saved diagnosis and its recommendations.")
    try:
        recent = get_predictions(limit=1)
        if not recent:
            render_empty_state("No leaf scans yet", "Start your first crop scan. Successful scans are saved here automatically.")
            st.sidebar.button("Start a Crop Scan", on_click=set_active_page, args=(PAGE_OPTIONS[1],))
        else:
            item = recent[0]
            render_disease_result_summary(dict(item))
            left, right = st.columns([1, 1.4])
            with left:
                if item["image_path"] and (Path(__file__).parent / item["image_path"]).exists():
                    st.image(str(Path(__file__).parent / item["image_path"]), width="stretch")
            with right:
                st.markdown("#### Treatment")
                st.write(item["treatment"] or "No treatment details were stored.")
                st.markdown("#### Fertilizer and nutrient guidance")
                st.write(item["fertilizer"] or "No nutrient guidance was stored.")
                st.markdown("#### Field notes")
                st.write(item["notes"] or "No field notes.")
            st.caption("Confidence is the model's class probability. Severity is a rough visual estimate, not a field measurement.")
            st.sidebar.button("Open Plant Records", on_click=set_active_page, args=(PAGE_OPTIONS[3],))
    except Exception as exc:
        st.error(f"Could not load the saved result: {exc}")

elif page == "🛒 Market Prices":
    st.title("Daily Vegetable Market Prices in India | Today's Mandi Rates")
    st.write("Explore indicative mandi benchmarks by state. Use official market portals to verify today's arrivals and rates before making a sale.")

    st.markdown("### Select State")
    states = [
        "Andhra Pradesh", "Telangana", "Karnataka", "Tamil Nadu", "Maharashtra",
        "Gujarat", "Punjab", "Haryana", "Uttar Pradesh", "Delhi", "Bihar",
        "West Bengal", "Kerala", "Madhya Pradesh", "Rajasthan", "Odisha",
    ]
    with st.sidebar.form("market_prices_form"):
        selected_market_state = st.selectbox("State", states)
        submitted = st.form_submit_button("Submit", type="primary", width="stretch")
    if submitted:
        st.session_state.market_prices_state = selected_market_state
    market_state = st.session_state.get("market_prices_state")

    st.markdown("🏛️ **Source Reference: AGMARKNET (Directorate of Marketing & Inspection, Ministry of Agriculture, Govt of India)**")
    st.markdown("[AGMARKNET.gov.in ↗](https://agmarknet.gov.in/) · [e-NAM Portal ↗](https://enam.gov.in/)")

    if market_state == "Andhra Pradesh":
        st.subheader("Andhra Pradesh APMC Mandi Benchmark Rates (05 Oct 2026)")
        st.caption("Indicative benchmark data · Sample timestamp: 05 Oct 2026 at 09:33 pm · Source attribution supplied: AGMARKNET & regional APMC feeds. Percentage changes compare with the 7-day average; values have not been independently verified.")
        prices = [
            ("Onion Big (పెద్ద ఉల్లిపాయ)", "Kg / Pcs", "₹30 ▲ 4.2%", "₹33–39"),
            ("Onion Small (చిన్న ఉల్లిపాయ)", "Kg / Pcs", "₹56 ▲ 13.5%", "₹62–73"),
            ("Tomato (టమోటా)", "Kg / Pcs", "₹22 ▲ 12.9%", "₹24–29"),
            ("Potato (బంగాళదుంప)", "Kg / Pcs", "₹24 ▲ 0.7%", "₹26–31"),
            ("Carrot (క్యారెట్)", "Kg / Pcs", "₹50 ▲ 3.9%", "₹55–65"),
            ("Beetroot (బీట్‌రూట్)", "Kg / Pcs", "₹38 ▼ 2.8%", "₹42–49"),
            ("Green Chilli (పచ్చిమిరప)", "Kg / Pcs", "₹48 ▲ 5.4%", "₹52–60"),
            ("Dry Red Chilli - Teja (ఎండిన మిరప)", "Quintal", "₹18,500 ▲ 8.2%", "₹190–220 /kg"),
            ("Watermelon (పుచ్చకాయ)", "Kg / Pcs", "₹14 ▼ 1.5%", "₹18–22"),
            ("Brinjal (వంకాయ)", "Kg / Pcs", "₹28 ▲ 2.1%", "₹32–38"),
            ("Okra / Bhendi (బెండకాయ)", "Kg / Pcs", "₹32 ▼ 0.8%", "₹36–42"),
            ("Banana (అరటి)", "Dozen", "₹35 ▲ 3.0%", "₹40–50"),
            ("Cotton Long Staple (ప్రత్తి)", "Quintal", "₹7,450 ▲ 1.8%", "₹7,600–7,900"),
            ("Paddy BPT 5204 (వరి)", "Quintal", "₹2,350 ▲ 2.5%", "₹2,450–2,600"),
        ]
        import pandas as pd
        st.dataframe(pd.DataFrame(prices, columns=["Vegetable / Crop Name", "Unit", "Mandi Price (vs. 7-day avg)", "Retail Price Range"]),
                     width="stretch", hide_index=True)
    elif market_state:
        pass
    else:
        st.caption("Select a state and press Submit to view available benchmark data.")

    st.markdown("### 💰 Calculate Your Field Harvest Revenue & Net Profit")
    yield_quintals = st.number_input("Crop Yield (Quintals / Bags)", min_value=0.0, value=10.0, step=1.0)
    selling_price = st.number_input("Market Selling Price (₹ per Quintal)", min_value=0.0, value=2350.0, step=50.0)
    farming_cost = st.number_input("Total Farming Cost (Fertilizer, Seed, Labor)", min_value=0.0, value=10000.0, step=500.0)
    revenue = yield_quintals * selling_price
    net_profit = revenue - farming_cost
    p1, p2, p3 = st.columns(3)
    p1.metric("Estimated Gross Revenue", f"₹{revenue:,.0f}")
    p2.metric("Total Farming Cost", f"₹{farming_cost:,.0f}")
    p3.metric("Estimated Net Profit", f"₹{net_profit:,.0f}", delta="Profit" if net_profit >= 0 else "Loss")
    st.caption("Estimate = yield × selling price − entered costs. This is a planning aid and excludes transport, commission, quality deductions, and other charges unless entered in farming costs.")

elif page == "⚙️ Settings":
    st.title("Settings")
    st.session_state["language_settings"] = st.session_state.get("header_language", "English")
    st.selectbox(
        "Language", ["English", TELUGU], key="language_settings",
        on_change=sync_settings_language,
    )
    st.caption("Your language choice is saved in the browser address and stays selected after refresh.")
