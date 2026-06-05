import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import datetime
import os
import json
import streamlit.components.v1 as components
import anthropic
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG & CONSTANTS ---
st.set_page_config(page_title="AFL Ladder Bet", layout="wide", page_icon="🏉")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Outfit', sans-serif;
    }
    .stApp {
        background-color: #070b10;
        color: #f8fafc;
    }
    
    /* Hide some default Streamlit elements for a cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Collapse ALL the default top chrome so there's no gap above the content.
       Streamlit reserves height for the header + decoration bar + toolbar. */
    header[data-testid="stHeader"] { display: none !important; height: 0 !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }

    /* The main content container carries a large default top padding (~6rem).
       Target every known testid/class across Streamlit versions. */
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stMainBlockContainer"],
    section.main > div.block-container,
    .block-container {
        padding-top: 0.4rem !important;
        padding-bottom: 2rem !important;
    }
    [data-testid="stAppViewContainer"] > .main { padding-top: 0 !important; }

    /* Premium Ladder Styles */
    .ladder-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 1rem 0;
    }
    .ladder-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 12px 20px;
        transition: transform 0.2s, background 0.2s, box-shadow 0.2s;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .ladder-row:hover {
        background: rgba(255, 255, 255, 0.06);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.4);
        border-color: rgba(56, 189, 248, 0.3);
    }
    .ladder-row.benchmark {
        border-left: 4px solid #facc15;
    }
    .ladder-row.human {
        border-left: 4px solid #38bdf8;
    }
    
    .ladder-left {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .ladder-rank {
        font-size: 1.6rem;
        font-weight: 800;
        color: #475569;
        width: 45px;
        text-align: right;
        white-space: nowrap;
    }
    .ladder-name {
        font-size: 1.3rem;
        font-weight: 600;
        color: #f8fafc;
    }
    .ladder-row.benchmark .ladder-name {
        color: #facc15; /* Yellow for benchmarks */
    }
    .ladder-row.human .ladder-name {
        color: #38bdf8; /* Blue for humans */
    }
    
    .ladder-right {
        text-align: right;
    }
    .ladder-score {
        font-size: 1.7rem;
        font-weight: 800;
        color: #f8fafc;
        text-shadow: 0 0 10px rgba(255,255,255,0.2);
    }
    .ladder-sub {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Top 3 Embellishments */
    .ladder-row[data-rank="1"] .ladder-rank { color: #fbbf24; }
    .ladder-row[data-rank="2"] .ladder-rank { color: #94a3b8; }
    .ladder-row[data-rank="3"] .ladder-rank { color: #b45309; }
    
    /* Modern Table Styles */
    .table-wrapper {
        border-radius: 12px;
        overflow-x: auto;
        overflow-y: hidden;
        border: 1px solid rgba(255,255,255,0.1);
        margin-top: 1rem;
        background: rgba(255, 255, 255, 0.02);
        -webkit-overflow-scrolling: touch;
    }
    .modern-table {
        width: 100%;
        border-collapse: collapse;
        min-width: 380px;
    }
    .modern-table th {
        background: rgba(255, 255, 255, 0.05);
        padding: 14px 20px;
        text-align: left;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 1px;
        border-bottom: 2px solid rgba(255,255,255,0.1);
    }
    .modern-table td {
        padding: 14px 20px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        color: #e2e8f0;
    }
    .modern-table tr:last-child td {
        border-bottom: none;
    }
    .modern-table tr:hover {
        background: rgba(255,255,255,0.04);
    }
    .tag-green { background: rgba(5,150,105,0.2); color: #34d399; border: 1px solid rgba(5,150,105,0.5); padding: 4px 0; border-radius: 8px; font-weight:700; display: inline-block; width: 42px; text-align: center;}
    .tag-yellow { background: rgba(217,119,6,0.2); color: #fbbf24; border: 1px solid rgba(217,119,6,0.5); padding: 4px 0; border-radius: 8px; font-weight:700; display: inline-block; width: 42px; text-align: center;}
    .tag-red { background: rgba(220,38,38,0.2); color: #f87171; border: 1px solid rgba(220,38,38,0.5); padding: 4px 0; border-radius: 8px; font-weight:700; display: inline-block; width: 42px; text-align: center;}
    
    .delta-text {
        font-size: 0.85rem;
        font-weight: 600;
        margin-left: 8px;
    }
    .delta-green { color: #34d399; }
    .delta-yellow { color: #fbbf24; }
    .delta-red { color: #f87171; }
    
    /* Primary button override */
    [data-testid="stButton"] button[kind="primary"] {
        background-color: #38bdf8 !important;
        border-color: #38bdf8 !important;
        color: #070b10 !important;
        font-weight: 700 !important;
    }

    /* ===== Context Strip ===== */
    .context-strip {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 16px;
        background: rgba(255,255,255,0.02);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        font-size: 0.85rem; margin-bottom: 0;
    }
    .cs-left { display: flex; align-items: center; gap: 14px; }
    .cs-app  { font-weight: 800; font-size: 0.88rem; letter-spacing: 1px; color: #f8fafc; }
    .cs-sep  { color: rgba(255,255,255,0.15); }
    .cs-round { color: #38bdf8; font-weight: 700; }
    .cs-leader { color: #94a3b8; }
    .cs-leader strong { color: #facc15; }
    .cs-right { font-size: 0.78rem; color: #64748b; }
    .live-dot {
        display: inline-block; width: 7px; height: 7px;
        background: #34d399; border-radius: 50%; margin-right: 5px;
        box-shadow: 0 0 6px #34d399;
        animation: pulse-dot 1.5s ease-in-out infinite;
    }
    @keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.4} }

    /* ===== Underline Nav (scoped via :has(#nav-marker)) ===== */
    [data-testid="stVerticalBlock"]:has(#nav-marker) [data-testid="stHorizontalBlock"] {
        border-bottom: 1px solid rgba(255,255,255,0.08);
        gap: 0 !important;
    }
    [data-testid="stVerticalBlock"]:has(#nav-marker) [data-testid="stButton"] button {
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0 !important;
        color: #64748b !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 14px 0 !important;
        width: 100% !important;
        box-shadow: none !important;
        margin-bottom: -1px !important;
        transition: color 0.15s, border-bottom-color 0.15s !important;
    }
    [data-testid="stVerticalBlock"]:has(#nav-marker) [data-testid="stButton"] button[kind="primary"] {
        color: #f8fafc !important;
        border-bottom-color: #38bdf8 !important;
        background: transparent !important;
        font-weight: 700 !important;
    }
    [data-testid="stVerticalBlock"]:has(#nav-marker) [data-testid="stButton"] button:hover {
        color: rgba(248,250,252,0.8) !important;
        background: transparent !important;
        border-bottom-color: rgba(56,189,248,0.4) !important;
    }

    /* ===== Compact Leaderboard (Issue 2) ===== */
    .lb-col-headers {
        display: grid;
        grid-template-columns: 28px 1fr 58px 84px 84px;
        padding: 0 12px 6px 12px; gap: 4px;
        border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 4px;
    }
    .lb-col-header {
        font-size: 0.62rem; font-weight: 800;
        text-transform: uppercase; letter-spacing: 1.5px; color: #334155;
    }
    .lb-col-header.right { text-align: right; }
    .compact-row {
        display: grid;
        grid-template-columns: 28px 1fr 58px 84px 84px;
        align-items: center; padding: 7px 12px;
        border-radius: 6px; border-left: 3px solid transparent;
        gap: 4px; transition: background 0.12s; margin-bottom: 1px;
    }
    .compact-row:hover { background: rgba(255,255,255,0.04); }
    .compact-row.human     { border-left-color: #38bdf8; }
    .compact-row.benchmark { border-left-color: #facc15; }
    .c-rank { font-size: 0.82rem; font-weight: 800; color: #334155; text-align: right; }
    .c-rank.gold   { color: #fbbf24; }
    .c-rank.silver { color: #94a3b8; }
    .c-rank.bronze { color: #b45309; }
    .c-name { font-size: 0.9rem; font-weight: 600; }
    .compact-row.human     .c-name { color: #38bdf8; }
    .compact-row.benchmark .c-name { color: #facc15; }
    .c-score { font-size: 1rem; font-weight: 800; color: #f8fafc; text-align: right; }
    .bubble {
        display: inline-flex; align-items: center; justify-content: center;
        padding: 2px 8px; border-radius: 20px;
        font-size: 0.72rem; font-weight: 700; white-space: nowrap; float: right;
    }
    .b-green { background: rgba(52,211,153,0.14); color: #34d399; border: 1px solid rgba(52,211,153,0.25); }
    .b-red   { background: rgba(248,113,113,0.14); color: #f87171; border: 1px solid rgba(248,113,113,0.25); }
    .b-gray  { background: rgba(255,255,255,0.05); color: #475569;  border: 1px solid rgba(255,255,255,0.08); }

    /* ===== Dashboard Cards (Issue 4) — each card IS a button ===== */
    #dash-cards-marker { display: none; }

    /* Style the three dashboard buttons to look like clickable cards */
    [data-testid="stVerticalBlock"]:has(> #dash-cards-marker) [data-testid="stButton"] > button {
        height: 100%;
        min-height: 150px;
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: flex-start !important;
        justify-content: flex-start;
        text-align: left;
        gap: 6px;
        padding: 20px 18px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: rgba(255,255,255,0.02) !important;
        white-space: normal !important;
        transition: border-color 0.15s, background 0.15s, transform 0.1s;
        box-shadow: none !important;
    }
    [data-testid="stVerticalBlock"]:has(> #dash-cards-marker) [data-testid="stButton"] > button:hover {
        border-color: rgba(56,189,248,0.45) !important;
        background: rgba(56,189,248,0.04) !important;
        transform: translateY(-2px);
    }
    /* Active (selected) card = primary button */
    [data-testid="stVerticalBlock"]:has(> #dash-cards-marker) [data-testid="stButton"] > button[kind="primary"] {
        border-color: #38bdf8 !important;
        background: rgba(56,189,248,0.08) !important;
    }
    /* Title line (first paragraph of the markdown label) */
    [data-testid="stVerticalBlock"]:has(> #dash-cards-marker) [data-testid="stButton"] > button p:first-child {
        font-size: 1rem !important; font-weight: 700 !important; color: #f8fafc !important;
        margin: 0 !important;
    }
    /* Description line (remaining paragraphs) */
    [data-testid="stVerticalBlock"]:has(> #dash-cards-marker) [data-testid="stButton"] > button p:not(:first-child) {
        font-size: 0.78rem !important; font-weight: 400 !important; color: #64748b !important;
        line-height: 1.5 !important; margin: 0 !important;
    }
    [data-testid="stVerticalBlock"]:has(> #dash-cards-marker) [data-testid="stButton"] > button[kind="primary"] p {
        color: #f8fafc !important;
    }
    [data-testid="stVerticalBlock"]:has(> #dash-cards-marker) [data-testid="stButton"] > button[kind="primary"] p:not(:first-child) {
        color: #bae6fd !important;
    }

    /* ===== Prediction Breakdown Callouts (Issue 5) ===== */
    .pb-metrics { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 12px; }
    .pb-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px; padding: 12px 14px;
    }
    .pb-card-label { font-size: 0.62rem; font-weight: 800; text-transform: uppercase;
                     letter-spacing: 1.5px; color: #334155; margin-bottom: 4px; }
    .pb-card-val { font-size: 1.05rem; font-weight: 800; }
    .pb-card-val.red   { color: #f87171; }
    .pb-card-val.green { color: #34d399; }
    .pb-card-val.sky   { color: #38bdf8; }
    .pb-card-sub { font-size: 0.7rem; color: #475569; margin-top: 3px; }
    .insight-strip {
        background: rgba(56,189,248,0.05); border: 1px solid rgba(56,189,248,0.14);
        border-radius: 10px; padding: 10px 14px;
        font-size: 0.83rem; color: #94a3b8; margin-bottom: 12px;
    }
    .insight-strip strong { color: #f8fafc; }
    tr.row-worst td { background: rgba(248,113,113,0.06) !important; }
    tr.row-worst td:first-child { border-left: 3px solid rgba(248,113,113,0.5); }
    tr.row-best  td { background: rgba(52,211,153,0.06) !important; }
    tr.row-best  td:first-child { border-left: 3px solid rgba(52,211,153,0.5); }

    /* ========================================================== */
    /* ===============   MOBILE / RESPONSIVE   ================== */
    /* ========================================================== */

    /* Tighten the side gutters on phones so content uses the full width */
    @media (max-width: 640px) {
        [data-testid="stAppViewBlockContainer"] {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-top: 0.4rem !important;
        }

        /* Context strip: let it wrap, shrink text, hide the "next game" line */
        .context-strip { flex-wrap: wrap; gap: 6px; padding: 9px 12px; font-size: 0.78rem; }
        .cs-left { flex-wrap: wrap; gap: 6px 10px; }
        .cs-app { font-size: 0.8rem; }
        .cs-right { display: none; }

        /* Nav buttons: smaller, tighter so 4 fit comfortably */
        [data-testid="stVerticalBlock"]:has(#nav-marker) [data-testid="stButton"] button {
            font-size: 0.72rem !important;
            padding: 11px 0 !important;
        }

        /* Leaderboard: drop the Pos column on very small screens, shrink the rest */
        .lb-col-headers, .compact-row {
            grid-template-columns: 24px 1fr 46px 70px;
        }
        .lb-col-headers .lb-col-header:last-child,
        .compact-row > div:last-child { display: none; }
        .c-name { font-size: 0.84rem; }
        .bubble { font-size: 0.66rem; padding: 2px 6px; }

        /* Dashboard cards: shorter on mobile when stacked */
        [data-testid="stVerticalBlock"]:has(> #dash-cards-marker) [data-testid="stButton"] > button {
            min-height: 0;
            padding: 14px 14px !important;
        }

        /* Prediction breakdown callouts: stack into one column */
        .pb-metrics { grid-template-columns: 1fr; gap: 8px; }

        /* Make headings a touch smaller */
        h1, h2 { font-size: 1.3rem !important; }
    }

    /* Tablet tweaks */
    @media (min-width: 641px) and (max-width: 1024px) {
        .pb-metrics { grid-template-columns: 1fr 1fr; }
        .cs-right { font-size: 0.72rem; }
    }
</style>
""", unsafe_allow_html=True)

TEAM_STYLES = {
    "Adelaide": {"bg": "#002b5c", "text": "#ffd200", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Adelaide.png"},
    "Brisbane Lions": {"bg": "#6e0e2d", "text": "#f3ba1c", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Brisbane.png"},
    "Carlton": {"bg": "#031a29", "text": "#ffffff", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Carlton.png"},
    "Collingwood": {"bg": "#000000", "text": "#ffffff", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Collingwood.png"},
    "Essendon": {"bg": "#000000", "text": "#cc2031", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Essendon.png"},
    "Fremantle": {"bg": "#2a1a54", "text": "#ffffff", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Fremantle.png"},
    "Geelong": {"bg": "#1c3c63", "text": "#ffffff", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Geelong.png"},
    "Gold Coast SUNS": {"bg": "#d71920", "text": "#facc15", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/GoldCoast.png"},
    "GWS GIANTS": {"bg": "#f47920", "text": "#ffffff", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Giants.png"},
    "Hawthorn": {"bg": "#4d2004", "text": "#facc15", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Hawthorn.png"},
    "Melbourne": {"bg": "#0f112e", "text": "#cc2031", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Melbourne.png"},
    "North Melbourne": {"bg": "#013b6e", "text": "#ffffff", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/NorthMelbourne.png"},
    "Port Adelaide": {"bg": "#000000", "text": "#008a97", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/PortAdelaide.png"},
    "Richmond": {"bg": "#000000", "text": "#ffd200", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Richmond.png"},
    "St Kilda": {"bg": "#000000", "text": "#ffffff", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/StKilda.png"},
    "Sydney Swans": {"bg": "#ed171f", "text": "#ffffff", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Sydney.png"},
    "West Coast Eagles": {"bg": "#002b5c", "text": "#facc15", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/WestCoast.png"},
    "Western Bulldogs": {"bg": "#014896", "text": "#ffffff", "logo": "https://squiggle.com.au/wp-content/themes/squiggle/assets/images/Bulldogs.png"}
}

PREDICTIONS = {
    "Antony": ["Geelong", "Brisbane Lions", "Hawthorn", "Sydney Swans", "Western Bulldogs", "Adelaide", "Gold Coast SUNS", "Fremantle", "Collingwood", "GWS GIANTS", "St Kilda", "Melbourne", "Carlton", "Port Adelaide", "North Melbourne", "Essendon", "Richmond", "West Coast Eagles"],
    "Slammy": ["Brisbane Lions", "Western Bulldogs", "Gold Coast SUNS", "Collingwood", "Adelaide", "Geelong", "Sydney Swans", "Fremantle", "St Kilda", "GWS GIANTS", "Hawthorn", "Melbourne", "Port Adelaide", "North Melbourne", "Carlton", "Richmond", "Essendon", "West Coast Eagles"],
    "Aidos": ["Brisbane Lions", "Geelong", "Gold Coast SUNS", "Western Bulldogs", "Sydney Swans", "Hawthorn", "Adelaide", "Fremantle", "Collingwood", "St Kilda", "GWS GIANTS", "Port Adelaide", "Carlton", "Essendon", "Melbourne", "North Melbourne", "Richmond", "West Coast Eagles"],
    "Coz": ["Gold Coast SUNS", "Sydney Swans", "Brisbane Lions", "Geelong", "Western Bulldogs", "Fremantle", "Adelaide", "GWS GIANTS", "Hawthorn", "St Kilda", "Essendon", "Port Adelaide", "Collingwood", "Carlton", "North Melbourne", "Melbourne", "Richmond", "West Coast Eagles"],
    "Fry": ["Sydney Swans", "Brisbane Lions", "Geelong", "Hawthorn", "Collingwood", "Gold Coast SUNS", "Adelaide", "GWS GIANTS", "Western Bulldogs", "Fremantle", "Port Adelaide", "St Kilda", "Melbourne", "Essendon", "Richmond", "Carlton", "North Melbourne", "West Coast Eagles"],
    "Prince": ["Brisbane Lions", "Geelong", "Western Bulldogs", "Hawthorn", "Collingwood", "GWS GIANTS", "Adelaide", "Gold Coast SUNS", "Fremantle", "Sydney Swans", "Melbourne", "Carlton", "Port Adelaide", "St Kilda", "North Melbourne", "Richmond", "Essendon", "West Coast Eagles"],
    "Last Year H+A": ["Adelaide", "Geelong", "Brisbane Lions", "Collingwood", "GWS GIANTS", "Fremantle", "Gold Coast SUNS", "Hawthorn", "Western Bulldogs", "Sydney Swans", "Carlton", "St Kilda", "Port Adelaide", "Melbourne", "Essendon", "North Melbourne", "Richmond", "West Coast Eagles"],
    "Last Year Finals": ["Brisbane Lions", "Geelong", "Collingwood", "Hawthorn", "Adelaide", "Gold Coast SUNS", "GWS GIANTS", "Fremantle", "Western Bulldogs", "Sydney Swans", "Carlton", "St Kilda", "Port Adelaide", "Melbourne", "Essendon", "North Melbourne", "Richmond", "West Coast Eagles"],
    "Cromputer": ["Brisbane Lions", "Western Bulldogs", "Hawthorn", "Geelong", "Adelaide", "Gold Coast SUNS", "Fremantle", "Sydney Swans", "Collingwood", "GWS GIANTS", "St Kilda", "Carlton", "Port Adelaide", "Melbourne", "Essendon", "North Melbourne", "Richmond", "West Coast Eagles"]
}

# Automatically add Benchmark
PREDICTIONS["Alphabetical"] = sorted(PREDICTIONS["Antony"])

HUMANS = ["Antony", "Slammy", "Aidos", "Coz", "Fry", "Prince"]
BENCHMARKS = ["Last Year H+A", "Last Year Finals", "Alphabetical", "Cromputer"]
ALL_ENTITIES = HUMANS + BENCHMARKS

# Fall back to 2026 as per our environment defaults if needed, but best is to dynamically retrieve
YEAR = datetime.datetime.now().year

# --- API HELPERS ---
HEADERS = {"User-Agent": "AFL_Dashboard_App/1.0"}
LOCAL_HISTORY_PATH = os.path.join(os.path.dirname(__file__), "ladder_history.json")

@st.cache_data(ttl=3600)
def fetch_games_for_year(year=YEAR):
    url = f"https://api.squiggle.com.au/?q=games&year={year}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get('games', [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=3600)
def fetch_live_ladder():
    """Fetch current standings with automatic year fallback.
    Returns (standings, year_used) so callers can surface a warning
    when the data is from a prior season rather than the current one.
    """
    current_year = datetime.datetime.now().year
    for year in [current_year, current_year - 1, current_year - 2, 2024]:
        url = f"https://api.squiggle.com.au/?q=standings&year={year}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json().get('standings', [])
                if data:
                    return sorted(data, key=lambda x: x['rank']), year
        except Exception:
            pass
    return [], None

@st.cache_data(ttl=3600)
def _fetch_ladder_from_api(year, round_num):
    """Raw Squiggle API fetch for one historical round (Streamlit-cached)."""
    url = f"https://api.squiggle.com.au/?q=standings&year={year}&round={round_num}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json().get('standings', [])
            return sorted(data, key=lambda x: x['rank'])
    except Exception:
        pass
    return []

# --- LOCAL HISTORY HELPERS ---

def load_local_history():
    """Load the persisted round-by-round ladder history from disk."""
    if os.path.exists(LOCAL_HISTORY_PATH):
        try:
            with open(LOCAL_HISTORY_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_local_history(history):
    """Write the ladder history dict back to disk."""
    try:
        with open(LOCAL_HISTORY_PATH, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass

def sync_local_history(year, completed_rounds):
    """
    On session start, check which completed rounds are missing from the local
    JSON cache and fetch them from the Squiggle API. Returns the full history dict.
    Historical ladder data never changes once a round is complete, so we only
    ever need to fetch each round once.
    """
    local_history = load_local_history()
    year_key = str(year)
    if year_key not in local_history:
        local_history[year_key] = {}

    missing = [r for r in completed_rounds if str(r) not in local_history[year_key]]
    if missing:
        for rd in missing:
            data = _fetch_ladder_from_api(year, rd)
            if data:
                local_history[year_key][str(rd)] = data
        save_local_history(local_history)
        st.toast(f"💾 Cached {len(missing)} new round(s) to local history.", icon="✅")

    return local_history

def fetch_historical_ladder(year, round_num):
    """
    Return a completed round's ladder standings.
    Reads from the local JSON cache (instant) when available;
    falls back to the Squiggle API for any round not yet cached.
    """
    local_history = st.session_state.get('local_history', {})
    year_key  = str(year)
    round_key = str(round_num)
    if year_key in local_history and round_key in local_history[year_key]:
        return local_history[year_key][round_key]
    return _fetch_ladder_from_api(year, round_num)

def _get_api_key():
    """Read the Anthropic key from env (local .env) or Streamlit Cloud secrets."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        try:
            key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            key = None
    return key

def generate_ai_summary(current_ladder, previous_ladder, games, scores_df):
    """Generates an AI summary of the season using Claude (claude-haiku-4-5)."""
    api_key = _get_api_key()
    if not api_key:
        return "⚠️ **AI Insights Unavailable**: Please set `ANTHROPIC_API_KEY` in your environment to enable dynamic season summaries."

    # Build context
    ladder_context = f"Current Ladder Order: {', '.join(current_ladder)}\n"
    if previous_ladder:
        ladder_context += f"Previous Week Ladder: {', '.join(previous_ladder)}\n"

    recent_games = [g for g in games if g.get('complete') == 100][-9:]
    games_context = "Recent Results:\n"
    for g in recent_games:
        games_context += f"- {g['hteam']} {g['hscore']} vs {g['ateam']} {g['ascore']}\n"

    upcoming_games = [g for g in games if g.get('complete') != 100][:9]
    upcoming_context = "Upcoming Impactful Games:\n"
    for g in upcoming_games:
        upcoming_context += f"- {g['hteam']} vs {g['ateam']}\n"

    scores_context = "Competitor Damage (Lower is better):\n"
    for _, row in scores_df.iterrows():
        scores_context += f"- {row['Entity']}: {row['Score']} points\n"

    prompt = f"""You are an expert AFL analyst and data scientist for a "Ladder Betting" competition.
In this competition, participants predict the final ladder. Their "Damage" is the sum of differences between their predicted rank and the actual current rank for every team. Lower damage is better.

Please provide a concise, premium AI summary covering:
1. **Ladder Movements**: Key changes in the AFL ladder since last week.
2. **Impactful Results**: Which specific game results most disrupted the ladder?
3. **Damage Insights**: Review the competitor scores. Who is leading, and why? What specific team predictions are driving the damage for the trailing players?
4. **The Road Ahead**: Which upcoming games in the next round will have the biggest impact on the leaderboard?

Format your response in beautiful Markdown with emojis. Keep it professional but engaging.

DATA CONTEXT:
{ladder_context}
{games_context}
{scores_context}
{upcoming_context}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"❌ **AI Error**: Failed to generate summary. ({str(e)})"

def get_poster_html(df_target, df_history, round_name):
    # Convert dataframes to JSON for use in Javascript
    leaderboard_data = df_target.head(10).to_json(orient="records")
    
    # Filter and prepare history data for both graphs
    df_humans = df_history[df_history["Type"] == "Human"]
    history_humans_json = df_humans.to_json(orient="records")
    history_all_json = df_history.to_json(orient="records")

    # Build a compact leaderboard HTML for the static part
    lb_rows = ""
    for idx, row in df_target.head(10).iterrows():
        rank = idx + 1
        name = row['Entity']
        score = int(row['Score'])
        dmg_delta = int(row.get('dmg_delta', 0))
        rank_delta = int(row.get('rank_delta', 0))
        
        color = "#38bdf8" if row['Type'] == "Human" else "#facc15"
        rank_icon = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
        
        # Arrow language matching the in-app leaderboard: ↓ = improved (good), ↑ = worse
        dmg_color = "#34d399" if dmg_delta < 0 else ("#64748b" if dmg_delta == 0 else "#f87171")
        if dmg_delta < 0:   dmg_txt = f"↓{abs(dmg_delta)}"
        elif dmg_delta > 0: dmg_txt = f"↑{dmg_delta}"
        else:               dmg_txt = "—"

        rank_color = "#34d399" if rank_delta > 0 else ("#64748b" if rank_delta == 0 else "#f87171")
        if rank_delta > 0:   rank_txt = f"↑{rank_delta}"
        elif rank_delta < 0: rank_txt = f"↓{abs(rank_delta)}"
        else:                rank_txt = "—"

        lb_rows += f"""
        <div style="display: grid; grid-template-columns: 30px 140px 60px 70px 70px; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
            <span style="font-weight: 800; color: #475569;">{rank_icon}</span>
            <span style="font-weight: 600; color: {color}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{name}</span>
            <span style="font-weight: 800; font-size: 1.1rem; text-align: right;">{score}</span>
            <span style="font-weight: 700; font-size: 0.85rem; text-align: right; color: {dmg_color};">{dmg_txt}</span>
            <span style="font-weight: 700; font-size: 0.85rem; text-align: right; color: {rank_color};">{rank_txt}</span>
        </div>
        """

    date_str = datetime.datetime.now().strftime("%d %b %Y")
    
    html = f"""
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        body {{ margin: 0; padding: 20px; background: #070b10; font-family: 'Outfit', sans-serif; }}
        #poster {{
            width: 1000px;
            padding: 50px;
            background: linear-gradient(135deg, #070b10 0%, #0f172a 100%);
            color: white;
            border-radius: 40px;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            position: relative;
            overflow: hidden;
        }}
        .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 50px; position: relative; }}
        .title-group h1 {{ margin: 0; font-size: 52px; font-weight: 800; letter-spacing: -1px; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .round-badge {{ background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); padding: 10px 20px; border-radius: 16px; color: #38bdf8; font-weight: 700; font-size: 18px; }}
        
        .main-grid {{ display: grid; grid-template-columns: 420px 1fr; gap: 40px; margin-bottom: 40px; }}
        .card {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 28px; padding: 32px; }}
        .card-title {{ margin: 0 0 20px 0; color: #38bdf8; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; }}
        
        .footer {{ text-align: center; color: #475569; font-size: 14px; margin-top: 40px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 30px; }}
        
        .btn-container {{ margin-bottom: 20px; display: flex; gap: 10px; }}
        .download-btn {{
            background: #38bdf8;
            color: #070b10;
            border: none;
            padding: 12px 24px;
            border-radius: 12px;
            font-weight: 700;
            cursor: pointer;
            font-family: 'Outfit', sans-serif;
            transition: all 0.2s;
        }}
        .download-btn:hover {{ background: #7dd3fc; transform: translateY(-1px); }}
        
        .lb-header {{
            display: grid;
            grid-template-columns: 30px 140px 60px 70px 70px;
            padding-bottom: 12px;
            border-bottom: 2px solid rgba(255,255,255,0.1);
            color: #94a3b8;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
    </style>

    <div class="btn-container">
        <button class="download-btn" onclick="downloadPoster()">⬇️ Download High-Res .JPG</button>
        <span style="color: #94a3b8; font-size: 14px; align-self: center;">Generating at 4x scale for maximum clarity.</span>
    </div>

    <div id="poster">
        <div class="header">
            <div class="title-group">
                <h1>AFL LADDER BET</h1>
            </div>
            <div class="round-badge">{round_name.upper()}</div>
        </div>
        
        <div class="main-grid">
            <div class="card">
                <h3 class="card-title">Top 10 Leaderboard</h3>
                <div class="lb-header">
                    <span>#</span>
                    <span>Name</span>
                    <span style="text-align: right;">Pts</span>
                    <span style="text-align: right;">Pts Δ</span>
                    <span style="text-align: right;">Pos Δ</span>
                </div>
                {lb_rows}
            </div>
            <div class="card" style="display: flex; flex-direction: column; justify-content: center; padding: 20px;">
                <h3 class="card-title" style="margin-left: 14px;">Competitor Progression</h3>
                <div id="graph1" style="width: 100%; height: 400px;"></div>
            </div>
        </div>
        
        <div class="card" style="padding: 20px;">
            <h3 class="card-title" style="margin: 14px;">Full Field Performance</h3>
            <div id="graph2" style="width: 100%; height: 400px;"></div>
        </div>

        <div class="footer">
            Generated on {date_str} • Good luck for the rest of the season! 🏉
        </div>
    </div>

    <script>
    const historyHumans = {history_humans_json};
    const historyAll = {history_all_json};

    function createGraph(id, data, title) {{
        const entities = [...new Set(data.map(d => d.Entity))];
        const traces = entities.map(entity => {{
            const entityData = data.filter(d => d.Entity === entity);
            return {{
                x: entityData.map(d => d.Round),
                y: entityData.map(d => d.Score),
                name: entity,
                mode: 'lines+markers',
                line: {{ shape: 'spline', width: 3 }},
                marker: {{ size: 8 }}
            }};
        }});

        const layout = {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            margin: {{ l: 50, r: 30, t: 20, b: 50 }},
            font: {{ family: 'Outfit', color: '#94a3b8', size: 12 }},
            xaxis: {{ showgrid: false, zeroline: false, title: {{ text: 'Round', font: {{ size: 11, color: '#475569' }} }} }},
            yaxis: {{ autorange: 'reversed', showgrid: false, zeroline: false, title: {{ text: 'Damage (lower = better)', font: {{ size: 11, color: '#475569' }} }} }},
            showlegend: true,
            legend: {{ orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center', font: {{ size: 11 }} }}
        }};

        Plotly.newPlot(id, traces, layout, {{ staticPlot: true, responsive: true }});
    }}

    // Initial render
    window.onload = () => {{
        createGraph('graph1', historyHumans, 'Competitors Only');
        createGraph('graph2', historyAll, 'Full Field');
    }};

    async function downloadPoster() {{
        const poster = document.getElementById('poster');
        
        // Use html2canvas to capture the element at high scale
        html2canvas(poster, {{
            scale: 4,
            backgroundColor: '#070b10',
            logging: false,
            useCORS: true,
            allowTaint: true,
            imageTimeout: 0
        }}).then(canvas => {{
            const link = document.createElement('a');
            link.download = 'AFL-Ladder-Bet-HighRes-{round_name.replace(" ", "-")}.jpg';
            link.href = canvas.toDataURL('image/jpeg', 0.95);
            link.click();
        }});
    }}
    </script>
    """
    return html

def get_breakdown_poster_html(actual_ladder, round_name):
    """
    Generate the team-by-team damage breakdown poster.
    Rows = rank positions 1-18.
    Columns = Actual team at that rank, then for each competitor:
              (team they placed at that rank | coloured damage number).
    """
    date_str  = datetime.datetime.now().strftime("%d %b %Y")
    safe_round = round_name.replace(" ", "-")

    # --- Pre-compute totals ---
    total_scores = {}
    for entity in ALL_ENTITIES:
        score, _ = calculate_score(PREDICTIONS[entity], actual_ladder)
        total_scores[entity] = score

    # --- Helpers ---
    def short_name(name):
        return (name
            .replace("Brisbane Lions",   "Brisbane")
            .replace("Gold Coast SUNS",  "Gold Coast")
            .replace("GWS GIANTS",       "GWS")
            .replace("West Coast Eagles","West Coast")
            .replace("Western Bulldogs", "W. Bulldogs")
            .replace("North Melbourne",  "N. Melbourne")
            .replace("Port Adelaide",    "Port Adl.")
            .replace("Sydney Swans",     "Sydney")
        )

    def short_entity(name):
        return (name
            .replace("Last Year H+A",    "LY H+A")
            .replace("Last Year Finals", "LY Finals")
        )

    def dmg_class(dmg):
        if dmg <= -1: return "dmg-perfect"
        if dmg <=  2: return "dmg-good"
        if dmg <=  5: return "dmg-ok"
        if dmg <=  8: return "dmg-bad"
        return "dmg-worst"

    # --- Header row ---
    header_html = '<th class="actual-header">Actual</th>'
    for entity in ALL_ENTITIES:
        score = total_scores[entity]
        color = "#38bdf8" if entity in HUMANS else "#facc15"
        header_html += (
            f'<th colspan="2" class="comp-header" style="color:{color};">'
            f'{short_entity(entity)}<br>'
            f'<span style="color:#f8fafc;font-size:1rem;font-weight:800;">{score}</span>'
            f'</th>'
        )

    # --- Data rows (one per rank position) ---
    rows_html = ""
    for r in range(18):
        actual_team = actual_ladder[r] if r < len(actual_ladder) else "?"
        row_bg = "rgba(255,255,255,0.025)" if r % 2 == 0 else "transparent"

        row_html  = f'<tr style="background:{row_bg};">'
        row_html += (
            f'<td class="actual-cell">'
            f'<span class="rank-badge">{r+1}</span>'
            f'{short_name(actual_team)}</td>'
        )

        for entity in ALL_ENTITIES:
            pred_team = PREDICTIONS[entity][r]
            try:
                actual_rank = actual_ladder.index(pred_team) + 1
                dmg = abs((r + 1) - actual_rank)
                if dmg == 0:
                    dmg = -1
            except ValueError:
                dmg = 0

            cls = dmg_class(dmg)
            row_html += f'<td class="team-cell">{short_name(pred_team)}</td>'
            row_html += f'<td class="dmg-cell {cls}">{dmg}</td>'

        row_html  += '</tr>'
        rows_html += row_html

    html = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        body {{ margin:0; padding:20px; background:#070b10; font-family:'Outfit',sans-serif; }}

        #bd-poster {{
            width: 1520px;
            padding: 40px;
            background: linear-gradient(135deg,#070b10 0%,#0f172a 100%);
            color: white;
            border-radius: 32px;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
        }}
        .poster-header {{
            display:flex; justify-content:space-between; align-items:center;
            margin-bottom:28px;
        }}
        .poster-title {{
            font-size:30px; font-weight:800;
            background:linear-gradient(90deg,#38bdf8,#818cf8);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        }}
        .round-badge {{
            background:rgba(56,189,248,0.1); border:1px solid rgba(56,189,248,0.3);
            padding:8px 16px; border-radius:12px; color:#38bdf8; font-weight:700;
        }}

        .bd-table {{ width:100%; border-collapse:collapse; font-size:0.76rem; }}

        .actual-header {{
            text-align:left; color:#94a3b8; font-size:0.68rem;
            text-transform:uppercase; letter-spacing:1px;
            padding:10px 14px; border-bottom:2px solid rgba(255,255,255,0.12);
        }}
        .comp-header {{
            text-align:center; font-size:0.72rem; font-weight:800;
            padding:8px 4px; border-bottom:2px solid rgba(255,255,255,0.12);
            border-left:1px solid rgba(255,255,255,0.06);
        }}
        .actual-cell {{
            color:#e2e8f0; font-weight:600; padding:5px 14px 5px 10px;
            white-space:nowrap; border-right:1px solid rgba(255,255,255,0.07);
        }}
        .rank-badge {{
            display:inline-block; width:22px; color:#475569;
            font-weight:800; font-size:0.68rem; margin-right:6px;
        }}
        .team-cell {{
            color:#94a3b8; padding:5px 4px 5px 8px;
            white-space:nowrap; font-size:0.73rem;
        }}
        .dmg-cell {{
            text-align:center; font-weight:800; padding:5px 6px;
            font-size:0.8rem; min-width:26px;
            border-right:1px solid rgba(255,255,255,0.06);
        }}
        .dmg-perfect {{ background:rgba(5,150,105,0.45);  color:#34d399; }}
        .dmg-good    {{ background:rgba(5,150,105,0.18);  color:#86efac; }}
        .dmg-ok      {{ background:rgba(234,179,8,0.22);  color:#fbbf24; }}
        .dmg-bad     {{ background:rgba(239,68,68,0.28);  color:#f87171; }}
        .dmg-worst   {{ background:rgba(185,28,28,0.55);  color:#fca5a5; font-weight:900; }}

        .poster-footer {{
            text-align:center; color:#475569; font-size:13px;
            margin-top:24px; border-top:1px solid rgba(255,255,255,0.05);
            padding-top:18px;
        }}
        .btn-bar {{ margin-bottom:20px; display:flex; align-items:center; gap:14px; }}
        .dl-btn {{
            background:#38bdf8; color:#070b10; border:none;
            padding:12px 24px; border-radius:12px; font-weight:700;
            cursor:pointer; font-family:'Outfit',sans-serif;
        }}
        .dl-btn:hover {{ background:#7dd3fc; }}
        .btn-hint {{ color:#94a3b8; font-size:14px; }}
    </style>

    <div class="btn-bar">
        <button class="dl-btn" onclick="downloadBD()">⬇️ Download Breakdown .JPG</button>
        <span class="btn-hint">Generated at 4× scale for maximum clarity.</span>
    </div>

    <div id="bd-poster">
        <div class="poster-header">
            <div class="poster-title">TEAM-BY-TEAM DAMAGE BREAKDOWN</div>
            <div class="round-badge">{round_name.upper()}</div>
        </div>
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;font-size:0.72rem;color:#94a3b8;flex-wrap:wrap;">
            <span style="font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#475569;">Damage per pick:</span>
            <span class="dmg-perfect" style="padding:3px 10px;border-radius:6px;font-weight:800;">-1 Perfect</span>
            <span class="dmg-good"    style="padding:3px 10px;border-radius:6px;font-weight:800;">0–2 Good</span>
            <span class="dmg-ok"      style="padding:3px 10px;border-radius:6px;font-weight:800;">3–5 OK</span>
            <span class="dmg-bad"     style="padding:3px 10px;border-radius:6px;font-weight:800;">6–8 Bad</span>
            <span class="dmg-worst"   style="padding:3px 10px;border-radius:6px;font-weight:800;">9+ Worst</span>
        </div>
        <table class="bd-table">
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        <div class="poster-footer">Generated {date_str} &nbsp;•&nbsp; AFL Ladder Predictor Challenge 🏉</div>
    </div>

    <script>
    function downloadBD() {{
        html2canvas(document.getElementById('bd-poster'), {{
            scale: 4,
            backgroundColor: '#070b10',
            logging: false,
            useCORS: true,
            allowTaint: true,
            imageTimeout: 0
        }}).then(canvas => {{
            const a = document.createElement('a');
            a.download = 'AFL-Damage-Breakdown-{safe_round}.jpg';
            a.href = canvas.toDataURL('image/jpeg', 0.95);
            a.click();
        }});
    }}
    </script>
    """
    return html


def get_competitor_breakdown_poster_html(actual_ladder, round_name):
    """
    Generate the competitor-focused damage breakdown poster.
    Rows  = actual teams at their actual rank (rank 1–18).
    Columns = each competitor.
    Cells = predicted rank | damage that team contributes to each competitor.
    """
    date_str  = datetime.datetime.now().strftime("%d %b %Y")
    safe_round = round_name.replace(" ", "-")

    # --- Pre-compute totals ---
    total_scores = {}
    for entity in ALL_ENTITIES:
        score, _ = calculate_score(PREDICTIONS[entity], actual_ladder)
        total_scores[entity] = score

    # --- Helpers (shared with team breakdown) ---
    def short_name(name):
        return (name
            .replace("Brisbane Lions",   "Brisbane")
            .replace("Gold Coast SUNS",  "Gold Coast")
            .replace("GWS GIANTS",       "GWS")
            .replace("West Coast Eagles","West Coast")
            .replace("Western Bulldogs", "W. Bulldogs")
            .replace("North Melbourne",  "N. Melbourne")
            .replace("Port Adelaide",    "Port Adl.")
            .replace("Sydney Swans",     "Sydney")
        )

    def short_entity(name):
        return (name
            .replace("Last Year H+A",    "LY H+A")
            .replace("Last Year Finals", "LY Finals")
        )

    def dmg_class(dmg):
        if dmg <= -1: return "dmg-perfect"
        if dmg <=  2: return "dmg-good"
        if dmg <=  5: return "dmg-ok"
        if dmg <=  8: return "dmg-bad"
        return "dmg-worst"

    # --- Header row ---
    header_html = '<th class="actual-header">Actual Team</th>'
    for entity in ALL_ENTITIES:
        score = total_scores[entity]
        color = "#38bdf8" if entity in HUMANS else "#facc15"
        header_html += (
            f'<th colspan="2" class="comp-header" style="color:{color};">'
            f'{short_entity(entity)}<br>'
            f'<span style="color:#f8fafc;font-size:1rem;font-weight:800;">{score}</span>'
            f'</th>'
        )

    # --- Data rows: one per actual rank position ---
    rows_html = ""
    for r in range(len(actual_ladder)):
        actual_team = actual_ladder[r]
        actual_rank = r + 1
        row_bg = "rgba(255,255,255,0.025)" if r % 2 == 0 else "transparent"

        row_html  = f'<tr style="background:{row_bg};">'
        row_html += (
            f'<td class="actual-cell">'
            f'<span class="rank-badge">{actual_rank}</span>'
            f'{short_name(actual_team)}</td>'
        )

        for entity in ALL_ENTITIES:
            try:
                pred_rank = PREDICTIONS[entity].index(actual_team) + 1
                dmg = abs(pred_rank - actual_rank)
                if dmg == 0:
                    dmg = -1   # perfect prediction
            except ValueError:
                pred_rank = "?"
                dmg = 0

            cls = dmg_class(dmg)
            row_html += f'<td class="team-cell">#{pred_rank}</td>'
            row_html += f'<td class="dmg-cell {cls}">{dmg}</td>'

        row_html  += '</tr>'
        rows_html += row_html

    html = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        body {{ margin:0; padding:20px; background:#070b10; font-family:'Outfit',sans-serif; }}

        #cb-poster {{
            width: 1520px;
            padding: 40px;
            background: linear-gradient(135deg,#070b10 0%,#0f172a 100%);
            color: white;
            border-radius: 32px;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
        }}
        .poster-header {{
            display:flex; justify-content:space-between; align-items:center;
            margin-bottom:28px;
        }}
        .poster-title {{
            font-size:30px; font-weight:800;
            background:linear-gradient(90deg,#38bdf8,#818cf8);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        }}
        .round-badge {{
            background:rgba(56,189,248,0.1); border:1px solid rgba(56,189,248,0.3);
            padding:8px 16px; border-radius:12px; color:#38bdf8; font-weight:700;
        }}

        .bd-table {{ width:100%; border-collapse:collapse; font-size:0.76rem; }}

        .actual-header {{
            text-align:left; color:#94a3b8; font-size:0.68rem;
            text-transform:uppercase; letter-spacing:1px;
            padding:10px 14px; border-bottom:2px solid rgba(255,255,255,0.12);
        }}
        .comp-header {{
            text-align:center; font-size:0.72rem; font-weight:800;
            padding:8px 4px; border-bottom:2px solid rgba(255,255,255,0.12);
            border-left:1px solid rgba(255,255,255,0.06);
        }}
        .actual-cell {{
            color:#e2e8f0; font-weight:600; padding:5px 14px 5px 10px;
            white-space:nowrap; border-right:1px solid rgba(255,255,255,0.07);
        }}
        .rank-badge {{
            display:inline-block; width:22px; color:#475569;
            font-weight:800; font-size:0.68rem; margin-right:6px;
        }}
        .team-cell {{
            color:#64748b; padding:5px 4px 5px 8px;
            white-space:nowrap; font-size:0.72rem; font-weight:600;
            text-align:center;
        }}
        .dmg-cell {{
            text-align:center; font-weight:800; padding:5px 6px;
            font-size:0.8rem; min-width:26px;
            border-right:1px solid rgba(255,255,255,0.06);
        }}
        .dmg-perfect {{ background:rgba(5,150,105,0.45);  color:#34d399; }}
        .dmg-good    {{ background:rgba(5,150,105,0.18);  color:#86efac; }}
        .dmg-ok      {{ background:rgba(234,179,8,0.22);  color:#fbbf24; }}
        .dmg-bad     {{ background:rgba(239,68,68,0.28);  color:#f87171; }}
        .dmg-worst   {{ background:rgba(185,28,28,0.55);  color:#fca5a5; font-weight:900; }}

        .poster-footer {{
            text-align:center; color:#475569; font-size:13px;
            margin-top:24px; border-top:1px solid rgba(255,255,255,0.05);
            padding-top:18px;
        }}
        .btn-bar {{ margin-bottom:20px; display:flex; align-items:center; gap:14px; }}
        .dl-btn {{
            background:#38bdf8; color:#070b10; border:none;
            padding:12px 24px; border-radius:12px; font-weight:700;
            cursor:pointer; font-family:'Outfit',sans-serif;
        }}
        .dl-btn:hover {{ background:#7dd3fc; }}
        .btn-hint {{ color:#94a3b8; font-size:14px; }}
    </style>

    <div class="btn-bar">
        <button class="dl-btn" onclick="downloadCB()">&#x2B07;&#xFE0F; Download Breakdown .JPG</button>
        <span class="btn-hint">Generated at 4&#xD7; scale for maximum clarity. Columns: predicted rank &#x2502; damage.</span>
    </div>

    <div id="cb-poster">
        <div class="poster-header">
            <div class="poster-title">DAMAGE BREAKDOWN BY COMPETITOR</div>
            <div class="round-badge">{round_name.upper()}</div>
        </div>
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;font-size:0.72rem;color:#94a3b8;flex-wrap:wrap;">
            <span style="font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#475569;">Damage this team adds:</span>
            <span class="dmg-perfect" style="padding:3px 10px;border-radius:6px;font-weight:800;">-1 Perfect</span>
            <span class="dmg-good"    style="padding:3px 10px;border-radius:6px;font-weight:800;">0–2 Good</span>
            <span class="dmg-ok"      style="padding:3px 10px;border-radius:6px;font-weight:800;">3–5 OK</span>
            <span class="dmg-bad"     style="padding:3px 10px;border-radius:6px;font-weight:800;">6–8 Bad</span>
            <span class="dmg-worst"   style="padding:3px 10px;border-radius:6px;font-weight:800;">9+ Worst</span>
        </div>
        <table class="bd-table">
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        <div class="poster-footer">Generated {date_str} &nbsp;•&nbsp; AFL Ladder Predictor Challenge &#x1F3C9;</div>
    </div>

    <script>
    function downloadCB() {{
        html2canvas(document.getElementById('cb-poster'), {{
            scale: 4,
            backgroundColor: '#070b10',
            logging: false,
            useCORS: true,
            allowTaint: true,
            imageTimeout: 0
        }}).then(canvas => {{
            const a = document.createElement('a');
            a.download = 'AFL-Competitor-Breakdown-{safe_round}.jpg';
            a.href = canvas.toDataURL('image/jpeg', 0.95);
            a.click();
        }});
    }}
    </script>
    """
    return html


# --- DATA PROCESSING ---
def get_completed_rounds(games):
    completed = [g['round'] for g in games if g.get('complete', 0) == 100]
    if not completed:
        return []
    return sorted(list(set(completed)))

TEAM_NAME_MAPPING = {
    "Sydney": "Sydney Swans",
    "Greater Western Sydney": "GWS GIANTS",
    "Gold Coast": "Gold Coast SUNS",
    "West Coast": "West Coast Eagles"
}

def extract_team_order(ladder_data):
    return [TEAM_NAME_MAPPING.get(t['name'], t['name']) for t in ladder_data]

def calculate_score(predicted_ladder, actual_ladder):
    total_score = 0
    damage_breakdown = []
    
    for act_idx, team in enumerate(actual_ladder):
        if team not in predicted_ladder:
            # Handle API name mismatches silently to prevent breaking, though requested matching
            continue 
        
        pred_idx = predicted_ladder.index(team)
        diff = abs(pred_idx - act_idx)
        
        if diff == 0:
            score = -1
        else:
            score = diff
            
        total_score += score
        damage_breakdown.append({
            "Team": team,
            "Predicted Rank": pred_idx + 1,
            "Actual Rank": act_idx + 1,
            "Damage": score
        })
        
    return total_score, damage_breakdown

# --- APP UI ---

# Fetch Core Data
with st.spinner("Fetching data from Squiggle API..."):
    games = fetch_games_for_year(YEAR)
    completed_rounds = get_completed_rounds(games)
    live_ladder_raw, live_ladder_year = fetch_live_ladder()
    live_ladder = extract_team_order(live_ladder_raw)

if live_ladder_year and live_ladder_year != YEAR:
    st.info(f"ℹ️ No {YEAR} ladder data is available yet — showing **{live_ladder_year}** data.")

if not live_ladder:
    st.error("Could not fetch the live ladder. Squiggle API might be down.")
    st.stop()

# Sync local history once per session (no-op when all rounds already cached)
if 'local_history' not in st.session_state:
    with st.spinner("Syncing local data cache…"):
        st.session_state.local_history = sync_local_history(YEAR, completed_rounds)

# --- Pre-compute df_history before navigation (cached in session_state by completed_rounds) ---
if st.session_state.get('df_history_rounds') != list(completed_rounds):
    historical_scores = []
    if completed_rounds:
        progress_bar = st.progress(0, text="Calculating historical scores...")
        for i, rd in enumerate(completed_rounds):
            progress_bar.progress((i + 1) / len(completed_rounds), text=f"Processing Round {rd}...")
            round_ladder_raw = fetch_historical_ladder(YEAR, rd)
            round_ladder = extract_team_order(round_ladder_raw)
            if not round_ladder:
                continue
            for entity in ALL_ENTITIES:
                score, _ = calculate_score(PREDICTIONS[entity], round_ladder)
                historical_scores.append({
                    "Round": rd, "Entity": entity, "Score": score,
                    "Type": "Human" if entity in HUMANS else "Benchmark"
                })
        progress_bar.empty()
    st.session_state.df_history = pd.DataFrame(historical_scores) if historical_scores else pd.DataFrame()
    st.session_state.df_history_rounds = list(completed_rounds)

df_history = st.session_state.df_history

active_round = 0
if games:
    active_round = max([g.get('round', 0) for g in games if g.get('complete', 0) > 0], default=0)


def _compute_dashboard_scores(target_ladder, prev_ladder):
    """Build a sorted df_target with dmg_delta / rank_delta columns."""
    scores = []
    for entity in ALL_ENTITIES:
        score, _ = calculate_score(PREDICTIONS[entity], target_ladder)
        scores.append({"Entity": entity, "Score": score,
                       "Type": "Human" if entity in HUMANS else "Benchmark"})
    df = pd.DataFrame(scores).sort_values("Score").reset_index(drop=True)

    prev_scores, prev_ranks = {}, {}
    if prev_ladder:
        for entity in ALL_ENTITIES:
            s, _ = calculate_score(PREDICTIONS[entity], prev_ladder)
            prev_scores[entity] = s
        pf = (pd.DataFrame([{"Entity": e, "Score": s} for e, s in prev_scores.items()])
              .sort_values("Score").reset_index(drop=True))
        for idx, row in pf.iterrows():
            prev_ranks[row['Entity']] = idx + 1

    df['dmg_delta'] = 0
    df['rank_delta'] = 0
    for idx, row in df.iterrows():
        e, s, r = row['Entity'], row['Score'], idx + 1
        df.at[idx, 'dmg_delta'] = s - prev_scores.get(e, s)
        df.at[idx, 'rank_delta'] = prev_ranks.get(e, r) - r
    return df


# --- Session-state navigation ---
if 'active_page' not in st.session_state:
    st.session_state.active_page = 'season_tracking'

_NAV = [
    ('season_tracking',      'Season Tracking'),
    ('dashboards',           'Dashboards'),
    ('prediction_breakdown', 'Prediction Breakdown'),
    ('ladder_predictor',     'Ladder Predictor'),
]

def _set_active_page(page_key):
    st.session_state.active_page = page_key

def _set_chart_view(view):
    st.session_state.chart_view = view

# Compute leader for context strip (quick pass over live ladder)
_strip_scores = sorted(
    [(e, calculate_score(PREDICTIONS[e], live_ladder)[0]) for e in HUMANS],
    key=lambda x: x[1]
)
_strip_leader       = _strip_scores[0][0] if _strip_scores else "—"
_strip_leader_score = _strip_scores[0][1] if _strip_scores else 0

_next_game = next((g for g in games if g.get('complete', 0) < 100), None)
if _next_game:
    try:
        _ng_date = datetime.datetime.strptime(_next_game['date'][:10], "%Y-%m-%d")
        _ng_str  = f"{_next_game['hteam']} vs {_next_game['ateam']} · {_ng_date.strftime('%d %b').lstrip('0')}"
    except Exception:
        _ng_str = f"{_next_game.get('hteam','')} vs {_next_game.get('ateam','')}"
else:
    _ng_str = ""

_round_label = f"Round {active_round}" if active_round else "Pre-season"

st.markdown(f"""
<div class="context-strip">
  <div class="cs-left">
    <span class="cs-app">AFL LADDER BET</span>
    <span class="cs-sep">·</span>
    <span class="cs-round">{_round_label}</span>
    <span class="cs-sep">·</span>
    <span class="cs-leader">🥇 <strong>{_strip_leader}</strong> leads · {_strip_leader_score} pts damage</span>
  </div>
  <div class="cs-right">{"<span class='live-dot'></span>Next: " + _ng_str if _ng_str else ""}</div>
</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div id="nav-marker"></div>', unsafe_allow_html=True)
    _nc = st.columns(len(_NAV))
    for _c, (_k, _l) in zip(_nc, _NAV):
        with _c:
            st.button(
                _l,
                use_container_width=True,
                type='primary' if st.session_state.active_page == _k else 'secondary',
                key=f'_nav_{_k}',
                on_click=_set_active_page,
                args=(_k,)
            )

st.markdown('<div style="height:1.2rem"></div>', unsafe_allow_html=True)
_page = st.session_state.active_page

if _page == 'season_tracking':
    if df_history.empty:
        st.info("No games have been completed yet this season!")
    else:
        # Round Selector
        sel_col, _ = st.columns([1, 2])
        with sel_col:
            round_options = ["Live"] + [f"Round {r}" for r in completed_rounds]
            selected_round_str = st.selectbox("Viewing:", round_options)

        is_live = selected_round_str == "Live"
        rd_num  = None if is_live else int(selected_round_str.split(" ")[1])

        # Determine target ladder
        if is_live:
            target_ladder = live_ladder
            header_text = "Current live leaderboard"
        else:
            target_ladder = extract_team_order(fetch_historical_ladder(YEAR, rd_num))
            header_text = f"Leaderboard after {selected_round_str.lower()}"

        # Determine previous round ladder for deltas
        prev_ladder = None
        delta_explainer = ""
        if is_live:
            baseline_round = active_round - 1
            if baseline_round > 0:
                prev_ladder = extract_team_order(fetch_historical_ladder(YEAR, baseline_round))
                delta_explainer = f"Changes in damage and rank are since the end of round {baseline_round}"
        else:
            try:
                prev_idx = completed_rounds.index(rd_num) - 1
                if prev_idx >= 0:
                    baseline_round = completed_rounds[prev_idx]
                    prev_ladder = extract_team_order(fetch_historical_ladder(YEAR, baseline_round))
                    delta_explainer = f"Changes in damage and rank are since the end of round {baseline_round}"
            except ValueError:
                pass

        # Calculate Target Scores
        current_scores = []
        for entity in ALL_ENTITIES:
            score, _ = calculate_score(PREDICTIONS[entity], target_ladder)
            current_scores.append({
                "Entity": entity,
                "Score": score,
                "Type": "Human" if entity in HUMANS else "Benchmark"
            })
        df_target = pd.DataFrame(current_scores).sort_values(by="Score").reset_index(drop=True)

        # Calculate Previous Scores for Delta
        prev_scores_dict = {}
        prev_rank_dict = {}
        if prev_ladder:
            for entity in ALL_ENTITIES:
                score, _ = calculate_score(PREDICTIONS[entity], prev_ladder)
                prev_scores_dict[entity] = score
            prev_df = pd.DataFrame([{"Entity": e, "Score": s} for e, s in prev_scores_dict.items()]).sort_values(by="Score").reset_index(drop=True)
            for idx, row in prev_df.iterrows():
                prev_rank_dict[row['Entity']] = idx + 1

        df_target['dmg_delta'] = 0
        df_target['rank_delta'] = 0
        if prev_ladder:
            for idx, row in df_target.iterrows():
                entity = row['Entity']
                score = row['Score']
                rank = idx + 1
                prev_score = prev_scores_dict.get(entity, score)
                prev_rank = prev_rank_dict.get(entity, rank)
                df_target.at[idx, 'dmg_delta'] = score - prev_score
                df_target.at[idx, 'rank_delta'] = prev_rank - rank

        # --- AI Summary Section ---
        # Lazy: only generate when the user opens the expander and clicks Generate.
        # Nothing is fetched/generated on page load, keeping startup fast.
        def _generate_ai():
            prev_rd_ladder = None
            if len(completed_rounds) > 1:
                prev_rd_ladder = extract_team_order(fetch_historical_ladder(YEAR, completed_rounds[-2]))
            return generate_ai_summary(target_ladder, prev_rd_ladder, games, df_target)

        with st.expander("🤖 AI Season Insights", expanded=False):
            if 'ai_summary' not in st.session_state:
                st.caption("Get an AI-written recap of ladder movements, key results and what's driving each competitor's score.")
                if st.button("✨ Generate Insights", key="gen_ai", type="primary"):
                    with st.spinner("🤖 AI is analysing the season…"):
                        st.session_state.ai_summary = _generate_ai()
                    st.rerun()
            else:
                if st.button("🔄 Refresh Insights", key="refresh_ai"):
                    with st.spinner("🤖 Refreshing AI insights…"):
                        st.session_state.ai_summary = _generate_ai()
                    st.rerun()
                st.markdown(st.session_state.ai_summary)

        # --- Build chart (single, toggled) ---
        if 'chart_view' not in st.session_state:
            st.session_state.chart_view = 'competitors'

        _chart_df = (df_history[df_history["Type"] == "Human"]
                     if st.session_state.chart_view == 'competitors' else df_history)
        _use_dash = st.session_state.chart_view == 'full_field'

        fig_main = px.line(
            _chart_df, x="Round", y="Score", color="Entity", markers=True,
            line_dash="Type" if _use_dash else None,
            template="plotly_dark",
            line_shape="spline"
        )
        fig_main.update_yaxes(
            autorange="reversed", showgrid=False, zeroline=False, fixedrange=True,
            title_text="Damage (lower = better)",
            title_font=dict(size=11, color="#475569"),
            tickfont=dict(color="#475569")
        )
        fig_main.update_xaxes(showgrid=False, zeroline=False, fixedrange=True,
                               tickfont=dict(color="#475569"))
        fig_main.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Damage: %{y}<extra></extra>")
        fig_main.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Outfit"), hovermode="closest",
            margin=dict(t=10, b=10),
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
        )

        # Columns: Ladder | Graphs
        col_ladder, col_graphs = st.columns([1, 2])

        with col_ladder:
            st.markdown(f"<div style='font-size:1rem;font-weight:700;margin-bottom:4px;'>{header_text}</div>", unsafe_allow_html=True)
            if delta_explainer:
                st.markdown(f"<div style='font-size:0.72rem;color:#475569;margin-bottom:10px;'>{delta_explainer} &nbsp;·&nbsp; ↓ pts = improved &nbsp;·&nbsp; ↑ pos = moved up</div>", unsafe_allow_html=True)

            # Column headers
            html_ladder = """
<div class="lb-col-headers">
  <div class="lb-col-header">#</div>
  <div class="lb-col-header">Competitor</div>
  <div class="lb-col-header right" title="Total damage score. Lower is better — sum of abs(predicted rank − actual rank) for all 18 teams, with −1 for perfect picks.">Pts ⓘ</div>
  <div class="lb-col-header right" title="Change in damage score vs previous round. Green = improved (score went down).">Pts Δ ⓘ</div>
  <div class="lb-col-header right" title="Change in leaderboard position vs previous round. Green = moved up.">Pos Δ ⓘ</div>
</div>
"""
            for idx, row in df_target.iterrows():
                rank       = idx + 1
                entity_name = row['Entity']
                score      = int(row['Score'])
                entity_type = row['Type'].lower()

                rank_cls = ("gold" if rank == 1 else
                            "silver" if rank == 2 else
                            "bronze" if rank == 3 else "")

                if prev_ladder:
                    dmg_diff  = int(row['dmg_delta'])
                    rank_diff = int(row['rank_delta'])
                    if dmg_diff < 0:
                        pts_bubble = f'<span class="bubble b-green">↓{abs(dmg_diff)} pts</span>'
                    elif dmg_diff > 0:
                        pts_bubble = f'<span class="bubble b-red">↑{dmg_diff} pts</span>'
                    else:
                        pts_bubble = '<span class="bubble b-gray">— pts</span>'

                    if rank_diff > 0:
                        pos_bubble = f'<span class="bubble b-green">↑{rank_diff}</span>'
                    elif rank_diff < 0:
                        pos_bubble = f'<span class="bubble b-red">↓{abs(rank_diff)}</span>'
                    else:
                        pos_bubble = '<span class="bubble b-gray">—</span>'
                else:
                    pts_bubble = '<span class="bubble b-gray">—</span>'
                    pos_bubble = '<span class="bubble b-gray">—</span>'

                html_ladder += f"""<div class="compact-row {entity_type}">
<div class="c-rank {rank_cls}">{rank}</div>
<div class="c-name">{entity_name}</div>
<div class="c-score">{score}</div>
<div style="text-align:right">{pts_bubble}</div>
<div style="text-align:right">{pos_bubble}</div>
</div>
"""
            st.markdown(html_ladder, unsafe_allow_html=True)

        with col_graphs:
            # Chart toggle
            tc1, tc2, _ = st.columns([1, 1, 3])
            with tc1:
                st.button("Competitors", key="chart_tog_comp", use_container_width=True,
                          type="primary" if st.session_state.chart_view == 'competitors' else "secondary",
                          on_click=_set_chart_view, args=('competitors',))
            with tc2:
                st.button("Full Field", key="chart_tog_full", use_container_width=True,
                          type="primary" if st.session_state.chart_view == 'full_field' else "secondary",
                          on_click=_set_chart_view, args=('full_field',))
            st.plotly_chart(fig_main, use_container_width=True, config={'displayModeBar': False})


if _page == 'dashboards':
    if df_history.empty:
        st.info("No completed rounds yet — check back after Round 1 is complete.")
    else:
        # Round selector
        dash_sel_col, _ = st.columns([1, 2])
        with dash_sel_col:
            dash_round_options = ["Live"] + [f"Round {r}" for r in completed_rounds]
            dash_selected_round = st.selectbox("Viewing:", dash_round_options, key="dash_round_select")

        dash_is_live = dash_selected_round == "Live"
        dash_rd_num = None if dash_is_live else int(dash_selected_round.split(" ")[1])

        if dash_is_live:
            dash_target_ladder = live_ladder
        else:
            dash_target_ladder = extract_team_order(fetch_historical_ladder(YEAR, dash_rd_num))

        # Determine previous round for deltas
        dash_prev_ladder = None
        if dash_is_live:
            if active_round > 1:
                dash_prev_ladder = extract_team_order(fetch_historical_ladder(YEAR, active_round - 1))
        else:
            try:
                prev_idx = completed_rounds.index(dash_rd_num) - 1
                if prev_idx >= 0:
                    dash_prev_ladder = extract_team_order(fetch_historical_ladder(YEAR, completed_rounds[prev_idx]))
            except ValueError:
                pass

        dash_df_target = _compute_dashboard_scores(dash_target_ladder, dash_prev_ladder)

        active_dash = st.session_state.get('active_dashboard')

        _dash_cards = [
            ("leaderboard", "🏆", "Leaderboard",
             "Full standings with damage progression charts for every competitor."),
            ("breakdown_team", "📋", "Breakdown (Team)",
             "What each competitor predicted at every rank, and the damage each call causes."),
            ("breakdown_competitor", "🎯", "Breakdown (Competitor)",
             "For each team's actual position, the damage it adds to every competitor."),
        ]

        # Each card IS the button — clicking anywhere on the box opens the
        # dashboard below. The label is markdown (bold title + description) and
        # the button is styled to look like a card via #dash-cards-marker CSS.
        cards_box = st.container()
        with cards_box:
            st.markdown('<div id="dash-cards-marker"></div>', unsafe_allow_html=True)
            cols = st.columns(3, gap="medium")
            for col, (dash_id, icon, title, desc) in zip(cols, _dash_cards):
                with col:
                    label = f"{icon}  **{title}**\n\n{desc}"
                    if st.button(label, key=f"dashbtn_{dash_id}", use_container_width=True,
                                 type="primary" if active_dash == dash_id else "secondary"):
                        st.session_state.active_dashboard = dash_id
                        st.rerun()

        # Re-read in case a button above changed it this pass
        active_dash = st.session_state.get('active_dashboard')

        if active_dash is not None:
            st.markdown("---")
            _dash_titles = {
                "leaderboard":         "🏆 Leaderboard Dashboard",
                "breakdown_team":      "📋 Breakdown (Team)",
                "breakdown_competitor":"🎯 Breakdown (Competitor)",
            }
            hcol, ccol = st.columns([6, 1])
            with hcol:
                st.subheader(_dash_titles.get(active_dash, ""))
                st.caption(f"Showing **{dash_selected_round}** · use the **Download** button inside the poster to save a high-res image.")
            with ccol:
                st.write("")
                if st.button("✕ Close", key="close_dash", use_container_width=True):
                    st.session_state.active_dashboard = None
                    st.rerun()

            if active_dash == "leaderboard":
                with st.spinner("Generating high-fidelity dashboard..."):
                    components.html(get_poster_html(dash_df_target, df_history, dash_selected_round), height=1000, scrolling=True)
            elif active_dash == "breakdown_team":
                with st.spinner("Generating breakdown dashboard..."):
                    components.html(get_breakdown_poster_html(dash_target_ladder, dash_selected_round), height=980, scrolling=True)
            elif active_dash == "breakdown_competitor":
                with st.spinner("Generating competitor breakdown..."):
                    components.html(get_competitor_breakdown_poster_html(dash_target_ladder, dash_selected_round), height=980, scrolling=True)


if _page == 'prediction_breakdown':
    c_dropdown, _ = st.columns([1, 2])
    with c_dropdown:
        options = ["Live AFL Ladder"] + ALL_ENTITIES
        selected_view = st.selectbox("Select participant:", options)

    col_table, col_empty = st.columns([2, 1])

    with col_table:
        if selected_view == "Live AFL Ladder":
            st.subheader("Live AFL Ladder")
            df_live_display = pd.DataFrame(live_ladder_raw)
            if not df_live_display.empty:
                html_table = '<div class="table-wrapper"><table class="modern-table">'
                html_table += '<thead><tr><th>Rank</th><th>Team</th><th>Pts</th><th>%</th></tr></thead><tbody>'
                for _, row in df_live_display.iterrows():
                    team_name = TEAM_NAME_MAPPING.get(row['name'], row['name'])
                    html_table += f"<tr><td>{row['rank']}</td><td><strong>{team_name}</strong></td><td>{row['pts']}</td><td>{row['percentage']:.1f}</td></tr>"
                html_table += '</tbody></table></div>'
                st.markdown(html_table, unsafe_allow_html=True)
        else:
            total_score, breakdown = calculate_score(PREDICTIONS[selected_view], live_ladder)
            df_bd = pd.DataFrame(breakdown)

            # Callout metrics
            df_sorted_dmg  = df_bd.sort_values("Damage", ascending=False)
            worst_row      = df_sorted_dmg.iloc[0]
            best_row       = df_bd[df_bd["Damage"] >= 0].sort_values("Damage").iloc[0] if not df_bd[df_bd["Damage"] >= 0].empty else df_bd.sort_values("Damage").iloc[-1]
            perfect_count  = len(df_bd[df_bd["Damage"] == -1])
            worst_teams    = set(df_sorted_dmg.head(2)["Team"].tolist())
            best_teams     = set(df_bd[df_bd["Damage"] >= 0].nsmallest(2, "Damage")["Team"].tolist()) if not df_bd[df_bd["Damage"] >= 0].empty else set()

            st.markdown(f"""
<div class="pb-metrics">
  <div class="pb-card">
    <div class="pb-card-label">Biggest Liability</div>
    <div class="pb-card-val red">{worst_row['Team']}</div>
    <div class="pb-card-sub">Pred #{int(worst_row['Predicted Rank'])} · Actual #{int(worst_row['Actual Rank'])} · {int(worst_row['Damage'])} pts</div>
  </div>
  <div class="pb-card">
    <div class="pb-card-label">Best Pick</div>
    <div class="pb-card-val green">{best_row['Team']}</div>
    <div class="pb-card-sub">Pred #{int(best_row['Predicted Rank'])} · Actual #{int(best_row['Actual Rank'])} · {int(best_row['Damage'])} pts</div>
  </div>
  <div class="pb-card">
    <div class="pb-card-label">Perfect Picks</div>
    <div class="pb-card-val sky">{perfect_count} team{"s" if perfect_count != 1 else ""}</div>
    <div class="pb-card-sub">−1 bonus each · Total: {total_score} pts</div>
  </div>
</div>
<div class="insight-strip">
  ⚡ <strong>{worst_row['Team']}</strong> is your biggest liability — predicted #{int(worst_row['Predicted Rank'])}, currently sitting #{int(worst_row['Actual Rank'])}. Costs <strong>{int(worst_row['Damage'])} points</strong> alone.
</div>
""", unsafe_allow_html=True)

            df_bd_sorted = df_bd.sort_values("Predicted Rank")
            html_table = '<div class="table-wrapper"><table class="modern-table">'
            html_table += '<thead><tr><th>Team</th><th>Pred Rank</th><th>Act Rank</th><th>Damage</th></tr></thead><tbody>'
            for _, row in df_bd_sorted.iterrows():
                dmg  = row['Damage']
                team = row['Team']
                row_cls = "row-worst" if team in worst_teams else ("row-best" if team in best_teams else "")
                tag  = "tag-green" if dmg <= 0 else ("tag-yellow" if dmg <= 3 else "tag-red")
                html_table += (
                    f'<tr class="{row_cls}"><td><strong>{team}</strong></td>'
                    f"<td>{int(row['Predicted Rank'])}</td>"
                    f"<td>{int(row['Actual Rank'])}</td>"
                    f"<td><span class='{tag}'>{dmg}</span></td></tr>"
                )
            html_table += '</tbody></table></div>'
            st.markdown(html_table, unsafe_allow_html=True)


# Declare the sortable component once at script level so it isn't re-registered
# on every fragment rerun.
_afl_sortable = components.declare_component(
    "afl_sortable",
    path=os.path.join(os.path.dirname(__file__), "custom_sortable")
)

@st.fragment
def _ladder_predictor_ui():
    """
    Isolated fragment for the drag-and-drop ladder predictor.
    Scores auto-display from session_state. The iframe 'Calculate Scores'
    button is the only trigger for a Streamlit rerun, so dragging is perfectly smooth.
    """
    if 'custom_ladder' not in st.session_state:
        st.session_state.custom_ladder = live_ladder.copy()
    if 'ladder_nonce' not in st.session_state:
        st.session_state.ladder_nonce = 0

    col_drag, col_results = st.columns([1, 1])

    with col_drag:
        head_l, head_r = st.columns([3, 2])
        with head_l:
            st.subheader("Build Final Ladder")
        with head_r:
            st.write("")
            if st.button("↺ Reset to live", key="reset_ladder", use_container_width=True,
                         help="Reset the draggable ladder back to the current live AFL standings."):
                st.session_state.custom_ladder = live_ladder.copy()
                st.session_state.ladder_nonce += 1
                st.rerun()

        st.caption("Drag teams into your predicted final order, then hit **Calculate Scores** at the bottom of the list.")

        teams_data = [
            {
                "name": t,
                **{k: TEAM_STYLES.get(t, {"bg": "#ffffff", "text": "#000000", "logo": ""})[k]
                   for k in ("bg", "text", "logo")}
            }
            for t in st.session_state.custom_ladder
        ]

        # nonce in the key forces a fresh iframe (re-init) after a reset
        custom_ladder = _afl_sortable(
            teams=teams_data,
            default=st.session_state.custom_ladder,
            key=f"sortable_{st.session_state.ladder_nonce}"
        )
        if custom_ladder:
            st.session_state.custom_ladder = custom_ladder

    with col_results:
        st.subheader("Predicted Result")
        ladder_to_score = st.session_state.custom_ladder

        if ladder_to_score:
            custom_scores = [
                {
                    "Participant": entity,
                    "Damage": calculate_score(PREDICTIONS[entity], ladder_to_score)[0],
                    "Type": "Human" if entity in HUMANS else "Benchmark"
                }
                for entity in ALL_ENTITIES
            ]
            df_custom = pd.DataFrame(custom_scores).sort_values("Damage").reset_index(drop=True)
            df_custom.index += 1  # 1-indexed ranks

            # Winner callout
            win = df_custom.iloc[0]
            runner = df_custom.iloc[1] if len(df_custom) > 1 else None
            margin_txt = ""
            if runner is not None:
                gap = int(runner['Damage']) - int(win['Damage'])
                margin_txt = f" — {gap} pt{'s' if gap != 1 else ''} clear of {runner['Participant']}" if gap > 0 else f" — tied with {runner['Participant']}"
            st.markdown(f"""
<div class="insight-strip" style="margin-top:4px;">
  🏆 If this is the final ladder, <strong>{win['Participant']}</strong> wins with <strong>{int(win['Damage'])} damage</strong>{margin_txt}.
</div>""", unsafe_allow_html=True)

            html_custom = '<div class="table-wrapper"><table class="modern-table">'
            html_custom += '<thead><tr><th>Rank</th><th>Participant</th><th>Type</th><th>Total Damage</th></tr></thead><tbody>'
            for rank, row in df_custom.iterrows():
                row_cls = "row-best" if rank == 1 else ""
                medal = "🥇 " if rank == 1 else ("🥈 " if rank == 2 else ("🥉 " if rank == 3 else ""))
                html_custom += (
                    f'<tr class="{row_cls}"><td>{medal}{rank}</td>'
                    f"<td><strong>{row['Participant']}</strong></td>"
                    f"<td>{row['Type']}</td>"
                    f"<td>{int(row['Damage'])}</td></tr>"
                )
            html_custom += '</tbody></table></div>'
            st.markdown(html_custom, unsafe_allow_html=True)
        else:
            st.info("Drag the teams into your preferred order, then click **Calculate Scores** in the ladder panel.")


if _page == 'ladder_predictor':
    st.markdown("<div style='font-size:1.2rem;font-weight:700;margin-bottom:2px;'>Ladder Predictor</div>", unsafe_allow_html=True)
    st.caption("Build a hypothetical final ladder and instantly see how every competitor would score against it. Great for asking \"what if?\"")
    _ladder_predictor_ui()
