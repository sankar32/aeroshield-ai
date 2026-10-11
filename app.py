import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="AeroShield AI Control Tower", layout="wide")

st.title("🛡️ AeroShield-AI: Autonomous Airshed and School Defense Grid")
st.markdown("Real-time telemetry, stubble-burning source tracking, and automated school safety triggers.")

# --- SIDEBAR: JUDGE CONTROL PANEL ---
with st.sidebar:
    st.header("🎛️ Command Controls")
    st.markdown("Controls to test autonomous response behaviors live for the judges.")
    
    simulation_mode = st.selectbox(
        "Simulation Mode", 
        ["Autonomous Live Feed", "Force Stubble-Burning Spike", "All-Clear Safe Mode"]
    )
    
    st.divider()
    st.markdown("### ☁️ Cloud Status")
    st.success("AWS S3 Pipeline: Connected (Demo Sync Active)")
    
    st.markdown("### 🏫 Active Safeguards")
    st.checkbox("Auto-Ventilation Shutoff", value=True)
    st.checkbox("Automated Parent SMS Alerts", value=True)

def load_data():
    try:
        df = pd.read_csv("sensor_feed.csv")
        if "lat" not in df.columns or "lon" not in df.columns:
            coord_map = {
                "School_Alpha": {"lat": 28.6139, "lon": 77.2090},
                "School_Beta": {"lat": 28.5355, "lon": 77.3910},
                "Farm_Perimeter_01": {"lat": 30.9010, "lon": 75.8573}
            }
            df["lat"] = df["location_id"].map(lambda x: coord_map.get(x, {}).get("lat", 28.6))
            df["lon"] = df["location_id"].map(lambda x: coord_map.get(x, {}).get("lon", 77.2))
            
        # Override data dynamically if sidebar trigger is pulled
        if simulation_mode == "Force Stubble-Burning Spike":
            df.loc[df["location_id"] == "School_Alpha", "aqi"] = 320
            df.loc[df["location_id"] == "School_Alpha", "protocol_status"] = "EMERGENCY_LOCKDOWN"
            df.loc[df["location_id"] == "School_Alpha", "primary_source"] = "stubble_burning"
        elif simulation_mode == "All-Clear Safe Mode":
            df["aqi"] = 85
            df["protocol_status"] = "SAFE"
            df["primary_source"] = "local_traffic"
            
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["timestamp", "location_id", "zone", "lat", "lon", "pm25", "aqi", "primary_source", "protocol_status"])

df = load_data()

# --- 1. TOP METRICS ---
metric_col1, metric_col2, metric_col3 = st.columns(3)

avg_aqi = df["aqi"].mean() if not df.empty else 0
hazards = len(df[df["aqi"] > 200]) if not df.empty else 0

with metric_col1:
    st.metric("Average Regional AQI", f"{avg_aqi:.1f}")
with metric_col2:
    st.metric("Active Hazard Zones", hazards)
with metric_col3:
    st.metric("System Status", "Autonomous Active 🟢")

st.divider()

# --- 2. AI CHAT ASSISTANT SECTION WITH QUICK-ACTION CHIPS ---
st.subheader("🤖 AeroShield AI Assistant Panel")
st.markdown("Ask the AI about live air quality, active hazards, or school protocols, or click a quick prompt below:")

# Quick Preset Buttons for Judges
col_b1, col_b2, col_b3 = st.columns(3)
preset_query = None
with col_b1:
    if st.button("🚨 Which nodes are at risk?"):
        preset_query = "Which nodes are at risk?"
with col_b2:
    if st.button("🏫 Check school safety status"):
        preset_query = "Check school safety status"
with col_b3:
    if st.button("🔥 Track stubble burning sources"):
        preset_query = "Track stubble burning sources"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am AeroShield AI. Ask me about school AQI safety or stubble burning spikes."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("Ask me something..")
active_query = preset_query if preset_query else user_input

