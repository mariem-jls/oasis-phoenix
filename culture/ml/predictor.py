import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# Chemins vers les modèles
BASE_DIR   = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"

# Chargement unique au démarrage
_rf       = None
_scaler   = None
_le       = None
_features = None
_mapping  = None

def _load():
    global _rf, _scaler, _le, _features, _mapping
    if _rf is None:
        print("[Predictor] Chargement modèles...")
        _rf       = joblib.load(MODELS_DIR / "model_rf.pkl")
        _scaler   = joblib.load(MODELS_DIR / "scaler.pkl")
        _le       = joblib.load(MODELS_DIR / "label_encoder.pkl")
        _features = joblib.load(MODELS_DIR / "features_list.pkl")
        _mapping  = pd.read_csv(MODELS_DIR / "scientname_to_name.csv")
        print(f"[Predictor] ✓ {len(_le.classes_)} plantes chargées")

def predict(soil: dict, climat: dict, nasa: dict, top_n: int = 5) -> list:
    """
    Prédit les top_n plantes recommandées pour une parcelle.

    Paramètres :
        soil   : {pH, salinite, depth_cat}
        climat : {T_max, T_min, precip, moisture}
        nasa   : {radiation, ndvi}
        top_n  : nombre de recommandations

    Retourne :
        liste de dicts {scientname, name, confiance_pct}
    """
    _load()

    # Convertir depth_cat en numérique
    DEPTH_ORDER = {"S": 1, "M": 2, "D": 3}
    depth_num   = DEPTH_ORDER.get(soil.get("depth_cat", "M"), 2)

    # Convertir radiation → luminosité FAO (1-5)
    rad = nasa.get("radiation", 5.5)
    if   rad >= 18: lig = 4
    elif rad >= 14: lig = 3
    elif rad >= 10: lig = 2
    else:           lig = 1

    pH      = soil.get("pH",      7.5)
    sal     = soil.get("salinite", 4.0)
    T_max   = climat.get("T_max",  32.5)
    T_min   = climat.get("T_min",   4.0)
    precip  = climat.get("precip", 185.0)

    # Construire le vecteur — même format que l'entraînement FAO
    # Features : plages FAO reconstituées depuis valeurs ponctuelles
    vector = {
        "pH_min":         pH,
        "pH_opt_low":     pH,
        "pH_opt_high":    pH,
        "pH_max":         pH,
        "T_min":          T_min,
        "T_opt_low":      T_min + (T_max - T_min) * 0.3,
        "T_opt_high":     T_min + (T_max - T_min) * 0.8,
        "T_max":          T_max,
        "T_gel":          min(T_min - 2, 0),
        "prec_min":       precip,
        "prec_opt_low":   precip,
        "prec_opt_high":  precip,
        "prec_max":       precip,
        "sal_max_dsm":    int(sal),
        "lig_min":        lig,
        "lig_max":        lig,
        "dep_min":        depth_num,
        "dep_max":        depth_num,
        "fer_min":        2,
        "fer_max":        2,
        "dra_min":        1,
        "dra_max":        2,
        "photoperiode_num": 1,
        "pp_min":         12,
        "pp_max":         14,
        "duration_min":   90,
        "duration_max":   365,
    }

    X     = np.array([[vector[f] for f in _features]])
    X_sc  = _scaler.transform(X)
    proba = _rf.predict_proba(X_sc)[0]

    # Top N
    top_idx = proba.argsort()[-top_n:][::-1]
    results = []
    for idx in top_idx:
        sci  = _le.inverse_transform([idx])[0]
        conf = round(float(proba[idx]) * 100, 1)
        nom  = _mapping[_mapping["SCIENTNAME"] == sci]["NAME"].values
        nom  = nom[0] if len(nom) > 0 else sci
        results.append({
            "scientname":   sci,
            "name":         nom,
            "confiance_pct": conf
        })

    return results