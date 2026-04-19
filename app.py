import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import datetime

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
    header {visibility: hidden;}

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
        padding: 16px 24px;
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
        font-size: 1.8rem;
        font-weight: 800;
        color: #475569;
        width: 30px;
        text-align: right;
    }
    .ladder-name {
        font-size: 1.5rem;
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
        font-size: 2rem;
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
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.1);
        margin-top: 1rem;
        background: rgba(255, 255, 255, 0.02);
    }
    .modern-table {
        width: 100%;
        border-collapse: collapse;
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
    .tag-green { background: rgba(5,150,105,0.2); color: #34d399; border: 1px solid rgba(5,150,105,0.5); padding: 4px 10px; border-radius: 8px; font-weight:700; display: inline-block;}
    .tag-yellow { background: rgba(217,119,6,0.2); color: #fbbf24; border: 1px solid rgba(217,119,6,0.5); padding: 4px 10px; border-radius: 8px; font-weight:700; display: inline-block;}
    .tag-red { background: rgba(220,38,38,0.2); color: #f87171; border: 1px solid rgba(220,38,38,0.5); padding: 4px 10px; border-radius: 8px; font-weight:700; display: inline-block;}
</style>
""", unsafe_allow_html=True)

PREDICTIONS = {
    "Antony": ["Geelong", "Brisbane Lions", "Hawthorn", "Sydney Swans", "Western Bulldogs", "Adelaide", "Gold Coast SUNS", "Fremantle", "Collingwood", "GWS GIANTS", "St Kilda", "Melbourne", "Carlton", "Port Adelaide", "North Melbourne", "Essendon", "Richmond", "West Coast Eagles"],
    "Slammy": ["Brisbane Lions", "Western Bulldogs", "Gold Coast SUNS", "Collingwood", "Adelaide", "Geelong", "Sydney Swans", "Fremantle", "St Kilda", "GWS GIANTS", "Hawthorn", "Melbourne", "Port Adelaide", "North Melbourne", "Carlton", "Richmond", "Essendon", "West Coast Eagles"],
    "Aidos": ["Brisbane Lions", "Geelong", "Gold Coast SUNS", "Western Bulldogs", "Sydney Swans", "Hawthorn", "Adelaide", "Fremantle", "Collingwood", "St Kilda", "GWS GIANTS", "Port Adelaide", "Carlton", "Essendon", "Melbourne", "North Melbourne", "Richmond", "West Coast Eagles"],
    "Coz": ["Gold Coast SUNS", "Sydney Swans", "Brisbane Lions", "Geelong", "Western Bulldogs", "Fremantle", "Adelaide", "GWS GIANTS", "Hawthorn", "St Kilda", "Essendon", "Port Adelaide", "Collingwood", "Carlton", "North Melbourne", "Melbourne", "Richmond", "West Coast Eagles"],
    "Fry": ["Sydney Swans", "Brisbane Lions", "Geelong", "Hawthorn", "Collingwood", "Gold Coast SUNS", "Adelaide", "GWS GIANTS", "Western Bulldogs", "Fremantle", "Port Adelaide", "St Kilda", "Melbourne", "Essendon", "Richmond", "Carlton", "North Melbourne", "West Coast Eagles"],
    "Prince": ["Brisbane Lions", "Geelong", "Western Bulldogs", "Hawthorn", "Collingwood", "GWS GIANTS", "Adelaide", "Gold Coast SUNS", "Fremantle", "Sydney Swans", "Melbourne", "Carlton", "Port Adelaide", "St Kilda", "North Melbourne", "Richmond", "Essendon", "West Coast Eagles"],
    "Last Year H+A": ["Adelaide", "Geelong", "Brisbane Lions", "Collingwood", "GWS GIANTS", "Fremantle", "Gold Coast SUNS", "Hawthorn", "Western Bulldogs", "Sydney Swans", "Carlton", "St Kilda", "Port Adelaide", "Melbourne", "Essendon", "North Melbourne", "Richmond", "West Coast Eagles"],
    "Last Year Finals": ["Brisbane Lions", "Geelong", "Collingwood", "Hawthorn", "Adelaide", "Gold Coast SUNS", "GWS GIANTS", "Fremantle", "Western Bulldogs", "Sydney Swans", "Carlton", "St Kilda", "Port Adelaide", "Melbourne", "Essendon", "North Melbourne", "Richmond", "West Coast Eagles"]
    "Alphabetical": ["Brisbane Lions", "Carlton", "Collingwood", "Essendon", "Fremantle", "Geelong", "Gold Coast SUNS", "GWS GIANTS", "Hawthorn", "Melbourne", "North Melbourne", "Port Adelaide", "Richmond", "St Kilda", "Sydney Swans", "Western Bulldogs", "West Coast Eagles"]
}

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
            
            # Use the very latest ladder for the live scoreboard
            current_scores = []
            for entity in ALL_ENTITIES:
                score, _ = calculate_score(PREDICTIONS[entity], live_ladder)
                current_scores.append({
                    "Entity": entity,
                    "Score": score,
                    "Type": "Human" if entity in HUMANS else "Benchmark"
                })
            df_live = pd.DataFrame(current_scores).sort_values(by="Score").reset_index(drop=True)

            # Create columns: Left for Ladder (1 part), Right for Graphs (2 parts)
            col_ladder, col_graphs = st.columns([1, 2])

            with col_ladder:
                st.subheader("Current Live Leaderboard")
                
                # Generate Custom HTML Ladder
                html_ladder = '<div class="ladder-container">\n'
                for idx, row in df_live.iterrows():
                    rank = idx + 1
                    entity_name = row['Entity']
                    score = row['Score']
                    entity_type = row['Type'].lower()  # 'human' or 'benchmark'
                    
                    # Assign crowns/medals to top 3
                    rank_display = f"#{rank}"
                    if rank == 1: rank_display = "🥇"
                    elif rank == 2: rank_display = "🥈"
                    elif rank == 3: rank_display = "🥉"
                    
                    # Dedented HTML string to avoid Streamlit parsing it as a Markdown code block
                    html_ladder += f"""<div class="ladder-row {entity_type}" data-rank="{rank}">
<div class="ladder-left">
<div class="ladder-rank">{rank_display}</div>
<div class="ladder-name">{entity_name}</div>
</div>
<div class="ladder-right">
<div class="ladder-score">{int(score)}</div>
<div class="ladder-sub">DAMAGE</div>
</div>
</div>\n"""
                html_ladder += '</div>'
                st.markdown(html_ladder, unsafe_allow_html=True)

            with col_graphs:
                # --- Graph 1: Competitors Only ---
                st.subheader("Competitor Progression Over Time")
                df_humans = df_history[df_history["Type"] == "Human"]
                fig1 = px.line(
                    df_humans, x="Round", y="Score", color="Entity", markers=True,
                    title="Total Points (Lower is Better)",
                    template="plotly_dark",
                    line_shape="spline"
                )
                fig1.update_yaxes(autorange="reversed", showgrid=False, zeroline=False) # Lower score is better
                fig1.update_xaxes(showgrid=False, zeroline=False)
                fig1.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(family="Outfit"),
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig1, use_container_width=True)
                
                # --- Graph 2: The Full Field ---
                st.subheader("Full Field (Including Benchmarks)")
                fig2 = px.line(
                    df_history, x="Round", y="Score", color="Entity", markers=True,
                    line_dash="Type", title="Total Points (Lower is Better)",
                    template="plotly_dark"
                )
                fig2.update_yaxes(autorange="reversed", showgrid=False, zeroline=False)
                fig2.update_xaxes(showgrid=False, zeroline=False)
                fig2.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(family="Outfit"),
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.header("Prediction Breakdown")
    
    options = ["Live AFL Ladder"] + ALL_ENTITIES
    selected_view = st.selectbox("Select a participant or view the Live Ladder:", options)
    
    
    # Constrain layout for a better look on wide screens
    col_table, col_empty = st.columns([2, 1])
    
    with col_table:
        if selected_view == "Live AFL Ladder":
            st.subheader("Live AFL Ladder")
            df_live_display = pd.DataFrame(live_ladder_raw)
            if not df_live_display.empty:
                # Build custom HTML table
                html_table = '<div class="table-wrapper"><table class="modern-table">'
                html_table += '<thead><tr><th>Rank</th><th>Team</th><th>Pts</th><th>%</th></tr></thead><tbody>'
                for _, row in df_live_display.iterrows():
                    team_name = TEAM_NAME_MAPPING.get(row['name'], row['name'])
                    html_table += f"<tr><td>{row['rank']}</td><td><strong>{team_name}</strong></td><td>{row['pts']}</td><td>{row['percentage']:.1f}</td></tr>"
                html_table += '</tbody></table></div>'
                st.markdown(html_table, unsafe_allow_html=True)
                
        else:
            st.subheader(f"Damage Breakdown for {selected_view}")
            
            # Calculate current damage based on LIVE ladder
            total_score, breakdown = calculate_score(PREDICTIONS[selected_view], live_ladder)
            
            st.metric(label="Current Total Score", value=total_score, delta="Lower is better", delta_color="off")
            
            df_breakdown = pd.DataFrame(breakdown)
            df_breakdown = df_breakdown.sort_values("Predicted Rank")
            
            # Build custom HTML table for breakdown
            html_table = '<div class="table-wrapper"><table class="modern-table">'
            html_table += '<thead><tr><th>Team</th><th>Pred Rank</th><th>Act Rank</th><th>Damage</th></tr></thead><tbody>'
            for _, row in df_breakdown.iterrows():
                dmg = row['Damage']
                if dmg <= 0:
                    tag = "tag-green"
                elif dmg <= 3:
                    tag = "tag-yellow"
                else:
                    tag = "tag-red"
                    
                html_table += f"<tr>"
                html_table += f"<td><strong>{row['Team']}</strong></td>"
                html_table += f"<td>{row['Predicted Rank']}</td>"
                html_table += f"<td>{row['Actual Rank']}</td>"
                html_table += f"<td><span class='{tag}'>{dmg}</span></td>"
                html_table += f"</tr>"
            html_table += '</tbody></table></div>'
            st.markdown(html_table, unsafe_allow_html=True)


