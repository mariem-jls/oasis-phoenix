import os
import time
import pandas as pd

from config import DATA_PATH, DATA_REFRESH_SECONDS, append_error_once

_DF_CACHE = pd.DataFrame()
_DF_CACHE_MTIME = None
_DF_CACHE_LAST_CHECK = 0.0


def load_dataframe():
    if not os.path.exists(DATA_PATH):
        append_error_once(f"Missing dataset file: {DATA_PATH}")
        return pd.DataFrame()

    try:
        loaded_df = pd.read_csv(DATA_PATH)
    except Exception as exc:
        append_error_once(f"Failed to read dataset: {exc}")
        return pd.DataFrame()

    if 'date' in loaded_df.columns:
        loaded_df['date'] = pd.to_datetime(loaded_df['date'], errors='coerce')
        loaded_df = loaded_df.dropna(subset=['date']).sort_values('date').reset_index(drop=True)

    return loaded_df


def get_dataframe(force=False):
    global _DF_CACHE, _DF_CACHE_MTIME, _DF_CACHE_LAST_CHECK

    now = time.time()
    should_recheck = force or _DF_CACHE.empty or (now - _DF_CACHE_LAST_CHECK >= DATA_REFRESH_SECONDS)
    if not should_recheck:
        return _DF_CACHE

    _DF_CACHE_LAST_CHECK = now

    try:
        current_mtime = os.path.getmtime(DATA_PATH)
    except OSError:
        current_mtime = None

    should_reload = force or _DF_CACHE.empty or (current_mtime != _DF_CACHE_MTIME)
    if should_reload:
        _DF_CACHE = load_dataframe()
        _DF_CACHE_MTIME = current_mtime

    return _DF_CACHE


def ensure_columns(frame, columns):
    for col, default in columns.items():
        if col not in frame.columns:
            frame[col] = default
    return frame


def get_latest_row(frame):
    if frame.empty:
        return None

    required = {
        'SO2_column_number_density': 0.0,
        'NO2_column_number_density': 0.0,
        'CO_column_number_density': 0.0,
        'O3_column_number_density': 0.0,
        'absorbing_aerosol_index': 0.0,
        'tropospheric_HCHO_column_number_density': 0.0,
        'NDVI': 0.0,
        'NDWI': 0.0,
        'temp': 0.0,
        'soil_moisture': 0.0,
        'risk_level': 'N/A',
        'health_risk_index': 0.0,
        'phoenix_statut': 'N/A',
        'phoenix_plante': 'N/A',
        'phoenix_revenu': 'N/A',
        'phoenix_carbone': 'N/A',
        'phoenix_delai': 'N/A',
        'phoenix_action': 'N/A',
        'cause': 'N/A',
    }

    working = ensure_columns(frame.copy(), required)
    valid = working[(working['NDVI'] >= -1.0) & (working['NDVI'] <= 1.0)]
    valid_non_zero_so2 = valid[valid['SO2_column_number_density'] > 0]

    if not valid_non_zero_so2.empty:
        return valid_non_zero_so2.iloc[-1]
    if not valid.empty:
        return valid.iloc[-1]
    return working.iloc[-1]
