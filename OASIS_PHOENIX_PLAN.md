# 🌿 OASIS PHOENIX — Plan Complet & État du Projet

> Système de surveillance environnementale intelligente pour l'oasis de Gabès, Tunisie.
> Dernière mise à jour : Avril 2026

---

## ✅ CE QUI EST FAIT

### Données
- [x] 11 sources satellite téléchargées via Google Earth Engine (Sentinel-2, 5P, Landsat, ERA5)
- [x] SO2 et CH4 réparés (fix `unmask()` + `mean.get(..., null)` dans GEE)
- [x] CH4 supprimé (64% zeros, mauvaise échelle — non fiable)
- [x] Dataset fusionné : **2634 lignes, 2019–2026, 0 nulls**
- [x] Nettoyage : SO2/HCHO négatifs clippés à 0
- [x] Feature engineering : 23 colonnes (temporel, rolling, z-scores, changements 7j)

### Modèles IA
- [x] **Isolation Forest** — détection anomalies (132 anomalies, 5.0%)
- [x] **Random Forest** — classification causes (95.5% accuracy, temporal split)
- [x] **Ridge Regression** — prédiction NDVI 30j (R²=0.67, MAE=0.011)
- [x] Health Risk Index (0–100) calculé
- [x] Phoenix recommendations par zone

### Application
- [x] Flask API avec 5 endpoints (`/api/latest`, `/api/anomalies`, `/api/predict`, `/api/history`, `/api/stats`)
- [x] Carte Leaflet animée (scan line, zones pulsantes, marqueurs anomalies)
- [x] Interface radar style météo avec gaz atmosphériques en temps réel

---

## ❌ CE QUI MANQUE — PRIORITÉS

### 🔴 PRIORITÉ 1 — Critique pour la démo

#### 1. Endpoint `/api/history` pour gaz (NO2, CO, O3, AER)
Le panneau latéral affiche SO2 mais les autres gaz ne sont pas remontés dans `/api/latest`.

**Fix dans `app.py`** — ajouter dans `/api/latest` :
```python
# Récupérer la dernière ligne complète
last = df.iloc[-1]
return jsonify({
    ...
    'NO2': round(float(last['NO2_column_number_density']), 8),
    'CO':  round(float(last['CO_column_number_density']), 6),
    'O3':  round(float(last['O3_column_number_density']), 6),
    'AER': round(float(last['absorbing_aerosol_index']), 4),
    'HCHO': round(float(last['tropospheric_HCHO_column_number_density']), 8),
})
```

#### 2. Graphe historique SO2 + NDVI
Aucune visualisation de l'évolution dans le temps. Pour la démo c'est essentiel.

**À ajouter dans `carte.html`** — un mini graphe Chart.js ou D3 en bas de panel :
```html
<canvas id="history-chart" height="100"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

Fetch `/api/history` → afficher SO2 et NDVI sur 2 ans glissants.

#### 3. Seuils OMS visibles sur les barres de gaz
Les barres de gaz n'ont pas de repère visuel pour savoir si c'est dangereux.

**À ajouter** — une ligne verticale rouge à la position du seuil OMS sur chaque barre :
```
SO2  : seuil = 20 µg/m³ ≈ 0.0000076 mol/m²
NO2  : seuil = 40 µg/m³ ≈ 0.0000213 mol/m²
O3   : seuil = 100 µg/m³
CO   : seuil = 10 mg/m³
```

---

### 🟡 PRIORITÉ 2 — Important pour qualité

#### 4. Cause affichée dans l'état actuel
Le panneau latéral ne montre pas la **cause** identifiée par le Random Forest.

**Fix** — ajouter dans `/api/latest` :
```python
'cause': str(last['cause']),
```
Et dans la carte afficher : `Cause: POLLUTION_MODEREE` avec couleur adaptée.

#### 5. Endpoint `/api/zone/<zone_name>`
Quand l'utilisateur clique sur une zone, afficher les données **spécifiques à cette zone** avec diagnostic complet Phoenix.

```python
@app.route('/api/zone/<name>')
def zone_detail(name):
    # Pour l'instant retourner les données globales latest
    # Future : données per-pixel via PostGIS
    ...
```

#### 6. Auto-refresh toutes les 30 secondes
La carte ne se rafraîchit pas automatiquement.

**À ajouter en fin de `carte.html`** :
```javascript
setInterval(() => {
    fetch('/api/latest').then(r=>r.json()).then(updatePanel);
}, 30000);
```

#### 7. Page `/api/anomalies` — filtre par cause
Permettre de filtrer les anomalies par type : `POLLUTION_SEVERE`, `SECHERESSE`, etc.

```python
@app.route('/api/anomalies')
def anomalies():
    cause = request.args.get('cause', None)
    anom = df[df['is_anomaly'] == 1]
    if cause:
        anom = anom[anom['cause'] == cause]
    ...
