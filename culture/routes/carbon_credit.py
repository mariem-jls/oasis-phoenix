from flask import Blueprint, request, jsonify
from culture.services.carbonmark import (
    get_carbon_price_usd,
    calculate_carbon_revenue,
    get_carbon_rate,
    usd_to_tnd,
    CARBON_RATES
)

culture_carbon_bp = Blueprint("culture_carbon", __name__)

@culture_carbon_bp.route("/culture/carbon/price", methods=["GET"])
def carbon_price():
    """
    Prix actuel des crédits carbone depuis Carbonmark.

    Retourne :
        {prix_usd, prix_tnd, source}
    """
    prix_usd = get_carbon_price_usd()
    return jsonify({
        "prix_usd_tonne": prix_usd,
        "prix_tnd_tonne": usd_to_tnd(prix_usd),
        "source":         "Carbonmark API"
    }), 200


@culture_carbon_bp.route("/culture/carbon/calculate", methods=["GET"])
def carbon_calculate():
    """
    Calcule les revenus carbone pour une plante et une superficie.

    Paramètres GET :
        scientname   : nom scientifique (ex: ACACIA TORTILIS)
        superficie   : en hectares (défaut: 1.0)

    Exemple :
        GET /culture/carbon/calculate?scientname=ACACIA TORTILIS&superficie=2.5
    """
    scientname = request.args.get("scientname", "")
    try:
        superficie = float(request.args.get("superficie", 1.0))
    except ValueError:
        return jsonify({"error": "superficie invalide"}), 400

    if not scientname:
        return jsonify({"error": "scientname obligatoire"}), 400

    prix_usd = get_carbon_price_usd()
    carbon   = calculate_carbon_revenue(scientname, superficie, prix_usd)

    return jsonify({
        "scientname":  scientname,
        "superficie":  superficie,
        "carbon":      carbon
    }), 200


@culture_carbon_bp.route("/culture/carbon/rates", methods=["GET"])
def carbon_rates():
    """
    Liste tous les taux de séquestration CO2 disponibles.
    """
    prix_usd = get_carbon_price_usd()
    rates    = []

    for genre, tco2 in CARBON_RATES.items():
        if genre == "DEFAULT":
            continue
        rev_tnd = usd_to_tnd(tco2 * prix_usd)
        rates.append({
            "genre":         genre,
            "tCO2_ha_an":    tco2,
            "revenu_tnd_an": rev_tnd,
        })

    rates.sort(key=lambda x: x["tCO2_ha_an"], reverse=True)

    return jsonify({
        "prix_carbone_usd": prix_usd,
        "prix_carbone_tnd": usd_to_tnd(prix_usd),
        "taux":             rates
    }), 200