import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import datetime

# --- CONFIG & CONSTANTS ---
st.set_page_config(page_title="AFL Ladder Bet", layout="wide", page_icon="🏉")

PREDICTIONS = {
    "Antony": ["Geelong", "Brisbane Lions", "Hawthorn", "Sydney Swans", "Western Bulldogs", "Adelaide", "Gold Coast SUNS", "Fremantle", "Collingwood", "GWS GIANTS", "St Kilda", "Melbourne", "Carlton", "Port Adelaide", "North Melbourne", "Essendon", "Richmond", "West Coast Eagles"],
    "Slammy": ["Brisbane Lions", "Western Bulldogs", "Gold Coast SUNS", "Collingwood", "Adelaide", "Geelong", "Sydney Swans", "Fremantle", "St Kilda", "GWS GIANTS", "Hawthorn", "Melbourne", "Port Adelaide", "North Melbourne", "Carlton", "Richmond", "Essendon", "West Coast Eagles"],
    "Aidos": ["Brisbane Lions", "Geelong", "Gold Coast SUNS", "Western Bulldogs", "Sydney Swans", "Hawthorn", "Adelaide", "Fremantle", "Collingwood", "St Kilda", "GWS GIANTS", "Port Adelaide", "Carlton", "Essendon", "Melbourne", "North Melbourne", "Richmond", "West Coast Eagles"],
    "Coz": ["Gold Coast SUNS", "Sydney Swans", "Brisbane Lions", "Geelong", "Western Bulldogs", "Fremantle", "Adelaide", "GWS GIANTS", "Hawthorn", "St Kilda", "Essendon", "Port Adelaide", "Collingwood", "Carlton", "North Melbourne", "Melbourne", "Richmond", "West Coast Eagles"],
    "Fry": ["Sydney Swans", "Brisbane Lions", "Geelong", "Hawthorn", "Collingwood", "Gold Coast SUNS", "Adelaide", "GWS GIANTS", "Western Bulldogs", "Fremantle", "Port Adelaide", "St Kilda", "Melbourne", "Essendon", "Richmond", "Carlton", "North Melbourne", "West Coast Eagles"],
    "Prince": ["Brisbane Lions", "Geelong", "Western Bulldogs", "Hawthorn", "Collingwood", "GWS GIANTS", "Adelaide", "Gold Coast SUNS", "Fremantle", "Sydney Swans", "Melbourne", "Carlton", "Port Adelaide", "St Kilda", "North Melbourne", "Richmond", "Essendon", "West Coast Eagles"],
    "Last Year H+A": ["Adelaide", "Geelong", "Brisbane Lions", "Collingwood", "GWS GIANTS", "Fremantle", "Gold Coast SUNS", "Hawthorn", "Western Bulldogs", "Sydney Swans", "Carlton", "St Kilda", "Port Adelaide", "Melbourne", "Essendon", "North Melbourne", "Richmond", "West Coast Eagles"],
    "Last Year Finals": ["Brisbane Lions", "Geelong", "Collingwood", "Hawthorn", "Adelaide", "Gold Coast SUNS", "GWS GIANTS", "Fremantle", "Western Bulldogs", "Sydney Swans", "Carlton", "St Kilda", "Port Adelaide", "Melbourne", "Essendon", "North Melbourne", "Richmond", "West Coast Eagles"]
}

# Automatically add Benchmark
PREDICTIONS["Alphabetical"] = sorted(PREDICTIONS["Antony"])

HUMANS = ["Antony", "Slammy", "Aidos", "Coz", "Fry", "Prince"]
BENCHMARKS = ["Last Year H+A", "Last Year Finals", "Alphabetical"]
ALL_ENTITIES = HUMANS + BENCHMARKS

# Fall back to 2026 as per our environment defaults if needed, but best is to dynamically retrieve
YEAR = datetime.datetime.now().year

# --- API HELPERS ---
HEADERS = {"User-Agent": "AFL_Dashboard_App/1.0"}

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
    # If the current year has no data, fallback to previous years
    current_year = datetime.datetime.now().year
    for year in [current_year, current_year - 1, current_year - 2, 2024]:
        url = f"https://api.squiggle.com.au/?q=standings&year={year}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json().get('standings', [])
                if data:
                    return sorted(data, key=lambda x: x['rank'])
        except Exception:
            pass
    return []

@st.cache_data(ttl=3600)
def fetch_historical_ladder(year, round_num):
    url = f"https://api.squiggle.com.au/?q=standings&year={year}&round={round_num}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json().get('standings', [])
            return sorted(data, key=lambda x: x['rank'])
    except Exception:
        pass
    return []

