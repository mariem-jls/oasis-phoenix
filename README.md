# 🌿 Oasis Phoenix — AI Healing Gabès

<p align="center">
  <img src="static/logo_phoenix.png" alt="Oasis Phoenix Logo" width="180"/>
</p>

<p align="center">
  <strong>Plateforme IA intégrée de surveillance environnementale et de recommandation agricole</strong><br>
  <em>Gouvernorat de Gabès · Tunisie du Sud</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=flat-square"/>
  <img src="https://img.shields.io/badge/Flask-3.0-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/scikit--learn-1.6.1-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/Leaflet-1.9.4-brightgreen?style=flat-square"/>
</p>

---

## 📋 Description

Oasis Phoenix est une plateforme à double module développée pour répondre à la crise environnementale et agricole du gouvernorat de Gabès, impacté par l'industrie SIAPE (phosphogypse, SO₂) :

| Module | Description |
|---|---|
| **AI Healing Gabès** | Surveillance temps réel des polluants atmosphériques, détection d'anomalies IA, heatmap live des 13 délégations |
| **Culture Phoenix** | Recommandation de cultures adaptées par Random Forest (1 694 espèces FAO), calcul de revenus crédits carbone |

---

## 🗂️ Structure du projet

```
oasis_phoenix/
├── app.py                          ← Point d'entrée Flask unifié
├── config.py                       ← Configuration globale
├── requirements.txt                ← Dépendances Python
│
├── culture/                        ← Module recommandation agricole
│   ├── __init__.py                 ← register_culture_blueprints()
│   ├── ml/predictor.py             ← Chargement modèle RF + prédiction
│   ├── routes/
│   │   ├── predict_culture.py      ← GET/POST /culture/recommend
│   │   └── carbon_credit.py        ← /culture/carbon/price|rates|calculate
│   └── services/
│       ├── soilgrids.py            ← pH + salinité (SoilGrids API)
│       ├── openmeteo.py            ← Température + précipitations (3 ans)
│       ├── nasa.py                 ← Radiation + NDVI proxy (NASA POWER)
│       ├── carbonmark.py           ← Prix crédits carbone Carbonmark
│       └── gemini_enrichment.py    ← Enrichissement Gemini + images Wikipedia
│
├── routes/                         ← Module surveillance environnementale
│   ├── history.py                  ← /api/history
│   ├── live.py                     ← /api/live/zones
│   ├── predict.py                  ← /api/predict
│   └── zones.py                    ← /api/zones
│
├── services/                       ← Services partagés
│   ├── ai_engine.py
│   ├── data_loader.py
│   ├── live_air.py
│   └── model_loader.py
│
├── models/                         ← Fichiers modèles ML (non versionnés)
│   ├── isolation_forest.pkl        ← Module surveillance
│   ├── random_forest.pkl           ← Module surveillance
│   ├── ridge_regression.pkl        ← Module surveillance
│   ├── scaler.pkl                  ← Module surveillance
│   ├── scaler_ridge.pkl            ← Module surveillance
│   ├── culture_model_rf.pkl        ← Module culture (RF 1694 espèces)
│   ├── culture_scaler.pkl          ← Module culture
│   ├── culture_label_encoder.pkl   ← Module culture
│   ├── culture_features_list.pkl   ← Module culture
│   └── scientname_to_name.csv      ← Mapping noms scientifiques
│
├── data/
│   └── combined_clean.csv          ← Dataset surveillance (6 ans)
│
├── templates/
│   ├── index.html                  ← Landing page unifiée
│   └── carte.html                  ← Dashboard surveillance
│
└── static/
    ├── logo_phoenix.png            ← Logo officiel
    ├── gabes_delegations.geojson   ← GeoJSON 13 délégations
    └── culture/
        ├── carte_culture.html      ← Carte recommandation parcelle
        ├── resultats_culture.html  ← Résultats détaillés
        ├── dashboard_carbone.html  ← Dashboard crédits carbone
        └── intro.html              ← Expérience intro cinématique
```

---

## 🚀 Démarrage rapide

```bash
# 1. Cloner le projet
git clone https://github.com/nibnib7/oasis_phoenix.git
cd oasis_phoenix

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Placer les fichiers modèles dans models/
# (voir section Modèles requis ci-dessous)

# 4. Lancer le serveur
python app.py
```

Ouvrez **http://127.0.0.1:5000** dans votre navigateur.

---

## 🤖 Modèles requis

Les fichiers `.pkl` ne sont pas versionnés (trop lourds). Contactez l'équipe pour les obtenir.

### Module Surveillance (collègues)
```
models/isolation_forest.pkl
models/random_forest.pkl
models/ridge_regression.pkl
models/scaler.pkl
models/scaler_ridge.pkl
```
Chargés par `services/model_loader.py`.

### Module Culture (recommandation agricole)
```
models/culture_model_rf.pkl         ← RandomForest n=100 depth=30 — 91.5% accuracy
models/culture_scaler.pkl
models/culture_label_encoder.pkl
models/culture_features_list.pkl
models/scientname_to_name.csv
```
Chargés par `culture/ml/predictor.py`.
Générés depuis Google Colab sur dataset FAO ECOCROP (1 694 espèces).

---

## 🌐 URLs disponibles

| URL | Description |
|---|---|
| `http://localhost:5000/` | Landing page unifiée |
| `http://localhost:5000/dashboard` | Dashboard surveillance environnementale |
| `http://localhost:5000/culture` | Carte recommandation agricole |
| `http://localhost:5000/culture/resultats` | Résultats détaillés |
| `http://localhost:5000/culture/carbone` | Dashboard crédits carbone |
| `http://localhost:5000/culture/intro` | Intro cinématique |

---

## 🔌 APIs utilisées

| API | Usage | Clé requise |
|---|---|---|
| SoilGrids | pH + salinité du sol | Non |
| Open-Meteo | Température + précipitations (3 ans) | Non |
| NASA POWER | Radiation solaire + NDVI proxy | Non |
| Carbonmark | Prix crédits carbone live | Oui (sandbox) |
| Gemini 2.0 Flash | Enrichissement noms plantes | Oui |

---

## 📊 Endpoints API Culture

```
GET /culture/recommend?lat=33.88&lon=10.09&superficie=2.5
GET /culture/carbon/price
GET /culture/carbon/rates
GET /culture/carbon/calculate?scientname=ACACIA+TORTILIS&superficie=2.5
GET /health
```

---

## 👥 Équipe

Projet développé dans le cadre de la réhabilitation agricole du gouvernorat de Gabès, Tunisie.

---

## 📄 Licence

MIT License — Oasis Phoenix Team · 2026