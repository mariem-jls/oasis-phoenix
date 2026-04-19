from flask import Blueprint, jsonify
import pandas as pd

from config import ACTIVE_BASE_DIR, APP_ERRORS, ZONES, to_float, to_text
from services.ai_engine import compute_toxicity, soil_stress_payload
from services.data_loader import get_dataframe, get_latest_row, compute_zone_base_risks
from services.live_air import fetch_live_air_quality, get_live_snapshot_all_zones, find_zone

zones_bp = Blueprint('zones', __name__)


@zones_bp.route('/api/latest')
def latest():
    frame = get_dataframe()
    row = get_latest_row(frame)
    if row is None:
        return jsonify({'error': 'Dataset not loaded', 'source': ACTIVE_BASE_DIR, 'issues': APP_ERRORS}), 503

    live = get_live_snapshot_all_zones()
    live_zones = live.get('zones', [])
    first_zone = live_zones[0] if live_zones else {}
    live_summary = live.get('summary', compute_toxicity(0.0, 0.0, 0.0, 0.0))

    row_date = row['date'] if 'date' in row.index else None
    date_text = str(row_date.date()) if pd.notna(row_date) else 'N/A'

    return jsonify({
        'date': date_text,
        'SO2': round(to_float(row['SO2_column_number_density']), 10),
        'NO2': round(to_float(row['NO2_column_number_density']), 10),
        'CO': round(to_float(row['CO_column_number_density']), 10),
        'O3': round(to_float(row['O3_column_number_density']), 10),
        'AER': round(to_float(row['absorbing_aerosol_index']), 6),
        'HCHO': round(to_float(row['tropospheric_HCHO_column_number_density']), 10),
        'SO2_date': date_text,
        'NDVI': round(to_float(row['NDVI']), 4),
        'NDWI': round(to_float(row['NDWI']), 4),
        'temp': round(to_float(row['temp']), 2),
        'soil_moisture': round(to_float(row['soil_moisture']), 4),
        'risk_level': to_text(row['risk_level']),
        'health_risk': round(to_float(row['health_risk_index']), 1),
        'cause': to_text(row['cause']),
        'phoenix': {
            'statut': to_text(row['phoenix_statut']),
            'plante': to_text(row['phoenix_plante']),
            'revenu': to_text(row['phoenix_revenu']),
            'carbone': to_text(row['phoenix_carbone']),
            'delai': to_text(row['phoenix_delai']),
            'action': to_text(row['phoenix_action']),
        },
        'source': ACTIVE_BASE_DIR,
        'live_source': live.get('source', 'N/A'),
        'live_timestamp': live.get('timestamp', 'N/A'),
        'live_enabled': True,
        'live_worst_zone': live.get('worst_zone', 'N/A'),
        'toxicity': live_summary,
        'SO2_live_ug_m3': round(to_float(first_zone.get('so2_ug_m3', 0.0)), 2),
        'NO2_live_ug_m3': round(to_float(first_zone.get('no2_ug_m3', 0.0)), 2),
        'CO_live_ug_m3': round(to_float(first_zone.get('co_ug_m3', 0.0)), 2),
        'O3_live_ug_m3': round(to_float(first_zone.get('o3_ug_m3', 0.0)), 2),
        'issues': APP_ERRORS[-5:],
    })


@zones_bp.route('/api/zones')
def zones():
    return jsonify({'zones': ZONES})


@zones_bp.route('/api/zones/ai')
def zones_ai():
    results = []
    for zone in ZONES:
        live = fetch_live_air_quality(zone['name'], zone['lat'], zone['lon'])
        ai = live.get('ai', {})
        results.append({
            'zone': zone['name'],
            'lat': zone['lat'],
            'lon': zone['lon'],
            'so2_ug_m3': live.get('so2_ug_m3', 0),
            'no2_ug_m3': live.get('no2_ug_m3', 0),
            'co_ug_m3': live.get('co_ug_m3', 0),
            'o3_ug_m3': live.get('o3_ug_m3', 0),
            'european_aqi': live.get('european_aqi'),
            'is_anomaly': ai.get('is_anomaly', False),
            'anomaly_label': ai.get('anomaly_label', 'NORMAL'),
            'anomaly_score': ai.get('anomaly_score', 0),
            'cause': ai.get('cause', 'NORMAL'),
            'cause_proba': ai.get('cause_proba', 0),
            'risk_score': ai.get('risk_score', 0),
            'risk_level': ai.get('risk_level', '🟢 SAINE'),
            'current_ndvi': ai.get('current_ndvi', 0),
            'ndvi_predicted_30d': ai.get('ndvi_predicted_30d', 0),
            'ndvi_trend': ai.get('ndvi_trend', 'stable'),
            'timestamp': live.get('timestamp', 'N/A'),
        })
    return jsonify(results)


