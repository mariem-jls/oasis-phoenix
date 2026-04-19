import time
import urllib.parse
import urllib.request
import json

from config import AIR_QUALITY_API, LIVE_REFRESH_SECONDS, ZONES, to_float, to_text, append_error_once
from services.ai_engine import compute_toxicity, run_ai_on_live

_LIVE_CACHE = {}


def fetch_live_air_quality(zone_name, lat, lon):
    cache_key = f"{zone_name}|{lat:.4f}|{lon:.4f}"
    now = time.time()

    cached = _LIVE_CACHE.get(cache_key)
    if cached and now - cached['fetched_at'] < LIVE_REFRESH_SECONDS:
        return cached['payload']

    params = {
        'latitude': lat,
        'longitude': lon,
        'current': 'sulphur_dioxide,nitrogen_dioxide,ozone,carbon_monoxide,european_aqi',
        'timezone': 'auto',
    }
    query = urllib.parse.urlencode(params)
    url = f"{AIR_QUALITY_API}?{query}"

    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            raw = response.read().decode('utf-8')
            parsed = json.loads(raw)

        current = parsed.get('current', {})
        so2_ug = to_float(current.get('sulphur_dioxide', 0.0))
        no2_ug = to_float(current.get('nitrogen_dioxide', 0.0))
        o3_ug = to_float(current.get('ozone', 0.0))
        co_ug = to_float(current.get('carbon_monoxide', 0.0))

        toxicity = compute_toxicity(so2_ug, no2_ug, o3_ug, co_ug)
        ai_payload = run_ai_on_live(zone_name, so2_ug, no2_ug, co_ug, o3_ug)

        payload = {
            'zone': zone_name,
            'lat': lat,
            'lon': lon,
            'timestamp': to_text(current.get('time'), 'N/A'),
            'source': 'open-meteo-air-quality',
            'so2_ug_m3': round(so2_ug, 2),
            'no2_ug_m3': round(no2_ug, 2),
            'o3_ug_m3': round(o3_ug, 2),
            'co_ug_m3': round(co_ug, 2),
            'european_aqi': current.get('european_aqi'),
            'toxicity': toxicity,
            'ai': ai_payload,
        }
        _LIVE_CACHE[cache_key] = {'payload': payload, 'fetched_at': now}
        return payload
    except Exception as exc:
        append_error_once(f"Live API fetch failed for {zone_name}: {exc}")
        if cached:
            stale = dict(cached['payload'])
            stale['stale'] = True
            return stale

        return {
            'zone': zone_name,
            'lat': lat,
            'lon': lon,
            'timestamp': 'N/A',
            'source': 'open-meteo-air-quality',
            'so2_ug_m3': 0.0,
            'no2_ug_m3': 0.0,
            'o3_ug_m3': 0.0,
            'co_ug_m3': 0.0,
            'european_aqi': None,
            'toxicity': compute_toxicity(0.0, 0.0, 0.0, 0.0),
            'ai': run_ai_on_live(zone_name, 0.0, 0.0, 0.0, 0.0),
            'unavailable': True,
        }


def get_live_snapshot_all_zones():
    zones_payload = []
    for zone in ZONES:
        zones_payload.append(fetch_live_air_quality(zone['name'], zone['lat'], zone['lon']))

    if not zones_payload:
        return {
            'zones': [],
            'summary': compute_toxicity(0.0, 0.0, 0.0, 0.0),
            'worst_zone': 'N/A',
            'timestamp': 'N/A',
            'source': 'open-meteo-air-quality',
        }

    worst = max(zones_payload, key=lambda z: to_float(z.get('toxicity', {}).get('risk_score', 0.0)))
    return {
        'zones': zones_payload,
        'summary': worst.get('toxicity', compute_toxicity(0.0, 0.0, 0.0, 0.0)),
        'worst_zone': worst.get('zone', 'N/A'),
        'timestamp': worst.get('timestamp', 'N/A'),
        'source': 'open-meteo-air-quality',
    }


def find_zone(zone_name):
    for zone in ZONES:
        if zone['name'].lower() == zone_name.lower():
            return zone
    return None
