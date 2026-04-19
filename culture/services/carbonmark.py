import requests
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
CARBONMARK_API_KEY = os.getenv(
    "CARBONMARK_API_KEY",
    "cm_api_sandbox_941075b1-84ac-48bb-880f-562d0cff123c"
)

CARBONMARK_BASE = "https://v1.api.carbonmark.com"

# Taux de séquestration par genre botanique (tCO2/ha/an)
# Source : littérature agronomique
CARBON_RATES = {
    "PAULOWNIA":  12.0,
    "ATRIPLEX":    4.0,
    "MORINGA":     6.0,
    "ACACIA":      8.0,
    "PROSOPIS":    5.0,
    "TAMARIX":     3.5,
    "HALOXYLON":   3.0,
    "PHOENIX":    10.0,
    "DEFAULT":     5.0,
}

def get_carbon_price_usd() -> float:
    """
    Récupère le prix actuel des crédits carbone depuis Carbonmark API.
    Retourne le prix en USD/tonne CO2.
    """
    try:
        headers = {
            "Authorization": f"Bearer {CARBONMARK_API_KEY}",
            "Content-Type":  "application/json"
        }
        r = requests.get(
            f"{CARBONMARK_BASE}/projects",
            headers=headers,
            params={"limit": 5, "category": "forestry"},
            timeout=10,
            verify=False

        )
        r.raise_for_status()
        data     = r.json()
        projects = data.get("items", data if isinstance(data, list) else [])

        prices = []
        for p in projects:
            price = (p.get("price") or
                     p.get("minCarbonPrice") or
                     p.get("latestPrice"))
            if price:
                try:
                    prices.append(float(price))
                except:
                    pass

        if prices:
            avg_usd = sum(prices) / len(prices)
            print(f"[Carbonmark] Prix moyen : {avg_usd:.2f} USD/t")
            return round(avg_usd, 2)

    except Exception as e:
        print(f"[Carbonmark] fallback : {e}")

    # Fallback : prix marché Gold Standard 2024
    return 8.5

def usd_to_tnd(usd: float) -> float:
    """Conversion USD → TND (taux fixe BNT 2024)"""
    return round(usd * 3.28, 2)

def get_carbon_rate(scientname: str) -> float:
    """Taux de séquestration CO2 pour une plante (tCO2/ha/an)"""
    genre = scientname.upper().split()[0] if scientname else "DEFAULT"
    return CARBON_RATES.get(genre, CARBON_RATES["DEFAULT"])

def calculate_carbon_revenue(
    scientname:   str,
    superficie_ha: float,
    prix_usd:      float
) -> dict:
    """
    Calcule les revenus en crédits carbone pour une parcelle.

    Retourne :
        {
            tCO2_ha_an, tCO2_total_an,
            revenu_usd_an, revenu_tnd_an,
            revenu_tnd_5ans,
            prix_marche_usd
        }
    """
    rate        = get_carbon_rate(scientname)
    total_co2   = round(rate * superficie_ha, 2)
    rev_usd     = round(total_co2 * prix_usd,  2)
    rev_tnd     = usd_to_tnd(rev_usd)

    return {
        "tCO2_ha_an":      rate,
        "tCO2_total_an":   total_co2,
        "revenu_usd_an":   rev_usd,
        "revenu_tnd_an":   rev_tnd,
        "revenu_tnd_5ans": round(rev_tnd * 5, 2),
        "prix_marche_usd": prix_usd
    }