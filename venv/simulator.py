import time
import random
import pandas as pd
from datetime import datetime

# Added latitude and longitude for regional node mapping
LOCATIONS = [
    {"id": "School_Alpha", "zone": "North District", "lat": 28.6139, "lon": 77.2090, "base_aqi": 120},
    {"id": "School_Beta", "zone": "Central District", "lat": 28.5355, "lon": 77.3910, "base_aqi": 90},
    {"id": "Farm_Perimeter_01", "zone": "Rural Belt", "lat": 30.9010, "lon": 75.8573, "base_aqi": 310}
]

def generate_telemetry():
    data = []
    for loc in LOCATIONS:
        spike = random.choice([0, 0, 0, 200]) if "Rural" in loc["zone"] else random.randint(-15, 25)
        aqi = max(50, loc["base_aqi"] + spike)
        
        status = "SAFE"
        if aqi > 200:
            status = "HAZARD_WARNING"
        elif aqi > 300:
            status = "EMERGENCY_LOCKDOWN"

        data.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location_id": loc["id"],
            "zone": loc["zone"],
            "lat": loc["lat"],
            "lon": loc["lon"],
            "pm25": round(aqi * 0.8, 2),
            "aqi": aqi,
            "primary_source": "stubble_burning" if aqi > 250 else "local_traffic",
            "protocol_status": status
        })
    return pd.DataFrame(data)

if __name__ == "__main__":
    print("Starting AeroShield Mock Sensor Stream with Geolocation...")
    while True:
        df = generate_telemetry()
        df.to_csv("sensor_feed.csv", index=False)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Telemetry & Coordinates updated.")
        time.sleep(5)
