import time
import random
import pandas as pd
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# AWS S3 Configuration
AWS_BUCKET_NAME = "aeroshield-telemetry-bucket"
AWS_REGION = "us-east-1"

s3_client = boto3.client('s3', region_name=AWS_REGION)

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

def upload_to_s3(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name
    try:
        s3_client.upload_file(file_name, bucket, object_name)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ☁️ Successfully synced telemetry to AWS S3: {bucket}/{object_name}")
    except NoCredentialsError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ℹ️ [Demo Mode] Local CSV updated successfully (AWS credentials not configured).")
    except ClientError as e:
        print(f"⚠️ AWS S3 Upload error: {e}")

if __name__ == "__main__":
    print("Starting AeroShield Mock Sensor Stream with AWS S3 Pipeline...")
    while True:
        df = generate_telemetry()
        file_path = "sensor_feed.csv"
        df.to_csv(file_path, index=False)
        
        # Try syncing to AWS S3 cloud storage gracefully
        upload_to_s3(file_path, AWS_BUCKET_NAME, "live_feed/sensor_feed.csv")
        
        time.sleep(5)
