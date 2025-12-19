import requests
import time
import random

API_URL = "http://localhost:3000/ingest"

def generate_sensor_data():
    # 5% chance of a "Critical Failure" or "Cyber Attack"
    is_attack = random.random() > 0.95 
    
    if is_attack:
        # A hacked sensor sends impossible or dangerous values
        value = random.uniform(5.0, 10.0) # Normal is 0.1 to 0.4
        print(f"⚠️  SIMULATING ATTACK: Sending rogue value {value}")
    else:
        value = round(random.uniform(0.1, 0.4), 4)

    return {
        "sensor_id": f"SENSOR-{random.randint(1, 5)}",
        "sensor_type": "Traffic",
        "value": value,
        "location": {"lat": 40.7128, "lon": -74.0060},
        "timestamp": int(time.time())
    }
print("📡 Simulation started. Sending data to Rust...")
while True:
    try:
        data = generate_sensor_data()
        requests.post(API_URL, json=data)
        print(f"Sent: {data['sensor_id']} | Value: {data['value']}")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(1)