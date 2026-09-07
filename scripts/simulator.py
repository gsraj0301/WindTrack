import sqlite3
import random
import time
import numpy as np
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'windtrack.db')
CYCLE_SECONDS = 10

STATUS_TRANSITIONS = {
    'Online':    {'Warning': 0.10},
    'Warning':   {'Critical': 0.20, 'Online': 0.30},
    'Critical':  {'Warning': 0.15},
}

HEALTH_RANGES = {
    'Online':   (75, 85),
    'Warning':  (50, 65),
    'Critical': (30, 49),
}

ALERT_MAP = {'Online': 'Normal', 'Warning': 'Warning', 'Critical': 'Critical'}


def get_readings(turbines):
    """Generate one reading per turbine."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rows = []
    for t in turbines:
        tid, cap, health, status = t[0], t[1], t[2], t[3]
        h_frac = health / 100.0
        kwh = cap * random.uniform(0.15, 0.40) * h_frac * random.uniform(0.85, 1.15)
        if status == 'Offline':
            kwh = 0.0
        elif status == 'Maintenance':
            kwh *= random.uniform(0.0, 0.3)

        vibration = max(random.uniform(0.1, 3.5) * (2 - h_frac) + random.gauss(0, 0.1), 0.1)
        temp = np.clip(random.uniform(35, 95) + (1 - h_frac) * 30 + random.gauss(0, 1.5), 30, 110)
        rpm = round(max(random.uniform(0, 18) * h_frac + random.gauss(0, 0.5), 0), 1) if status != 'Offline' else 0.0
        wind = max(random.uniform(3, 15) + random.gauss(0, 1), 0)

        rows.append((
            tid,
            now,
            round(vibration, 3),
            round(float(temp), 1),
            rpm,
            round(wind, 1),
            round(max(kwh, 0), 2),
            float(health),
            status,
            ALERT_MAP.get(status, 'Normal')
        ))
    return rows, now


def mutate_statuses(cursor, turbines):
    """Pick 2-4 random turbines and possibly shift their status."""
    changes = []
    sample = random.sample(turbines, min(random.randint(2, 4), len(turbines)))
    for t in sample:
        tid, _cap, _health, status = t[0], t[1], t[2], t[3]
        transitions = STATUS_TRANSITIONS.get(status, {})
        for new_status, prob in transitions.items():
            if random.random() < prob:
                new_health = random.randint(*HEALTH_RANGES[new_status])
                new_alert = ALERT_MAP[new_status]
                cursor.execute(
                    "UPDATE turbines SET health_score=?, status=?, alert_level=? WHERE turbine_id=?",
                    (new_health, new_status, new_alert, tid)
                )
                changes.append(f"{tid}: {status}→{new_status}")
                break
    return changes


def run_cycle(conn, cycle_num=0):
    """Run one simulator cycle against an open connection.

    Returns (now, num_rows, changes) where changes is a list of status-change strings.
    Caller is responsible for committing.
    """
    cursor = conn.cursor()
    turbines = cursor.execute(
        "SELECT turbine_id, capacity_kw, health_score, status FROM turbines"
    ).fetchall()

    rows, now = get_readings(turbines)
    cursor.executemany(
        "INSERT INTO live_readings (turbine_id, timestamp, vibration_g, temp_c, rpm, wind_speed_ms, kwh, health_score, status, alert_level) VALUES (?,?,?,?,?,?,?,?,?,?)",
        rows
    )

    changes = mutate_statuses(cursor, turbines)
    return now, len(rows), changes


def simulator_loop():
    """Infinite loop, run as a background daemon thread."""
    cycle = 0
    while True:
        cycle += 1
        conn = sqlite3.connect(DB_PATH, timeout=10)
        try:
            now, num_rows, changes = run_cycle(conn, cycle)
            conn.commit()
        except Exception as e:
            print(f"  Cycle {cycle:>4} | ERROR: {e}")
            conn.rollback()
        finally:
            conn.close()

        change_str = " | ".join(changes) if changes else "none"
        print(f"  Cycle {cycle:>4} | {now} | {num_rows} rows | Status changes: {change_str}")
        time.sleep(CYCLE_SECONDS)


def run():
    print("🌬️  WindTrack Simulator started (Ctrl+C to stop)")
    print(f"   DB: {DB_PATH}")
    print("-" * 50)
    try:
        simulator_loop()
    except KeyboardInterrupt:
        print("\n  Simulator stopped.")


if __name__ == '__main__':
    run()
