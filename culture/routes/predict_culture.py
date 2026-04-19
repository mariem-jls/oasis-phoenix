from flask import Blueprint, request, jsonify
from culture.services.soilgrids        import get_soil
from culture.services.openmeteo        import get_climate
from culture.services.nasa             import get_nasa
from culture.services.carbonmark       import get_carbon_price_usd, calculate_carbon_revenue
from culture.services.gemini_enrichment import enrichir_recommandations
from culture.ml.predictor              import predict

culture_predict_bp = Blueprint("culture_predict", __name__)

@culture_predict_bp.route("/culture/recommend", methods=["GET"])
def recommend():
    """
    Recommande les meilleures plantes pour une parcelle.

    Paramètres GET :
        lat          : latitude  (obligatoire)
        lon          : longitude (obligatoire)
        superficie   : superficie en hectares (défaut: 1.0)
        top_n        : nombre de recommandations (défaut: 5)

    Exemple :
        GET /culture/recommend?lat=33.88&lon=10.09&superficie=2.5
    """
    # ── 1. Paramètres
    try:
        lat        = float(request.args.get("lat"))
        lon        = float(request.args.get("lon"))
        superficie = float(request.args.get("superficie", 1.0))
        top_n      = int(request.args.get("top_n", 5))
    except (TypeError, ValueError):
        return jsonify({"error": "lat et lon sont obligatoires"}), 400

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return jsonify({"error": "Coordonnées invalides"}), 400

    # ── 2. Appels APIs terrain
    soil   = get_soil(lat, lon)
    climat = get_climate(lat, lon)
    nasa   = get_nasa(lat, lon)

    # ── 3. Prédiction RF
    recommandations = predict(soil, climat, nasa, top_n=top_n)

    # ── 4. Prix carbone Carbonmark
    prix_usd = get_carbon_price_usd()

    # ── 5. Revenus carbone
    for rec in recommandations:
        rec["carbon"] = calculate_carbon_revenue(
            scientname    = rec["scientname"],
            superficie_ha = superficie,
            prix_usd      = prix_usd
        )

    # ── 6. Conditions pour Gemini
    conditions_terrain = {
        "pH":        soil["pH"],
        "salinite":  soil["salinite"],
        "T_max":     climat["T_max"],
        "T_min":     climat["T_min"],
        "precip_mm": climat["precip"],
        "moisture":  climat["moisture"],
        "ndvi":      nasa["ndvi"],
        "radiation": nasa["radiation"],
    }

    # ── 7. Enrichissement Gemini + Wikipedia
    enrichir = request.args.get("enrichir", "true").lower() != "false"
    if enrichir:
        recommandations = enrichir_recommandations(
            recommandations, conditions_terrain)

    # ── 8. Réponse
    return jsonify({
        "coordonnees":      {"lat": lat, "lon": lon},
        "superficie_ha":    superficie,
        "conditions_terrain": conditions_terrain,
        "sources": {
            "sol":    soil["source"],
            "climat": climat["source"],
            "nasa":   nasa["source"],
            "enrichissement": "Gemini 1.5 Flash + Wikipedia"
        },
        "recommandations": recommandations
    }), 200


@culture_predict_bp.route("/culture/recommend", methods=["POST"])
def recommend_post():
    """
    Version POST — pour envoyer plusieurs parcelles à la fois.

    Body JSON :
        {
            "parcelles": [
                {"lat": 33.88, "lon": 10.09, "superficie": 2.5},
                {"lat": 33.75, "lon": 10.12, "superficie": 1.8}
            ],
            "top_n": 3
        }
    """
    data      = request.get_json()
    parcelles = data.get("parcelles", [])
    top_n     = int(data.get("top_n", 3))

    if not parcelles:
        return jsonify({"error": "Aucune parcelle fournie"}), 400

    prix_usd = get_carbon_price_usd()
    resultats = []

    for p in parcelles:
        try:
            lat        = float(p["lat"])
            lon        = float(p["lon"])
            superficie = float(p.get("superficie", 1.0))

            soil   = get_soil(lat, lon)
            climat = get_climate(lat, lon)
            nasa   = get_nasa(lat, lon)
            recs   = predict(soil, climat, nasa, top_n=top_n)

            for rec in recs:
                rec["carbon"] = calculate_carbon_revenue(
                    rec["scientname"], superficie, prix_usd)

            resultats.append({
                "lat":             lat,
                "lon":             lon,
                "superficie_ha":   superficie,
                "recommandations": recs
            })
        except Exception as e:
            resultats.append({
                "lat":   p.get("lat"),
                "lon":   p.get("lon"),
                "error": str(e)
            })

    return jsonify({
        "total":     len(resultats),
        "prix_carbone_usd": prix_usd,
        "resultats": resultats
    }), 200