import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="AeroShield AI Control Tower", layout="wide")

st.title("🛡️ AeroShield-AI: Autonomous Airshed and School Defense Grid")
st.markdown("Real-time telemetry, stubble-burning source tracking, and automated school safety triggers.")

def load_data():
    try:
        return pd.read_csv("sensor_feed.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["timestamp", "location_id", "zone", "pm25", "aqi", "primary_source", "protocol_status"])

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

# --- 2. AI CHAT ASSISTANT SECTION ---
st.subheader("🤖 AeroShield AI Assistant Panel")
st.markdown("Ask the AI about live air quality, active hazards, or school protocols based on live telemetry.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am AeroShield AI. Ask me about school AQI safety or stubble burning spikes."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_input := st.chat_input("Ask something (e.g., 'Which nodes are at risk?')..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    df_current = load_data()
    query = user_input.lower()
    
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
            response = "No active stubble burning spikes flagged in the current cycle."

    else:
        current_avg = df_current["aqi"].mean() if not df_current.empty else 0
        response = (
            f"Current regional average AQI is **{current_avg:.1f}**. "
            "You can ask me specifically about 'hazards', 'school safety', or 'stubble burning sources'."
        )

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)

st.divider()

# --- 3. LIVE TELEMETRY & ACTION LOG ---
st.subheader("📊 Live Sensor Node Telemetry")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Waiting for simulator data feed (`sensor_feed.csv`)...")

st.subheader("🤖 Autonomous Agent Action Log")
if not df.empty:
    high_risk = df[df["aqi"] > 250]
    if not high_risk.empty:
        for _, row in high_risk.iterrows():
            st.error(f"[{row['timestamp']}] Critical spike at **{row['location_id']}** (AQI: {row['aqi']}). Source: *{row['primary_source']}*. Action: Ventilation closed & parent SMS queued.")
    else:
        st.success("All monitored sectors are currently within acceptable safety thresholds.")

time.sleep(5)
st.rerun()
