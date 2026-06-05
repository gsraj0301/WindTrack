import pandas as pd
import numpy as np
from faker import Faker
import os
import random
from datetime import datetime, timedelta

fake = Faker("en_IN")
random.seed(42)
np.random.seed(42)

# Config 
NUM_TURBINES = 100
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 12, 31)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


# REFERENCE DATA
COMPANIES = {
    'Envision': {'share': 0.30, 'capacity_range': (2000, 3000)},
    'Suzlon': {'share': 0.25, 'capacity_range': (1500, 2100)},
    'Inox Wind': {'share': 0.20, 'capacity_range': (2000, 3000)},
    'Vestas': {'share': 0.15, 'capacity_range': (2500, 3600)},
    'GE Renewable': {'share': 0.10, 'capacity_range': (2000, 2750)}
    
    }
ZONES = [
    ('Tamil Nadu', 'TN', ['Tirunelveli', 'Coimbatore', 'Theni', 'Dindigul']),
    ('Gujarat', 'GJ', ['Kutch', 'Rajkot', 'Bhavnagar', 'Jamnagar']),
    ('Rajasthan', 'RJ', ['Jaisalmer', 'Barmer', 'Jodhpur']),
    ('Karnataka', 'KA', ['Gadag', 'Chitradurga', 'Davangere']),
    ('Maharashtra', 'MH', ['Satara', 'Sangli', 'Kolhapur']),
]

GPS_BOUNDS = {
    'TN': [8.0,  13.5, 76.5, 80.5],
    'GJ': [21.0, 24.5, 68.5, 74.0],
    'RJ': [25.0, 29.0, 69.0, 76.5],
    'KA': [13.0, 15.5, 74.5, 78.0],
    'MH': [16.5, 18.5, 73.5, 76.5],
}

def pick_company():
    companies = list(COMPANIES.keys())
    weights = [COMPANIES[c]['share'] for c in companies]
    return random.choices(companies, weights=weights, k=1)[0]

def random_gps(state_code):
    b = GPS_BOUNDS[state_code]
    lat = round(random.uniform(b[0], b[1]), 6)
    lon = round(random.uniform(b[2], b[3]), 6)
    return lat, lon

# STEP 1 : TURBINE MODEL
def generate_turbine():
    print("Generating turbines...")
    rows=[]

    for i in range(1, NUM_TURBINES+1):
        turbine_id = f"WT-{i:03d}"
        company = pick_company()
        cap_min, cap_max = COMPANIES[company]['capacity_range']
        capacity_kw = random.randint(cap_min, cap_max)

        # Pick zone weighted by wind resource

        state_name, state_code, locations = random.choices(ZONES, weights =[0.30, 0.25, 0.20,0.15, 0.10],
                                                           k=1)[0]
        location = random.choice(locations)
        lat, lon = random_gps(state_code)

        install_year = random.randint(2015, 2023)
        turbine_age = 2024 - install_year

        # Older turbines less likely to have IOT
        iot_probability = 0.85 if turbine_age <= 5 else (0.50 if turbine_age <= 10 else 0.20)
        iot_equipped = random.random() < iot_probability
        base_health = 90 -(turbine_age * 1.5)
        health_score = int(np.clip(
            base_health + random.uniform(-10, 10), 20, 100))
        
        # Status based in health
        if health_score >= 75:
            status = 'Online'
        elif health_score >= 50:
            status = random.choices(['Online', 'Maintenance'], weights=[0.7, 0.3])[0]
        else:
            status = random.choices(['Maintenance', 'Offline'], weights=[0.6, 0.4])[0]

        # Alert level
        if health_score >= 80:
            alert = 'Normal'
        elif health_score >= 60:
            alert = 'Warning'
        else:
            alert = 'Critical'
        last_inspection = START_DATE + timedelta(days=random.randint(10, 365))


        rows.append({
            'turbine_id':      turbine_id,
            'company':         company,
            'location':        location,
            'state':           state_name,
            'latitude':        lat,
            'longitude':       lon,
            'capacity_kw':     capacity_kw,
            'install_year':    install_year,
            'turbine_age':     turbine_age,
            'iot_equipped':    iot_equipped,
            'health_score':    health_score,
            'status':          status,
            'alert_level':     alert,
            'last_inspection': last_inspection.strftime('%Y-%m-%d'),
        })

    df = pd.DataFrame(rows)
    path=os.path.join(OUTPUT_DIR, 'turbines.csv')
    df.to_csv(path, index=False)
    print(f"  ✓ {len(df)} turbines saved → {path}")
    return df

