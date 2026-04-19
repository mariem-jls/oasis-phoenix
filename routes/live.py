from flask import Blueprint, jsonify

from config import WHO_THRESHOLDS_UG_M3
from services.live_air import get_live_snapshot_all_zones, fetch_live_air_quality, find_zone

live_bp = Blueprint('live', __name__)


@live_bp.route('/api/live/latest')
def live_latest():
    return jsonify(get_live_snapshot_all_zones())


@live_bp.route('/api/live/zones')
def live_zones():
    return jsonify(get_live_snapshot_all_zones().get('zones', []))


@live_bp.route('/api/live/zone/<zone_name>')
def live_zone(zone_name):
    target = find_zone(zone_name)
    if target is None:
        return jsonify({'error': f'Unknown zone: {zone_name}'}), 404
    return jsonify(fetch_live_air_quality(target['name'], target['lat'], target['lon']))


@live_bp.route('/api/anomalies/live')
def anomalies_live():
    zones = get_live_snapshot_all_zones().get('zones', [])
    anomalies = []
    for z in zones:
        zone_name = z.get('zone', 'N/A')
        zone_meta = find_zone(zone_name)
        ai = z.get('ai', {})
        if ai.get('is_anomaly', False):
            anomalies.append({
                'zone': zone_name,
                'lat': zone_meta.get('lat') if zone_meta else None,
                'lon': zone_meta.get('lon') if zone_meta else None,
                'timestamp': z.get('timestamp', 'N/A'),
                'so2_ug_m3': z.get('so2_ug_m3', 0.0),
                'no2_ug_m3': z.get('no2_ug_m3', 0.0),
                'co_ug_m3': z.get('co_ug_m3', 0.0),
                'o3_ug_m3': z.get('o3_ug_m3', 0.0),
                'anomaly_label': ai.get('anomaly_label', 'ANOMALY'),
                'risk_level': ai.get('risk_level', '🟢 SAINE'),
                'risk_score': ai.get('risk_score', 0.0),
            })
    return jsonify(anomalies)


@live_bp.route('/api/thresholds')
def thresholds():
    return jsonify({
        'units': 'ug/m3',
        'who': WHO_THRESHOLDS_UG_M3,
        'risk': {
            'critical': 70,
            'degraded': 40,
        },
    })