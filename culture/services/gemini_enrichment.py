import requests
import re
import os

def build_slug(scientname: str) -> str:
    """Convertit ATRIPLEX CONFERTIFOLIA (T.) → Atriplex_confertifolia"""
    clean = re.sub(r'\(.*?\)', '', scientname).strip()
    parts = clean.split()
    if len(parts) >= 2:
        return f"{parts[0].capitalize()}_{parts[1].lower()}"
    return parts[0].capitalize() if parts else ""

def get_image_wikipedia(slug: str) -> str:
    if not slug:
        return ""
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}",
            headers={"User-Agent": "OasisPhoenix/1.0 (contact@oasis.tn)"},
            timeout=8
        )
        r.raise_for_status()
        return r.json().get("thumbnail", {}).get("source", "")
    except Exception as e:
        print(f"[Wikipedia] {slug} : {e}")
        return ""

def enrichir_recommandations(recommandations: list, conditions: dict) -> list:
    enrichies = []
    for rec in recommandations:
        sci   = rec.get("scientname", "")
        slug  = build_slug(sci)
        image = get_image_wikipedia(slug)
        enrichies.append({
            **rec,
            "nom_commun_fr":      rec.get("name", sci),
            "nom_commun_ar":      "",
            "nom_tunisie":        "",
            "description_fr":     "",
            "pourquoi_ici":       "",
            "conseils_plantation":"",
            "saison_plantation":  "",
            "image_url":          image,
            "wikipedia_slug":     slug,
        })
        print(f"[Wikipedia] {sci} → {slug} → {'✓' if image else '✗'}")
    return enrichies