import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_base_dir():
    env_base = os.getenv('OASIS_PHOENIX_BASE_DIR', '').strip()
    if env_base:
        return os.path.abspath(env_base)
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
    {'name': 'Ghannouch',         'lat': 33.95, 'lon': 10.05},
    {'name': 'Gabes Medina',      'lat': 33.89, 'lon': 10.10},
    {'name': 'Gabes Ouest',       'lat': 33.90, 'lon': 10.03},
    {'name': 'Gabes Sud',         'lat': 33.85, 'lon': 10.09},
    {'name': 'Mareth',            'lat': 33.72, 'lon': 10.15},
    {'name': 'El Hamma',          'lat': 33.92, 'lon': 9.87},
    {'name': 'Metouia',           'lat': 34.03, 'lon': 9.97},
    {'name': 'Menzel El Habib',   'lat': 33.70, 'lon': 9.68},
    {'name': 'Matmata',           'lat': 33.47, 'lon': 9.83},
    {'name': 'Nouvelle Matmata',  'lat': 33.50, 'lon': 10.03},
    {'name': 'El Ogla',           'lat': 33.65, 'lon': 10.17},
    {'name': 'Ouedhref',          'lat': 33.28, 'lon': 9.93},
    {'name': 'Smar',              'lat': 33.81, 'lon': 10.11},
    {'name': 'Zone Industrielle', 'lat': 33.93, 'lon': 10.07},
    {'name': 'Oued Gabes',        'lat': 33.88, 'lon': 10.08},
    {'name': 'Chenini Nahal',     'lat': 33.78, 'lon': 10.02},
    {'name': 'Kettana',           'lat': 33.82, 'lon': 9.98},
    {'name': 'El Akarit',         'lat': 34.08, 'lon': 10.08},
    {'name': 'El Metouia Coast',  'lat': 34.00, 'lon': 10.12},
    {'name': 'Bou Attouche',      'lat': 33.72, 'lon': 9.88},
    {'name': 'Chott El Fejij',    'lat': 33.65, 'lon': 9.75},
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
