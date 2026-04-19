from routes.live import live_bp
from routes.history import history_bp
from routes.zones import zones_bp
from routes.predict import predict_bp


def register_blueprints(app):
    app.register_blueprint(live_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(zones_bp)
    app.register_blueprint(predict_bp)