```

---

### 🟢 PRIORITÉ 3 — Nice to have

#### 8. Interface mobile agriculteur
Page `/mobile` simplifiée : état de la parcelle + recommandation Phoenix en gros texte.

#### 9. Export PDF rapport
Bouton "Télécharger rapport" → génère un PDF avec les données du mois.

```python
from reportlab.pdfgen import canvas
@app.route('/api/rapport/pdf')
def rapport_pdf():
    ...
```

#### 10. Corrélation SO2 → santé
Ajouter un indicateur estimé : *"SO2 actuel → +X cas respiratoires estimés"* basé sur la régression.

#### 11. LSTM pour prédiction 90 jours
Remplacer Ridge Regression par LSTM quand TensorFlow est disponible.
R² actuel : 0.67. LSTM attendu : 0.85+.

```python
# Dans le notebook — cellule future
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
model = Sequential([
    LSTM(64, input_shape=(30, 17)),
    Dense(1)
])
```

---

## 📓 NOTEBOOK — ÉTAT DES CELLULES

```
Cellule 1  ✅  Import & Merge des 11 CSV
Cellule 2  ✅  EDA + diagnostic qualité
Cellule 3  ✅  Nettoyage (clip négatifs, drop CH4)
Cellule 4  ✅  Feature engineering (23 features)
Cellule 5  ✅  Isolation Forest → anomaly_score, is_anomaly
Cellule 6  ✅  Random Forest → cause (95.5% accuracy)
Cellule 7  ✅  Ridge Regression → ndvi_target_30d (R²=0.67)
Cellule 8  ✅  Health Risk Index + Phoenix recommendations
Cellule 9  ⬜  [À FAIRE] Graphes de visualisation
Cellule 10 ⬜  [À FAIRE] Corrélation SO2 / santé
Cellule 11 ⬜  [À FAIRE] LSTM (optionnel)
```

### Cellule 9 — Visualisations (à créer)

```python
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv('data/combined_clean.csv')
df['date'] = pd.to_datetime(df['date'])

fig, axes = plt.subplots(3, 1, figsize=(14, 10), facecolor='#050d12')
fig.suptitle('Oasis Phoenix — Analyse 2019–2026', color='#00ff88', fontsize=14)

# SO2
ax1 = axes[0]
ax1.plot(df['date'], df['SO2_column_number_density']*1e6, color='#ff3355', linewidth=0.8, alpha=0.8)
ax1.fill_between(df['date'], df['SO2_column_number_density']*1e6, alpha=0.2, color='#ff3355')
ax1.set_facecolor('#080f16')
ax1.set_ylabel('SO₂ (µmol/m²)', color='#ff3355')
ax1.tick_params(colors='#4a7a5a')
anomalies = df[df['is_anomaly']==1]
ax1.scatter(anomalies['date'], anomalies['SO2_column_number_density']*1e6, color='#ffcc00', s=10, zorder=5, label='Anomalie IA')
ax1.legend(facecolor='#080f16', labelcolor='#ffcc00')

# NDVI
ax2 = axes[1]
ax2.plot(df['date'], df['NDVI'], color='#00ff88', linewidth=0.8)
ax2.fill_between(df['date'], df['NDVI'], 0.1, alpha=0.15, color='#00ff88')
ax2.axhline(0.2, color='#ffcc00', linestyle='--', linewidth=0.8, alpha=0.6, label='Seuil critique NDVI')
ax2.set_facecolor('#080f16')
ax2.set_ylabel('NDVI', color='#00ff88')
ax2.tick_params(colors='#4a7a5a')
ax2.legend(facecolor='#080f16', labelcolor='#ffcc00')

# Health Risk
ax3 = axes[2]
colors = df['health_risk_index'].apply(lambda x: '#ff3355' if x>=70 else '#ffcc00' if x>=40 else '#00ff88')
ax3.bar(df['date'], df['health_risk_index'], color=colors, width=1, alpha=0.8)
ax3.set_facecolor('#080f16')
ax3.set_ylabel('Indice Risque (0–100)', color='#c8f0d8')
ax3.tick_params(colors='#4a7a5a')

for ax in axes:
    ax.spines['bottom'].set_color('#1f2937')
    ax.spines['left'].set_color('#1f2937')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.grid(axis='y', color='#1f2937', linewidth=0.5)

