import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'windtrack.db')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def init_database():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turbines (
            turbine_id TEXT PRIMARY KEY,
            company TEXT,
            location TEXT,
            state TEXT,
            latitude REAL,
            longitude REAL,
            capacity_kw INTEGER,
            install_year INTEGER,
            turbine_age INTEGER,
            iot_equipped BOOLEAN,
            health_score INTEGER,
            status TEXT,
            alert_level TEXT,
            last_inspection TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS power_output (
            turbine_id TEXT,
            timestamp TEXT,
            kwh REAL,
            state TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            turbine_id TEXT,
            timestamp TEXT,
            vibration_g REAL,
            temp_c REAL,
            rpm REAL,
            wind_speed_ms REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS live_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            turbine_id TEXT,
            timestamp TEXT,
            vibration_g REAL,
            temp_c REAL,
            rpm REAL,
            wind_speed_ms REAL,
            kwh REAL,
            health_score REAL,
            status TEXT,
            alert_level TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_live_turbine_ts ON live_readings(turbine_id, timestamp)")

    conn.commit()

    for table, filename in [('turbines', 'turbines.csv'),
                             ('power_output', 'power_output.csv'),
                             ('sensor_readings', 'sensor_readings.csv')]:
        path = os.path.join(DATA_DIR, filename)
        df = pd.read_csv(path)
        df.to_sql(table, conn, if_exists='replace', index=False)
        print(f"  ✓ {table}: {len(df):,} rows loaded")

    conn.close()
    print(f"\n  Database ready at: {DB_PATH}")


if __name__ == '__main__':
    print("\n🌬️  WindTrack — Database Initialization")
    print("=" * 45)
    init_database()
