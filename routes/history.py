from flask import Blueprint, jsonify, request
import pandas as pd

from config import ACTIVE_BASE_DIR, APP_ERRORS, AIR_QUALITY_API, LIVE_REFRESH_SECONDS, ZONES, to_float, to_text
from services.data_loader import get_dataframe, get_latest_row
from services.model_loader import model_if, model_rf, model_ridge, scaler, scaler_ridge

history_bp = Blueprint('history', __name__)


@history_bp.route('/api/anomalies')
def anomalies():
    frame = get_dataframe()
    if frame.empty:
        return jsonify([])

    if 'is_anomaly' not in frame.columns or 'anomaly_score' not in frame.columns:
        return jsonify([])

    anom = frame[frame['is_anomaly'] == 1].copy()
    cause_filter = to_text(request.args.get('cause', ''), '').strip()
    if cause_filter:
        anom = anom[anom['cause'].astype(str).str.upper() == cause_filter.upper()]

    anom = anom[
        (anom['NDVI'] > 0) &
        (anom['NDVI'] <= 1) &
        (anom['SO2_column_number_density'] > 0)
    ]

    recent_days = int(to_float(request.args.get('recent_days', 365), 365))
    if recent_days > 0 and not anom.empty and 'date' in anom.columns:
        dates = pd.to_datetime(anom['date'], errors='coerce')
        if dates.notna().any():
            cutoff = dates.max() - pd.Timedelta(days=recent_days)
            anom = anom[dates >= cutoff]

    if anom.empty:
        anom = frame[frame['is_anomaly'] == 1].copy()
        anom = anom[
            (anom['NDVI'] > 0) &
            (anom['NDVI'] <= 1) &
            (anom['SO2_column_number_density'] > 0)
        ]

    anom = anom.nsmallest(20, 'anomaly_score').copy()
    if anom.empty:
        return jsonify([])

    if 'date' in anom.columns:
        anom['date'] = anom['date'].astype(str)

    cols = [
        'date', 'SO2_column_number_density', 'NDVI',
        'anomaly_score', 'cause', 'risk_level', 'health_risk_index'
    ]
    return jsonify(anom[cols].to_dict(orient='records'))


@history_bp.route('/api/history')
def history():
    frame = get_dataframe()
    if frame.empty:
        return jsonify([])

    cols = [
        'date', 'SO2_column_number_density', 'NDVI',
        'NO2_column_number_density', 'CO_column_number_density',
        'O3_column_number_density', 'absorbing_aerosol_index',
        'NDWI', 'temp', 'soil_moisture', 'health_risk_index',
        'risk_level', 'cause', 'phoenix_statut', 'phoenix_plante',
        'phoenix_revenu', 'phoenix_carbone', 'phoenix_delai',
        'phoenix_action'
    ]
    sample = frame[[c for c in cols if c in frame.columns]].copy()
    sample['date'] = sample['date'].astype(str)
    return jsonify(sample.to_dict(orient='records'))


@history_bp.route('/api/stats')
def stats():
    frame = get_dataframe()
    if frame.empty:
        return jsonify({
            'total_days': 0,
            'date_from': 'N/A',
            'date_to': 'N/A',
            'anomaly_days': 0,
            'critical_days': 0,
            'degraded_days': 0,
            'healthy_days': 0,
            'avg_so2': 0.0,
            'avg_ndvi': 0.0,
            'source': ACTIVE_BASE_DIR,
            'issues': APP_ERRORS,
        })

    return jsonify({
        'total_days': len(frame),
        'date_from': str(frame['date'].min().date()) if 'date' in frame.columns else 'N/A',
        'date_to': str(frame['date'].max().date()) if 'date' in frame.columns else 'N/A',
        'anomaly_days': int(frame['is_anomaly'].sum()) if 'is_anomaly' in frame.columns else 0,
        'critical_days': int((frame['risk_level'] == '🔴 CRITIQUE').sum()) if 'risk_level' in frame.columns else 0,
        'degraded_days': int(((frame['risk_level'] == '🟡 DÉGRADÉE') | (frame['risk_level'] == '🟡 ALERTE')).sum()) if 'risk_level' in frame.columns else 0,
        'healthy_days': int((frame['risk_level'] == '🟢 SAINE').sum()) if 'risk_level' in frame.columns else 0,
        'avg_so2': round(to_float(frame['SO2_column_number_density'].mean() if 'SO2_column_number_density' in frame.columns else 0.0), 6),
        'avg_ndvi': round(to_float(frame['NDVI'].mean() if 'NDVI' in frame.columns else 0.0), 4),
        'source': ACTIVE_BASE_DIR,
        'issues': APP_ERRORS[-5:],
    })


@history_bp.route('/api/diagnostic')
def diagnostic():
    frame = get_dataframe()
    latest = get_latest_row(frame)
    latest_date = 'N/A'
    latest_so2 = 0.0
    latest_ndvi = 0.0

    if latest is not None:
        if 'date' in latest.index and pd.notna(latest['date']):
            latest_date = str(latest['date'].date())
        latest_so2 = to_float(latest.get('SO2_column_number_density', 0.0))
        latest_ndvi = to_float(latest.get('NDVI', 0.0))

    return jsonify({
        'active_base_dir': ACTIVE_BASE_DIR,
        'rows': int(len(frame)),
        'columns': list(frame.columns),
        'latest_date': latest_date,
        'latest_so2': latest_so2,
        'latest_ndvi': latest_ndvi,
        'models': {
            'isolation_forest': model_if is not None,
            'random_forest': model_rf is not None,
            'ridge_regression': model_ridge is not None,
            'scaler': scaler is not None,
            'scaler_ridge': scaler_ridge is not None,
        },
        'live': {
            'api': AIR_QUALITY_API,
            'refresh_seconds': LIVE_REFRESH_SECONDS,
            'zones': [z['name'] for z in ZONES],
        },
        'issues': APP_ERRORS,
    })