plt.tight_layout()
plt.savefig('static/analysis.png', dpi=150, bbox_inches='tight', facecolor='#050d12')
plt.show()
print("✅ Graphe sauvegardé dans static/analysis.png")
```

---

## 🗂️ STRUCTURE FINALE DU PROJET

```
oasis_phoenix/
├── data/
│   ├── AER_Gabes.csv
│   ├── CH4_Gabes.csv          ← supprimé du pipeline (non fiable)
│   ├── CLOUD_Gabes.csv
│   ├── CO_Gabes.csv
│   ├── ERA5_Gabes.csv
│   ├── HCHO_Gabes.csv
│   ├── NDVI_Gabes.csv
│   ├── NDWI_Gabes.csv
│   ├── NO2_Gabes.csv
│   ├── O3_Gabes.csv
│   ├── SO2_Gabes.csv
│   └── combined_clean.csv     ← dataset final (2634 lignes, 23 colonnes)
├── models/
│   ├── isolation_forest.pkl   ← détection anomalies
│   ├── random_forest.pkl      ← classification causes
│   ├── ridge_regression.pkl   ← prédiction NDVI 30j
│   ├── scaler.pkl             ← StandardScaler Isolation Forest
│   └── scaler_ridge.pkl       ← StandardScaler Ridge
├── static/
│   └── analysis.png           ← graphes générés (à créer)
├── templates/
│   └── carte.html             ← carte interactive Leaflet animée
├── app.py                     ← API Flask (5 endpoints)
├── notebook.ipynb             ← pipeline complet
└── requirements.txt
```

---

## 📦 REQUIREMENTS.TXT COMPLET

```
pandas
numpy
scikit-learn
joblib
flask
matplotlib
seaborn
```

---

## 🔌 API ENDPOINTS

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Carte interactive Leaflet |
| `/api/latest` | GET | Dernière mesure + Phoenix + Risk |
| `/api/anomalies` | GET | 20 anomalies les plus critiques |
| `/api/predict` | GET | Prédiction NDVI 30 jours |
| `/api/history` | GET | Historique complet 2019–2026 |
| `/api/stats` | GET | Statistiques globales |
| `/api/zone/<name>` | GET | ⬜ À créer — détail par zone |
| `/api/rapport/pdf` | GET | ⬜ À créer — export PDF |

---

## 📊 RÉSULTATS MODÈLES

| Modèle | Rôle | Score | Méthode évaluation |
|--------|------|-------|-------------------|
| Isolation Forest | Détection anomalies | 132 anomalies (5%) | Non supervisé |
| Random Forest | Classification causes | 95.5% accuracy | Temporal split 2019–2023 / 2024–2026 |
| Ridge Regression | Prédiction NDVI 30j | R²=0.67, MAE=0.011 | Temporal split |

---

## 🌡️ SEUILS DE RÉFÉRENCE

| Polluant | Seuil OMS | Unité GEE | Valeur seuil GEE |
|----------|-----------|-----------|-----------------|
| SO₂ | 20 µg/m³ | mol/m² | 0.0000076 |
| NO₂ | 40 µg/m³ | mol/m² | 0.0000213 |
| CO | 10 mg/m³ | mol/m² | 0.0045 |
| O₃ | 100 µg/m³ | mol/m² | 0.0020 |
| NDVI critique | < 0.2 | index | 0.2 |
| NDVI mort | < 0.1 | index | 0.1 |

---

## 🌱 RECOMMANDATIONS PHOENIX

| Statut | Condition | Plante | Revenu | CO₂ | Délai |
|--------|-----------|--------|--------|-----|-------|
| 🔴 CRITIQUE | SO2 > 0.0007 OU (SO2 > 0.0004 ET NDVI < 0.14) | Atriplex | 800 TND/an | 4T/an | 36 mois |
| 🟡 DÉGRADÉE | SO2 > 0.0004 OU NDVI < 0.15 | Paulownia | 3 350 TND/an | 12T/an | 18 mois |
| 🟡 STRESS HYDRIQUE | NDWI < -0.1 ET NDVI < 0.16 | Moringa | 1 200 TND/an | 8T/an | 12 mois |
| 🟢 SAINE | Normal | Moringa (préventif) | 1 200 TND/an | 8T/an | 12 mois |

---

## 🎤 PITCH 45 SECONDES

> *"L'oasis de Gabès — seule oasis maritime de Méditerranée — disparaît silencieusement.
> Pollution industrielle, urbanisation illicite, nappes épuisées.
> Personne ne surveille de façon systématique.*
>
> *Oasis Phoenix change ça. Quatre satellites gratuits analysent chaque parcelle tous les cinq jours.
> Notre IA détecte chaque anomalie, identifie sa cause, prédit ce qui va se passer dans 90 jours.*
>
> *Et pour chaque zone menacée, un clic sur la carte suffit : le système affiche immédiatement quelle plante planter, quel revenu espérer, comment certifier des crédits carbone.*
> On transforme une catastrophe environnementale en opportunité économique concrète.*
>
> *Trois utilisateurs. Un seul système. Agriculteur, municipalité, chercheur — chacun reçoit exactement ce dont il a besoin, automatiquement, en temps réel."*

---

## 🗓️ PROCHAINES ÉTAPES IMMÉDIATES

```
[ ] 1. Ajouter NO2/CO/O3/AER dans /api/latest
[ ] 2. Ajouter graphe historique Chart.js dans carte.html
[ ] 3. Afficher la cause dans le panneau état actuel
[ ] 4. Créer cellule 9 notebook (visualisations)
[ ] 5. Auto-refresh 30 secondes
[ ] 6. Tester /api/anomalies?cause=POLLUTION_SEVERE
[ ] 7. Screenshot démo pour présentation
```

---

*Oasis Phoenix — Hackathon 2026 — Gabès, Tunisie*