@zones_bp.route('/api/zone/<zone_name>')
def zone_detail(zone_name):
    target = find_zone(zone_name)
    if target is None:
        return jsonify({'error': f'Unknown zone: {zone_name}'}), 404

    frame = get_dataframe()
    row = get_latest_row(frame)
    if row is None:
        return jsonify({'error': 'Dataset not loaded', 'issues': APP_ERRORS}), 503

    live_zone_payload = fetch_live_air_quality(target['name'], target['lat'], target['lon'])
    row_date = row['date'] if 'date' in row.index else None
    date_text = str(row_date.date()) if pd.notna(row_date) else 'N/A'

    return jsonify({
        'zone': target['name'],
        'coords': {'lat': target['lat'], 'lon': target['lon']},
        'live': live_zone_payload,
        'snapshot': {
            'date': date_text,
            'NDVI': round(to_float(row.get('NDVI', 0.0)), 4),
            'NDWI': round(to_float(row.get('NDWI', 0.0)), 4),
            'temp': round(to_float(row.get('temp', 0.0)), 2),
            'soil_moisture': round(to_float(row.get('soil_moisture', 0.0)), 4),
            'cause': to_text(row.get('cause', 'N/A')),
            'risk_level': to_text(row.get('risk_level', 'N/A')),
            'health_risk': round(to_float(row.get('health_risk_index', 0.0)), 1),
            'phoenix': {
                'statut': to_text(row.get('phoenix_statut', 'N/A')),
                'plante': to_text(row.get('phoenix_plante', 'N/A')),
                'revenu': to_text(row.get('phoenix_revenu', 'N/A')),
                'carbone': to_text(row.get('phoenix_carbone', 'N/A')),
                'delai': to_text(row.get('phoenix_delai', 'N/A')),
                'action': to_text(row.get('phoenix_action', 'N/A')),
            },
        },
    })


@zones_bp.route('/api/oasis/soil')
def oasis_soil():
    frame = get_dataframe()
    row = get_latest_row(frame)
    if row is None:
        return jsonify({'error': 'Dataset not loaded', 'issues': APP_ERRORS}), 503

    base_soil = to_float(row.get('soil_moisture', 0.0))
    base_ndvi = to_float(row.get('NDVI', 0.0))
    base_temp = to_float(row.get('temp', 0.0))
    date_value = row.get('date')
    date_text = str(date_value.date()) if pd.notna(date_value) else 'N/A'

    zones_payload = []
    for zone in ZONES:
        dryness_factor = min(1.25, 0.85 + zone['lat'] / 100.0 + zone['lon'] / 200.0)
        soil_est = max(0.0, min(0.45, base_soil / dryness_factor))
        ndvi_est = max(0.0, min(1.0, base_ndvi * (1.03 - dryness_factor / 3.0)))
        temp_est = base_temp + (dryness_factor - 1.0) * 4.0
        stress = soil_stress_payload(soil_est, ndvi_est, temp_est)

        zones_payload.append({
            'zone': zone['name'],
            'lat': zone['lat'],
            'lon': zone['lon'],
            'soil_moisture': round(soil_est, 4),
            'soil_percent': round(soil_est * 100.0, 1),
            'ndvi': round(ndvi_est, 4),
            'temp': round(temp_est, 2),
            **stress,
        })

    worst = max(zones_payload, key=lambda z: z['stress_score']) if zones_payload else None

    return jsonify({
        'date': date_text,
        'focus': 'oasis-soil-health',
        'zones': zones_payload,
        'worst_zone': worst['zone'] if worst else 'N/A',
        'worst_stress_level': worst['stress_level'] if worst else 'N/A',
        'worst_stress_score': worst['stress_score'] if worst else 0,
    })

@zones_bp.route('/api/zones/baserisks')
def zone_base_risks():
    frame = get_dataframe()
    return jsonify(compute_zone_base_risks(frame))