# --- DATA PROCESSING ---
def get_completed_rounds(games):
    completed = [g['round'] for g in games if g.get('complete', 0) == 100]
    if not completed:
        return []
    return sorted(list(set(completed)))

def extract_team_order(ladder_data):
    return [t['name'] for t in ladder_data]

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
st.title("🏉 AFL Ladder Predictor Challenge")

# Fetch Core Data
with st.spinner("Fetching data from Squiggle API..."):
    games = fetch_games_for_year(YEAR)
    completed_rounds = get_completed_rounds(games)
    live_ladder_raw = fetch_live_ladder()
    live_ladder = extract_team_order(live_ladder_raw)

if not live_ladder:
    st.error("Could not fetch the live ladder. Squiggle API might be down.")
    st.stop()

# Tabs
tab1, tab2 = st.tabs(["📊 Season Tracking", "🎯 Prediction Breakdown"])

with tab1:
    st.header("Season Leaderboard")
    
    if len(completed_rounds) == 0:
        st.info("No games have been completed yet this season!")
    else:
        # Build Historical Dataframe
        historical_scores = []
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
                    "Round": rd,
                    "Entity": entity,
                    "Score": score,
                    "Type": "Human" if entity in HUMANS else "Benchmark"
                })
        
        progress_bar.empty()
        
        if historical_scores:
            df_history = pd.DataFrame(historical_scores)
            
            # --- Graph 1: Competitors Only ---
            st.subheader("Competitor Progression Over Time")
            df_humans = df_history[df_history["Type"] == "Human"]
            fig1 = px.line(
                df_humans, x="Round", y="Score", color="Entity", markers=True,
                title="Total Points (Lower is Better)",
                template="plotly_dark"
            )
            fig1.update_yaxes(autorange="reversed") # Lower score is better
            st.plotly_chart(fig1, use_container_width=True)
            
            # --- Graph 2: The Full Field ---
            st.subheader("Full Field (Including Benchmarks)")
            fig2 = px.line(
                df_history, x="Round", y="Score", color="Entity", markers=True,
                line_dash="Type", title="Total Points (Lower is Better)",
                template="plotly_dark"
            )
            fig2.update_yaxes(autorange="reversed")
            st.plotly_chart(fig2, use_container_width=True)
            
            # --- Graph 3: Live Leaderboard ---
            st.subheader("Current Live Leaderboard")
            
            # Use the very latest ladder for the live scoreboard
            current_scores = []
            for entity in ALL_ENTITIES:
                score, _ = calculate_score(PREDICTIONS[entity], live_ladder)
                current_scores.append({
                    "Entity": entity,
                    "Score": score,
                    "Type": "Human" if entity in HUMANS else "Benchmark"
                })
            
            df_live = pd.DataFrame(current_scores).sort_values(by="Score")
            
            fig3 = px.bar(
                df_live, x="Entity", y="Score", color="Type", text="Score",
                color_discrete_map={"Human": "#1f77b4", "Benchmark": "#ff7f0e"},
                title="Current Total Scores (Lower is Better)",
                template="plotly_dark"
            )
            # Make sure lower score looks visually preferred or at least sorted properly
            fig3.update_traces(textposition='auto')
            st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.header("Prediction Breakdown")
    
    options = ["Live AFL Ladder"] + ALL_ENTITIES
    selected_view = st.selectbox("Select a participant or view the Live Ladder:", options)
    
    if selected_view == "Live AFL Ladder":
        st.subheader("Live AFL Ladder")
        df_live_display = pd.DataFrame(live_ladder_raw)
        if not df_live_display.empty:
            df_live_display = df_live_display[['rank', 'name', 'pts', 'percentage']]
            df_live_display.columns = ['Rank', 'Team', 'Premiership Points', 'Percentage (%)']
            st.dataframe(df_live_display, use_container_width=True, hide_index=True)
    else:
        st.subheader(f"Damage Breakdown for {selected_view}")
        
        # Calculate current damage based on LIVE ladder
        total_score, breakdown = calculate_score(PREDICTIONS[selected_view], live_ladder)
        
        st.metric(label="Current Total Score", value=total_score, delta="Lower is better", delta_color="off")
        
        df_breakdown = pd.DataFrame(breakdown)
        
        # Sort by actual rank conceptually, but predicting order makes sense too
        df_breakdown = df_breakdown.sort_values("Predicted Rank")
        
        def highlight_damage(val):
            if val <= 0:
                color = '#4ade80' # Green
            elif val <= 3:
                color = '#facc15' # Yellow
            else:
                color = '#f87171' # Red
            return f'background-color: {color}; color: black;'

        # Using Pandas styling for conditional formatting
        styled_df = df_breakdown.style.map(highlight_damage, subset=['Damage'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

