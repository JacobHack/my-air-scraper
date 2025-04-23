import os
import requests
import psycopg2
from datetime import datetime, timedelta
from psycopg2.extras import Json

LAT = 44.9369
LON = -123.0280
START = datetime(2025, 4, 3, 2)
END = datetime(2025, 4, 20, 19)
API_KEY = os.getenv("API_KEY")
DB_URL = os.getenv("DB_URL")
URL = "http://api.openweathermap.org/data/2.5/air_pollution/history"

def get_data(start, end):
    params = {
        "lat": LAT,
        "lon": LON,
        "start": int(start.timestamp()),
        "end": int(end.timestamp()),
        "appid": API_KEY
    }
    response = requests.get(URL, params=params)
    response.raise_for_status()
    return response.json()

def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Ensure location exists
    cur.execute("""
        INSERT INTO locations (latitude, longitude)
        VALUES (%s, %s)
        ON CONFLICT (latitude, longitude) DO NOTHING
        RETURNING location_id;
    """, (LAT, LON))
    loc_id = cur.fetchone()
    if loc_id is None:
        cur.execute("SELECT location_id FROM locations WHERE latitude=%s AND longitude=%s", (LAT, LON))
        loc_id = cur.fetchone()
    loc_id = loc_id[0]

    # Insert component names if not already in DB
    component_names = ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"]
    for name in component_names:
        cur.execute("""
            INSERT INTO components (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING;
        """, (name,))
    conn.commit()

    current = START
    while current <= END:
        end_time = current + timedelta(hours=1)
        print(f"Fetching: {current} to {end_time}")

        try:
            data = get_data(current, end_time)
            if "list" in data:
                for entry in data["list"]:
                    dt = datetime.utcfromtimestamp(entry["dt"])
                    aqi = entry["main"]["aqi"]
                    components = entry["components"]

                    # Insert into raw_air_data
                    cur.execute("""
                        INSERT INTO raw_air_data (location, air_data)
                        VALUES (%s, %s);
                    """, (Json({"lat": LAT, "lon": LON}), Json(entry)))

                    # Insert into air_quality_readings
                    cur.execute("""
                        INSERT INTO air_quality_readings (location_id, datetime, aqi)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (location_id, datetime) DO NOTHING
                        RETURNING reading_id;
                    """, (loc_id, dt, aqi))
                    reading = cur.fetchone()
                    if reading:
                        reading_id = reading[0]
                        for name, value in components.items():
                            cur.execute("""
                                SELECT component_id FROM components WHERE name = %s;
                            """, (name,))
                            component_id = cur.fetchone()[0]
                            cur.execute("""
                                INSERT INTO reading_components (reading_id, component_id, value)
                                VALUES (%s, %s, %s);
                            """, (reading_id, component_id, value))
            conn.commit()
        except Exception as e:
            print(f"Error fetching data for {current}: {e}")
            conn.rollback()

        current += timedelta(hours=1)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
