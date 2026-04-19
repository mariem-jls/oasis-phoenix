# 🌿 Oasis Phoenix — AI Healing Gabès

<p align="center">
  <img src="static/phoenix.png" alt="Oasis Phoenix Logo" width="180"/>
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
  <img src="https://img.shields.io/badge/Sentinel--2-ESA-blue?style=flat-square"/>
</p>

---

## 👥 Équipe

 **Nibras Ounissi** 
 **Hana Fkiri** 
 **Marie Jlassi** 
 **Ferdaous Kachouri**
---

## 📋 Description du projet

**Oasis Phoenix** est une réponse technologique à la crise environnementale de Gabès — ville tunisienne dévastée par les rejets industriels de SIAPE (SO₂, phosphogypse) qui détruisent l'oasis historique de Chenini et contaminent les sols agricoles.

### Comment ça marche ?

L'ESA met à disposition gratuitement les images du satellite **Sentinel-2**, qui repasse au-dessus de Gabès tous les 5 jours. Ces images capturent l'infrarouge — invisible à l'œil nu — qui révèle l'état réel de la végétation.

On calcule le **NDVI** (Normalized Difference Vegetation Index) : un score entre -1 et +1 qui mesure la santé des plantes. Un palmier stressé — parce que la nappe phréatique baisse sous l'effet des prélèvements industriels — voit son NDVI chuter **avant** que quiconque ne le remarque sur le terrain.

L'IA prend le relais : elle analyse l'évolution semaine par semaine, **prédit** les zones qui vont devenir critiques dans 3-4 semaines, et **corrèle** les dégradations avec les rejets industriels ou les sécheresses.

---

## 🗂️ Modules de la plateforme

### Module 1 — OasisWatch · Surveillance satellite
Monitore la santé de l'oasis depuis l'espace sans capteur terrain.
- Images Sentinel-2 (ESA) · 5 jours de revisit
- Calcul NDVI pixel par pixel
- Modèle U-Net : détection automatique des zones de dégradation
- Prédiction NDVI 30 jours · Alertes automatiques
- Rapports pour le CRDA Gabès (institution gouvernementale eau/agriculture)

### Module 2 — Surveillance Atmosphérique · AI Healing Gabès
Monitoring temps réel des polluants atmosphériques sur les 13 délégations.
- Données Sentinel-5P + ERA5 + MODIS · 6 ans d'historique
- Modèles : Isolation Forest + Gradient Boosting
- SO₂, NO₂, CO, O₃ · Heatmap live · Leaderboard risque
- Prédiction NDVI 30 jours par délégation

### Module 6 — Culture Phoenix · Conseiller agricole IA
Recommandation de cultures résilientes pour les parcelles dégradées.
- Random Forest entraîné sur 1 694 espèces FAO ECOCROP
- APIs terrain : SoilGrids + Open-Meteo + NASA POWER
- 91.5% précision · Top 5 recommandations personnalisées
- Calcul revenus crédits carbone (Carbonmark · Gold Standard)
- Exemple : *"Plantez du Paulownia ici – gain estimé de 3 350 TND/an en crédits carbone d'ici 5 ans"*

### Module Réclamation — Gabès Voix · Plateforme citoyenne
Signalement participatif des incidents environnementaux.
- Soumission de rapports par les citoyens
- Analyse sémantique Gemini 2.0 Flash
- Clustering géo-temporel automatique des signalements similaires
- Génération d'alertes intelligentes multi-rapports
- Tableau de bord de vigilance citoyenne sur carte interactive

---

## 🗂️ Structure du projet

