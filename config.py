import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEGACY_BASE_DIR = r'C:\Users\Nebrasse\Desktop\Ai-Healing-Gabes\oasis_phoenix'


def resolve_base_dir():
    local_data = os.path.join(BASE_DIR, 'data', 'combined_clean.csv')
    local_models = os.path.join(BASE_DIR, 'models')
    if os.path.exists(local_data) and os.path.isdir(local_models):
        return BASE_DIR

    legacy_data = os.path.join(LEGACY_BASE_DIR, 'data', 'combined_clean.csv')
    legacy_models = os.path.join(LEGACY_BASE_DIR, 'models')
    if os.path.exists(legacy_data) and os.path.isdir(legacy_models):
        return LEGACY_BASE_DIR

    return BASE_DIR


ACTIVE_BASE_DIR = resolve_base_dir()
DATA_PATH = os.path.join(ACTIVE_BASE_DIR, 'data', 'combined_clean.csv')
MODELS_DIR = os.path.join(ACTIVE_BASE_DIR, 'models')

DATA_REFRESH_SECONDS = 10
LIVE_REFRESH_SECONDS = 180
AIR_QUALITY_API = 'https://air-quality-api.open-meteo.com/v1/air-quality'

WHO_THRESHOLDS_UG_M3 = {
    'so2': 40.0,
    'no2': 25.0,
    'o3': 100.0,
    'co': 4000.0,
}

ZONES = [
    {'name': 'Ghannouch', 'lat': 33.95, 'lon': 10.05},
    {'name': 'Gabes Medina', 'lat': 33.89, 'lon': 10.10},
    {'name': 'Gabes Ouest', 'lat': 33.90, 'lon': 10.03},
    {'name': 'Gabes Sud', 'lat': 33.85, 'lon': 10.09},
    {'name': 'Mareth', 'lat': 33.72, 'lon': 10.15},
    {'name': 'El Hamma', 'lat': 33.92, 'lon': 9.87},
    {'name': 'Metouia', 'lat': 34.03, 'lon': 9.97},
    {'name': 'Menzel El Habib', 'lat': 33.70, 'lon': 9.68},
    {'name': 'Matmata', 'lat': 33.47, 'lon': 9.83},
    {'name': 'Nouvelle Matmata', 'lat': 33.50, 'lon': 10.03},
    {'name': 'El Ogla', 'lat': 33.65, 'lon': 10.17},
    {'name': 'Ouedhref', 'lat': 33.28, 'lon': 9.93},
    {'name': 'Smar', 'lat': 33.81, 'lon': 10.11},
]

UG_TO_MOL = {
    'so2': 1e-6 / 64.0 * 1000,
    'no2': 1e-6 / 46.0 * 1000,
    'co': 1e-6 / 28.0 * 1000,
    'o3': 1e-6 / 48.0 * 1000,
}

APP_ERRORS = []


def append_error_once(message):
    if message not in APP_ERRORS:
        APP_ERRORS.append(message)


def to_float(value, default=0.0):
    try:
        if pd.isna(value):
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def to_text(value, default='N/A'):
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    return str(value)
