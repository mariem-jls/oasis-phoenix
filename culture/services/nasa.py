import requests
import numpy as np

def get_nasa(lat: float, lon: float) -> dict:
    """
    NASA POWER API — radiation solaire + NDVI proxy
    Gratuit, sans clé API
    """
    url    = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,GWETROOT",
        "community":  "AG",
        "longitude":  lon,
        "latitude":   lat,
        "start":      "20220101",
        "end":        "20241231",
        "format":     "JSON"
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        p     = r.json()["properties"]["parameter"]
        rad   = np.array(list(p.get("ALLSKY_SFC_SW_DWN", {}).values()))
        moist = np.array(list(p.get("GWETROOT", {}).values()))
        rad   = rad[rad > 0]
        moist = moist[moist >= 0]

        rad_n   = float(np.clip((rad.mean()   - 2) / 6, 0, 1)) if len(rad)   else 0.5
        moist_n = float(moist.mean())                           if len(moist) else 0.3
        ndvi    = round(float(np.clip(0.35 * rad_n + 0.45 * moist_n, 0.02, 0.60)), 3)

        return {
            "radiation": round(float(rad.mean()), 2) if len(rad) else 5.5,
            "ndvi":      ndvi,
            "source":    "NASA POWER"
        }
    except Exception as e:
        print(f"[NASA POWER] fallback : {e}")
        return {
            "radiation": 5.5,
            "ndvi":      0.20,
            "source":    "default"
        }