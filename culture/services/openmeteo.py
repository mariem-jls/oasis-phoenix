import requests
import pandas as pd

def get_climate(lat: float, lon: float) -> dict:
    """
    Open-Meteo Archive API — moyenne sur 3 ans pour robustesse
    Gratuit, sans clé API
    """
    annees = [
        ("2022-01-01", "2022-12-31"),
        ("2023-01-01", "2023-12-31"),
        ("2024-01-01", "2024-12-31"),
    ]
    all_data = []

    for start, end in annees:
        url    = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude":   lat,
            "longitude":  lon,
            "start_date": start,
            "end_date":   end,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "soil_moisture_0_to_7cm_mean"
            ],
            "timezone": "auto"
        }
        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            d = pd.DataFrame(r.json()["daily"])
            all_data.append(d)
        except Exception as e:
            print(f"[Open-Meteo] {start[:4]} fallback : {e}")
            continue

    if not all_data:
        return {
            "T_max":    32.5,
            "T_min":    4.2,
            "precip":   185.0,
            "moisture": 0.09,
            "source":   "default"
        }

    df_all = pd.concat(all_data, ignore_index=True)

    return {
        "T_max":    round(float(df_all["temperature_2m_max"].mean()), 1),
        "T_min":    round(float(df_all["temperature_2m_min"].min()),  1),
        "precip":   round(float(df_all["precipitation_sum"].sum()) / len(annees), 1),
        "moisture": round(float(df_all["soil_moisture_0_to_7cm_mean"].mean()), 4),
        "source":   "Open-Meteo"
    }