```
oasis_phoenix/
├── app.py                          ← Point d'entrée Flask unifié
├── config.py                       ← Configuration globale
├── requirements.txt
│
├── culture/                        ← Module Culture Phoenix (Nibras)
│   ├── __init__.py
│   ├── ml/predictor.py
│   ├── routes/
│   │   ├── predict_culture.py      ← GET/POST /culture/recommend
│   │   └── carbon_credit.py        ← /culture/carbon/price|rates|calculate
│   └── services/
│       ├── soilgrids.py
│       ├── openmeteo.py
│       ├── nasa.py
│       ├── carbonmark.py
│       └── gemini_enrichment.py
│
├── routes/                         ← Module Surveillance (Hana + Marie)
│   ├── history.py
│   ├── live.py
│   ├── predict.py
│   └── zones.py
│
├── services/
│   ├── ai_engine.py
│   ├── data_loader.py
│   ├── live_air.py
│   └── model_loader.py
│
├── models/                         ← Fichiers .pkl (non versionnés)
│   ├── isolation_forest.pkl        ← Surveillance atmosphérique
│   ├── random_forest.pkl           ← Surveillance atmosphérique
│   ├── ridge_regression.pkl        ← Surveillance atmosphérique
│   ├── scaler.pkl                  ← Surveillance atmosphérique
│   ├── scaler_ridge.pkl            ← Surveillance atmosphérique
│   ├── culture_model_rf.pkl        ← Culture Phoenix (RF 1694 espèces)
│   ├── culture_scaler.pkl
│   ├── culture_label_encoder.pkl
│   ├── culture_features_list.pkl
│   └── scientname_to_name.csv
│
├── data/
│   └── combined_clean.csv          ← Dataset surveillance 6 ans
│
├── templates/
│   ├── index.html                  ← Landing page unifiée
│   └── carte.html                  ← Dashboard surveillance
│
└── static/
    ├── phoenix.png                 ← Logo officiel
    ├── gabes_delegations.geojson
    └── culture/
        ├── carte_culture.html
        ├── resultats_culture.html
        ├── dashboard_carbone.html
        └── intro.html
```

---

## 🚀 Démarrage rapide

```bash
# 1. Cloner
git clone https://github.com/nibnib7/oasis_phoenix.git
cd oasis_phoenix

# 2. Installer les dépendances
pip install -r requirements.txt

# ⚠️  scikit-learn doit être en version 1.6.1
pip install scikit-learn==1.6.1

# 3. Placer les fichiers .pkl dans models/
# (contacter l'équipe pour les obtenir)

# 4. Lancer
python app.py
```

Ouvrez **http://127.0.0.1:5000**

---

## 🤖 Modèles requis

Les `.pkl` ne sont pas versionnés. Contactez l'équipe.

### Module Surveillance
```
models/isolation_forest.pkl
models/random_forest.pkl
models/ridge_regression.pkl
models/scaler.pkl
models/scaler_ridge.pkl
```

### Module Culture Phoenix
```
models/culture_model_rf.pkl         ← RF n=100 depth=30 · 91.5% accuracy
models/culture_scaler.pkl
models/culture_label_encoder.pkl
models/culture_features_list.pkl
models/scientname_to_name.csv
```
Générés sur Google Colab depuis le dataset FAO ECOCROP (1 694 espèces, data augmentation N=5).

---

## 🌐 URLs

| URL | Module |
|---|---|
| `http://localhost:5000/` | Landing page unifiée |
| `http://localhost:5000/dashboard` | Surveillance atmosphérique |
| `http://localhost:5000/culture` | Carte recommandation agricole |
| `http://localhost:5000/culture/resultats` | Résultats détaillés |
| `http://localhost:5000/culture/carbone` | Dashboard crédits carbone |
| `http://localhost:5000/culture/intro` | Intro cinématique |
| `http://localhost:5000/reclamation` | Plateforme citoyenne |

---

## 🔌 APIs utilisées

| API | Usage | Clé |
|---|---|---|
| Sentinel-2 (ESA) | Images satellite NDVI | Non |
| SoilGrids | pH + salinité sol | Non |
| Open-Meteo | Température + précipitations | Non |
| NASA POWER | Radiation + NDVI proxy | Non |
| Carbonmark | Prix crédits carbone live | Oui |
| Gemini 2.0 Flash | Enrichissement + réclamations | Oui |

---

## 📄 Licence

MIT License — Oasis Phoenix Team · Gabès · 2026
