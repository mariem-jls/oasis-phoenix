import datetime
import pandas as pd

from config import WHO_THRESHOLDS_UG_M3, UG_TO_MOL, to_float, append_error_once
from services.data_loader import get_dataframe, get_latest_row
from services.model_loader import model_if, model_rf, model_ridge, scaler, scaler_ridge

RF_FEATURES = [
    'NO2_column_number_density', 'CO_column_number_density',
    'O3_column_number_density', 'absorbing_aerosol_index',
    'tropospheric_HCHO_column_number_density',
    'NDVI', 'NDWI', 'soil_moisture', 'temp',
    'so2_change_7d', 'ndvi_change_7d', 'so2_rolling_14',
    'so2_std_14', 'ndvi_rolling_14', 'temp_rolling_14',
    'season', 'anomaly_score'
]

RIDGE_FEATURES = [
    'NO2_column_number_density', 'CO_column_number_density',
    'O3_column_number_density', 'absorbing_aerosol_index',
    'tropospheric_HCHO_column_number_density',
    'NDVI', 'NDWI', 'soil_moisture', 'temp',
    'so2_change_7d', 'ndvi_change_7d', 'so2_rolling_14',
    'so2_std_14', 'ndvi_rolling_14', 'temp_rolling_14',
    'season', 'day_of_year', 'anomaly_score'
]


def compute_toxicity(so2_ug, no2_ug, o3_ug, co_ug):
    ratios = {
        'so2_ratio': to_float(so2_ug) / WHO_THRESHOLDS_UG_M3['so2'],
        'no2_ratio': to_float(no2_ug) / WHO_THRESHOLDS_UG_M3['no2'],
        'o3_ratio': to_float(o3_ug) / WHO_THRESHOLDS_UG_M3['o3'],
        'co_ratio': to_float(co_ug) / WHO_THRESHOLDS_UG_M3['co'],
    }
    worst_ratio = max(ratios.values())
    risk_score = min(100.0, worst_ratio * 100.0)

    if worst_ratio >= 2.0:
        level = 'EXTREME'
    elif worst_ratio >= 1.5:
        level = 'SEVERE'
    elif worst_ratio >= 1.0:
        level = 'TOXIC'
    elif worst_ratio >= 0.6:
        level = 'ALERTE'
    else:
        level = 'NORMAL'

    return {
        'risk_score': round(risk_score, 1),
        'level': level,
        'is_toxic': worst_ratio >= 1.0,
        'ratios': {k: round(v, 3) for k, v in ratios.items()},
    }


def soil_stress_payload(soil_moisture, ndvi, temp):
    soil_component = max(0.0, min(1.0, (0.12 - to_float(soil_moisture)) / 0.12))
    ndvi_component = max(0.0, min(1.0, (0.22 - to_float(ndvi)) / 0.22))
    temp_component = max(0.0, min(1.0, (to_float(temp) - 24.0) / 18.0))

    stress_score = 100.0 * (0.5 * soil_component + 0.35 * ndvi_component + 0.15 * temp_component)
    if stress_score >= 70:
        level = 'CRITIQUE'
        recommendation = 'Irrigation urgente + paillage + protection racinaire'
    elif stress_score >= 45:
        level = 'ALERTE'
        recommendation = 'Irrigation optimisee + surveillance humidite sol'
    else:
        level = 'STABLE'
        recommendation = 'Maintenir regime hydrique actuel'

    return {
        'stress_score': round(stress_score, 1),
        'stress_level': level,
        'recommendation': recommendation,
    }


def safe_predict_ndvi_30d(row):
    if model_ridge is None or scaler_ridge is None:
        return to_float(row.get('NDVI', 0.0))

    missing = [c for c in RIDGE_FEATURES if c not in row.index]
    if missing:
        return to_float(row.get('NDVI', 0.0))

    try:
        x = pd.DataFrame([{c: to_float(row[c]) for c in RIDGE_FEATURES}])
        return float(model_ridge.predict(scaler_ridge.transform(x))[0])
    except Exception as exc:
        append_error_once(f"Prediction fallback used: {exc}")
        return to_float(row.get('NDVI', 0.0))


