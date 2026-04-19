import requests

def get_soil(lat: float, lon: float) -> dict:
    """
    SoilGrids REST API — pH + salinité estimée
    Gratuit, sans clé API
    """
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon":      lon,
        "lat":      lat,
        "property": ["phh2o", "cec", "bdod"],
        "depth":    ["0-5cm"],
        "value":    ["mean"]
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        layers = r.json()["properties"]["layers"]
        vals   = {}
        for lyr in layers:
            mean = lyr["depths"][0]["values"].get("mean")
            if mean is not None:
                vals[lyr["name"]] = mean

        ph       = vals.get("phh2o", 75)  / 10.0
        cec      = vals.get("cec",   200) / 10.0
        bdod     = vals.get("bdod",  130) / 100.0
        salinite = round(max(1.0, cec / 18.0), 2)

        if   bdod < 1.3: depth_cat = "D"
        elif bdod < 1.5: depth_cat = "M"
        else:            depth_cat = "S"

        return {
            "pH":        round(ph, 2),
            "salinite":  salinite,
            "depth_cat": depth_cat,
            "source":    "SoilGrids"
        }
    except Exception as e:
        print(f"[SoilGrids] fallback : {e}")
        return {
            "pH":        7.8,
            "salinite":  4.2,
            "depth_cat": "M",
            "source":    "default"
        }