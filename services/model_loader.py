import os
import joblib

from config import MODELS_DIR, append_error_once


def safe_load_model(model_name):
    model_path = os.path.join(MODELS_DIR, model_name)
    if not os.path.exists(model_path):
        append_error_once(f"Missing model file: {model_path}")
        return None
    try:
        return joblib.load(model_path)
    except Exception as exc:
        append_error_once(f"Failed to load model {model_name}: {exc}")
        return None


model_if = safe_load_model('isolation_forest.pkl')
model_rf = safe_load_model('random_forest.pkl')
model_ridge = safe_load_model('ridge_regression.pkl')
scaler = safe_load_model('scaler.pkl')
scaler_ridge = safe_load_model('scaler_ridge.pkl')