# STEP 2 : POWER OUTPUT TABLE
def generate_power_output(turbines_df):
    print("Generating power output (hourly × 100 turbines × 365 days)...")
    print("  This takes ~15 seconds, please wait...")

    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq='30min')
    all_rows = []

    for _, turbine in turbines_df.iterrows():
        tid      = turbine['turbine_id']
        cap      = turbine['capacity_kw']
        health   = turbine['health_score'] / 100
        status   = turbine['status']
        state    = turbine['state']

        # Wind seasonality: better in certain months for certain states
        seasonal_boost = {
            'Tamil Nadu':  [1.0, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.4, 1.2, 1.0, 1.0, 1.0],
            'Gujarat':     [1.1, 1.0, 1.0, 1.1, 1.3, 1.5, 1.6, 1.5, 1.3, 1.0, 1.0, 1.1],
            'Rajasthan':   [1.0, 1.0, 1.1, 1.2, 1.4, 1.5, 1.5, 1.4, 1.2, 1.0, 0.9, 1.0],
            'Karnataka':   [1.0, 1.0, 1.1, 1.2, 1.3, 1.4, 1.4, 1.3, 1.1, 1.0, 1.0, 1.0],
            'Maharashtra': [1.0, 1.0, 1.1, 1.2, 1.3, 1.5, 1.5, 1.4, 1.2, 1.0, 1.0, 1.0],
        }

        for ts in date_range:
            month_idx = ts.month - 1
            hour      = ts.hour

            # Daytime wind is stronger
            hour_factor = 0.6 + 0.4 * np.sin(np.pi * (hour - 6) / 12) if 6 <= hour <= 18 else 0.4

            season_factor = seasonal_boost[state][month_idx]

            # Base output = capacity × utilization × health × factors + noise
            base_utilization = random.uniform(0.20, 0.45)
            kwh = (
                cap
                * base_utilization
                * health
                * hour_factor
                * season_factor
                * random.uniform(0.85, 1.15)  # noise
            )

            # Offline turbines produce nothing; maintenance produces little
            if status == 'Offline':
                kwh = 0.0
            elif status == 'Maintenance':
                kwh *= random.uniform(0.0, 0.3)

            all_rows.append({
                'turbine_id': tid,
                'timestamp':  ts,
                'kwh':        round(max(kwh, 0), 2),
                'state':      state,
            })

    df = pd.DataFrame(all_rows)
    path = os.path.join(OUTPUT_DIR, 'power_output.csv')
    df.to_csv(path, index=False)
    print(f"  ✓ {len(df):,} rows saved → {path}")
    return df

# STEP 3 : SENSOR READINGS
def generate_sensor_readings(turbines_df):
    print("Generating sensor readings (hourly × 100 turbines × 365 days)...")
    print("  This takes ~15 seconds, please wait...")

    iot_turbines = turbines_df[turbines_df['iot_equipped'] == True]
    print(f" IOT-equipped turbines: {len(iot_turbines)}")

    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq='30min')
    all_rows = []

    for _, turbine in iot_turbines.iterrows():
        tid = turbine['turbine_id']
        health = turbine['health_score'] / 100
        status = turbine['status']
        for ts in date_range:
            # Degrade sensors as health drops
            vibration   = round(random.uniform(0.5, 2.0) * (2 - health) + random.gauss(0, 0.1), 3)
            temperature = round(random.uniform(40, 75) + (1 - health) * 30 + random.gauss(0, 1.5), 1)
            rpm         = round(random.uniform(8, 18) * health + random.gauss(0, 0.5), 1) if status != 'Offline' else 0.0
            wind_speed  = round(random.uniform(4, 15) + random.gauss(0, 1), 1)

            # Clamp values to realistic ranges
            vibration   = max(vibration, 0.1)
            temperature = np.clip(temperature, 30, 110)
            rpm         = max(rpm, 0)
            wind_speed  = max(wind_speed, 0)

            all_rows.append({
                'turbine_id':  tid,
                'timestamp':   ts,
                'vibration_g': vibration,
                'temp_c':      temperature,
                'rpm':         rpm,
                'wind_speed_ms': wind_speed,
            })
    df = pd.DataFrame(all_rows)
    path = os.path.join(OUTPUT_DIR, 'sensor_readings.csv')
    df.to_csv(path, index=False)
    print(f"  ✓ {len(df):,} rows saved → {path}")
    return df

# MAIN
if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("\n🌬️  WindTrack — Synthetic Data Generator")
    print("=" * 45)

    turbines_df = generate_turbine()
    power_df    = generate_power_output(turbines_df)
    sensor_df   = generate_sensor_readings(turbines_df)

    print("\n✅ All data generated successfully!")
    print(f"   Turbines       : {len(turbines_df)} rows")
    print(f"   Power Output   : {len(power_df):,} rows")
    print(f"   Sensor Readings: {len(sensor_df):,} rows")
    print(f"\n   Files in: windtrack/data/")