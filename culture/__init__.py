# culture/__init__.py
from culture.routes.predict_culture import culture_predict_bp
from culture.routes.carbon_credit   import culture_carbon_bp

def register_culture_blueprints(app):
    app.register_blueprint(culture_predict_bp)
    app.register_blueprint(culture_carbon_bp)
    print("[Culture] Blueprints enregistrés")
    print("[Culture]   GET  /culture/recommend")
    print("[Culture]   GET  /culture/carbon/price")
    print("[Culture]   GET  /culture/carbon/rates")