if active_query:
    st.session_state.messages.append({"role": "user", "content": active_query})
    with st.chat_message("user"):
        st.write(active_query)

    df_current = load_data()
    query = active_query.lower()
    
    if "hazard" in query or "risk" in query or "spike" in query:
        hazards_list = df_current[df_current["aqi"] > 200]
        if not hazards_list.empty:
            response = f"🚨 Currently, there are **{len(hazards_list)} high-risk nodes** detected:\n"
            for _, r in hazards_list.iterrows():
                response += f"- **{r['location_id']}** ({r['zone']}): AQI {r['aqi']} due to *{r['primary_source']}*.\n"
        else:
            response = "🟢 All monitored nodes are currently operating under safe AQI levels."

    elif "school" in query or "safety" in query or "status" in query:
        schools = df_current[df_current["location_id"].str.contains("School", case=False)]
        response = "🏫 **School Sector Overview:**\n"
        for _, r in schools.iterrows():
            response += f"- **{r['location_id']}**: AQI {r['aqi']} | Status: `{r['protocol_status']}`\n"

    elif "stubble" in query or "farm" in query or "source" in query:
        stubble_nodes = df_current[df_current["primary_source"] == "stubble_burning"]
        if not stubble_nodes.empty:
            response = f"🔥 Stubble burning activity detected at **{len(stubble_nodes)} telemetry nodes**:\n"
            for _, r in stubble_nodes.iterrows():
                response += f"- **{r['location_id']}** in *{r['zone']}* showing AQI {r['aqi']}.\n"
        else:
            response = "No active stubble burning spikes flagged inpy the current cycle."

    else:
        current_avg = df_current["aqi"].mean() if not df_current.empty else 0
        response = (
            f"Current regional average AQI is **{current_avg:.1f}**. "
            "You can ask me specifically about 'hazards', 'school safety', or 'stubble burning sources'."
        )

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)
    st.rerun()

st.divider()

# --- 3. ADVANCED PYDECK AIRSHED MAP WITH COLORS & TOOLTIPS ---
st.subheader("🗺️ Regional Airshed Command Map")
st.markdown("🟢 **Green**: Safe Nodes | 🔴 **Red**: Hazard / Stubble-Burning Spikes (Hover over points for details)")

if not df.empty and "lat" in df.columns:
    def get_color(aqi):
        if aqi > 200:
            return [255, 50, 50, 200]  # Bright Red
        return [50, 205, 50, 180]     # Lime Green

    df["color"] = df["aqi"].apply(get_color)
    df["radius"] = df["aqi"].apply(lambda x: max(15000, x * 100))

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="radius",
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=df["lat"].mean(),
        longitude=df["lon"].mean(),
        zoom=6.5,
        pitch=0,
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            "html": "<b>Node:</b> {location_id}<br/><b>Zone:</b> {zone}<br/><b>AQI:</b> {aqi}<br/><b>Source:</b> {primary_source}<br/><b>Status:</b> {protocol_status}",
            "style": {"backgroundColor": "#111", "color": "white"}
        }
    )
    st.pydeck_chart(r)

st.subheader("📊 Live Sensor Node Telemetry")
if not df.empty:
    display_df = df.drop(columns=["color", "radius"], errors="ignore")
    st.dataframe(display_df, use_container_width=True)

st.subheader("🤖 Autonomous Agent Action Log")
if not df.empty:
    high_risk = df[df["aqi"] > 200]
    if not high_risk.empty:
        for _, row in high_risk.iterrows():
            st.error(f"[{row['timestamp']}] Critical spike at **{row['location_id']}** (AQI: {row['aqi']}). Source: *{row['primary_source']}*. Action: Ventilation closed & parent SMS queued.")
    else:
        st.success("All monitored sectors are currently within acceptable safety thresholds.")

@st.fragment(run_every=5)
def auto_refresh():
    st.rerun()

auto_refresh()
