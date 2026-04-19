from flask import Blueprint, jsonify

from config import to_float
from services.ai_engine import compute_toxicity, safe_predict_ndvi_30d
from services.data_loader import get_dataframe, get_latest_row
from services.live_air import get_live_snapshot_all_zones

predict_bp = Blueprint('predict', __name__)


@predict_bp.route('/api/predict')
def predict():
    frame = get_dataframe()
    row = get_latest_row(frame)
    if row is None:
        return jsonify({'error': 'Dataset not loaded'}), 503

    ndvi_30d = safe_predict_ndvi_30d(row)
    current_ndvi = to_float(row.get('NDVI', 0.0))
    trend = 'improving' if ndvi_30d > current_ndvi else 'degrading'
    row_date = row['date'] if 'date' in row.index else None
    date_text = str(row_date.date()) if row_date is not None else 'N/A'

    return jsonify({
        'current_ndvi': round(current_ndvi, 4),
        'predicted_ndvi': round(ndvi_30d, 4),
        'trend': trend,
        'current_date': date_text,
    })


@predict_bp.route('/api/hazard')
def hazard():
    live = get_live_snapshot_all_zones()
    summary = live.get('summary', compute_toxicity(0.0, 0.0, 0.0, 0.0))

    frame = get_dataframe()
    row = get_latest_row(frame)
    health_risk = to_float(row.get('health_risk_index', 0.0)) if row is not None else 0.0

    hazard_prob = min(
        1.0,
        max(
            0.0,
            0.55 * (health_risk / 100.0) + 0.45 * (to_float(summary.get('risk_score', 0.0)) / 100.0),
        ),
    )
    hazard_label = 'HIGH' if hazard_prob >= 0.66 else 'MEDIUM' if hazard_prob >= 0.4 else 'LOW'

    return jsonify({
        'hazard_30d_probability': round(hazard_prob, 3),
        'hazard_30d_binary': 1 if hazard_prob >= 0.5 else 0,
        'hazard_level': hazard_label,
        'live_toxicity': summary,
        'worst_zone': live.get('worst_zone', 'N/A'),
        'timestamp': live.get('timestamp', 'N/A'),
        'method': 'blended-live-toxicity-and-health-risk',
    })