def run_ai_on_live(zone_name, so2_ug, no2_ug, co_ug, o3_ug):
    frame = get_dataframe()
    row = get_latest_row(frame)

    no2_mol = no2_ug * UG_TO_MOL['no2']
    co_mol = co_ug * UG_TO_MOL['co']
    o3_mol = o3_ug * UG_TO_MOL['o3']
    so2_mol = so2_ug * UG_TO_MOL['so2']

    month = datetime.datetime.now().month
    season = {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}[month]

    ndvi = to_float(row.get('NDVI', 0.15)) if row is not None else 0.15
    ndwi = to_float(row.get('NDWI', 0.10)) if row is not None else 0.10
    soil = to_float(row.get('soil_moisture', 0.03)) if row is not None else 0.03
    temp = to_float(row.get('temp', 22.0)) if row is not None else 22.0
    hcho = to_float(row.get('tropospheric_HCHO_column_number_density', 0.0)) if row is not None else 0.0
    aer = to_float(row.get('absorbing_aerosol_index', 0.0)) if row is not None else 0.0
    anom_sc = to_float(row.get('anomaly_score', -0.5)) if row is not None else -0.5
    so2_chg = so2_mol - to_float(row.get('so2_rolling_14', so2_mol)) if row is not None else 0.0
    ndvi_chg = to_float(row.get('ndvi_change_7d', 0.0)) if row is not None else 0.0
    so2_roll = to_float(row.get('so2_rolling_14', so2_mol)) if row is not None else so2_mol
    so2_std = to_float(row.get('so2_std_14', 0.0)) if row is not None else 0.0

    features = {
        'NO2_column_number_density': no2_mol,
        'CO_column_number_density': co_mol,
        'O3_column_number_density': o3_mol,
        'absorbing_aerosol_index': aer,
        'tropospheric_HCHO_column_number_density': hcho,
        'NDVI': ndvi,
        'NDWI': ndwi,
        'soil_moisture': soil,
        'temp': temp,
        'so2_change_7d': so2_chg,
        'ndvi_change_7d': ndvi_chg,
        'so2_rolling_14': so2_roll,
        'so2_std_14': so2_std,
        'ndvi_rolling_14': ndvi,
        'temp_rolling_14': temp,
        'season': season,
        'anomaly_score': anom_sc,
    }

    result = {
        'zone': zone_name,
        'is_anomaly': False,
        'anomaly_label': 'NORMAL',
        'anomaly_score': anom_sc,
        'cause': 'NORMAL',
        'cause_proba': 0.0,
        'risk_score': 0.0,
        'risk_level': '🟢 SAINE',
        'current_ndvi': round(ndvi, 4),
        'ndvi_predicted_30d': round(ndvi, 4),
        'ndvi_trend': 'stable',
        'so2_mol_m2': round(so2_mol, 10),
    }

    try:
        if model_if is not None and scaler is not None:
            x_if = pd.DataFrame([{c: features.get(c, 0.0) for c in RF_FEATURES}])
            x_scaled = scaler.transform(x_if)
            pred = model_if.predict(x_scaled)[0]
            score = float(model_if.score_samples(x_scaled)[0])
            result['is_anomaly'] = pred == -1
            result['anomaly_score'] = round(score, 4)
            result['anomaly_label'] = f'ANOMALIE SO2 — {zone_name}' if pred == -1 else 'NORMAL'
            features['anomaly_score'] = score
    except Exception as exc:
        append_error_once(f"IF error {zone_name}: {exc}")

    try:
        if model_rf is not None:
            x_rf = pd.DataFrame([{c: features.get(c, 0.0) for c in RF_FEATURES}])
            result['cause'] = model_rf.predict(x_rf)[0]
            result['cause_proba'] = round(float(model_rf.predict_proba(x_rf).max()), 2)
    except Exception as exc:
        append_error_once(f"RF error {zone_name}: {exc}")

    try:
        if model_ridge is not None and scaler_ridge is not None:
            x_rg = pd.DataFrame([{c: features.get(c, 0.0) for c in RIDGE_FEATURES}])
            x_rg_s = scaler_ridge.transform(x_rg)
            result['ndvi_predicted_30d'] = round(float(model_ridge.predict(x_rg_s)[0]), 4)
    except Exception as exc:
        append_error_once(f"Ridge error {zone_name}: {exc}")

    so2_score = min(100, (so2_mol / 0.001) * 100)
    ndvi_score = min(100, max(0, (0.22 - ndvi) / 0.22 * 100))
    anom_bonus = 20 if result['is_anomaly'] else 0
    risk = min(100, so2_score * 0.5 + ndvi_score * 0.3 + anom_bonus)
    result['risk_score'] = round(risk, 1)
    result['risk_level'] = '🔴 CRITIQUE' if risk >= 70 else '🟡 DÉGRADÉE' if risk >= 40 else '🟢 SAINE'
    pred_ndvi = to_float(result.get('ndvi_predicted_30d', ndvi))
    if pred_ndvi > ndvi:
        result['ndvi_trend'] = 'improving'
    elif pred_ndvi < ndvi:
        result['ndvi_trend'] = 'degrading'
    else:
        result['ndvi_trend'] = 'stable'

    return result
