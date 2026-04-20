from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import sqlite3, json, os, requests, math
from datetime import datetime, timedelta

from routes import register_blueprints
from services.data_loader import get_dataframe
from culture import register_culture_blueprints

load_dotenv()

app = Flask(__name__)
CORS(app)

# ── Config clustering ─────────────────────────────────────────────────────────
CLUSTER_RADIUS_KM   = 2.0   # rayon géo pour regrouper (2km)
CLUSTER_WINDOW_H    = 3     # fenêtre temporelle (3 heures)
CLUSTER_MIN_REPORTS = 3     # minimum pour déclencher une alerte
CLUSTER_SCORE_SEUIL = 0.65  # score confiance minimum

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "signalements.db")

# ── Base de données ───────────────────────────────────────────────────────────
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS signalements (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                texte       TEXT NOT NULL,
                langue      TEXT,
                type_env    TEXT,
                gravite     INTEGER,
                zone        TEXT,
                lat         REAL,
                lng         REAL,
                reponse_ia  TEXT,
                cluster_id  INTEGER,
                timestamp   TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clusters (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                type_env        TEXT,
                zone            TEXT,
                lat_centre      REAL,
                lng_centre      REAL,
                nb_signalements INTEGER DEFAULT 1,
                gravite_max     INTEGER DEFAULT 1,
                score_confiance REAL DEFAULT 0.0,
                resume_ia       TEXT,
                alerte_generee  INTEGER DEFAULT 0,
                actif           INTEGER DEFAULT 1,
                timestamp_debut TEXT,
                timestamp_maj   TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alertes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_id  INTEGER,
                titre       TEXT,
                message     TEXT,
                niveau      TEXT,
                nb_citoyens INTEGER,
                zone        TEXT,
                timestamp   TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    print("✅ Base de données signalements prête")

init_db()

# ── Helpers géo ───────────────────────────────────────────────────────────────
def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def coords_centre(lats, lngs):
    return sum(lats)/len(lats), sum(lngs)/len(lngs)

# ── Analyse IA : signalement individuel ──────────────────────────────────────
def analyser_signalement(texte):
    prompt = f"""Tu es un assistant environnemental expert de la région de Gabès (Oasis Phoenix).
Un citoyen soumet ce signalement :

"{texte}"

Réponds UNIQUEMENT avec un JSON valide, sans markdown ni explication :
{{
  "langue": "fr",
  "type_env": un parmi ["pollution_air","pollution_sol","pollution_eau","vegetation","sante","autre"],
  "gravite": entier 1 à 5,
  "zone": nom du quartier mentionné ou null,
  "reponse_citoyen": message au citoyen. 2-3 phrases. Remercie, confirme, donne un conseil concret.
}}"""

    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        res = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            },
            timeout=30
        )
        data = res.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return json.loads(raw)
    except Exception as e:
        print(f"⚠️  Erreur IA signalement: {e}")
        return {
            "langue": "fr", "type_env": "autre", "gravite": 3,
            "zone": None,
            "reponse_citoyen": "Merci pour votre signalement. Il a bien été enregistré."
        }

# ── Analyse IA : cluster ──────────────────────────────────────────────────────
def analyser_cluster(signalements, cluster):
    textes = "\n".join([f"- [{s['type_env']}] {s['texte']}" for s in signalements])
    nb     = len(signalements)
    zone   = cluster.get("zone") or "Gabès"

    prompt = f"""Tu es un expert en environnement et santé publique à Gabès, Tunisie.
{nb} citoyens ont signalé des problèmes similaires dans la zone "{zone}" en moins de {CLUSTER_WINDOW_H}h :

{textes}

Analyse cette situation collective et réponds UNIQUEMENT avec un JSON valide :
{{
  "resume": résumé factuel en français de la situation collective (2 phrases max),
  "niveau_alerte": un parmi ["INFO", "ATTENTION", "URGENT", "CRITIQUE"],
  "titre_alerte": titre court et percutant en français (max 8 mots),
  "recommandation_autorites": action concrète recommandée aux autorités (1 sentence),
  "score_confiance": float entre 0 et 1 (probabilité que ce soit un vrai problème environnemental),
  "facteurs": liste des 2-3 éléments qui renforcent la crédibilité du signalement collectif
}}"""

    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        res = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            },
            timeout=30
        )
        data = res.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return json.loads(raw)
    except Exception as e:
        print(f"⚠️  Erreur IA cluster: {e}")
        return {
            "resume": f"{nb} signalements similaires détectés dans la zone {zone}.",
            "niveau_alerte": "ATTENTION",
            "titre_alerte": f"Problème signalé à {zone}",
            "recommandation_autorites": "Vérification terrain recommandée.",
            "score_confiance": 0.7,
            "facteurs": ["Signalements multiples", "Zone commune"]
        }

# ── Moteur de clustering ──────────────────────────────────────────────────────
def run_clustering(new_sig_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        new_sig = dict(conn.execute("SELECT * FROM signalements WHERE id=?", (new_sig_id,)).fetchone())
        type_env = new_sig["type_env"]
        lat = new_sig["lat"] or 33.88
        lng = new_sig["lng"] or 9.99
        now = datetime.utcnow()
        window = (now - timedelta(hours=CLUSTER_WINDOW_H)).isoformat()
        clusters_actifs = conn.execute("SELECT * FROM clusters WHERE type_env = ? AND actif = 1 AND timestamp_debut >= ?", (type_env, window)).fetchall()
        matched_cluster = None
        for c in clusters_actifs:
            c = dict(c)
            dist = haversine(lat, lng, c["lat_centre"] or 33.88, c["lng_centre"] or 9.99)
            if dist <= CLUSTER_RADIUS_KM:
                matched_cluster = c
                break
        if matched_cluster:
            cluster_id = matched_cluster["id"]
            new_nb = matched_cluster["nb_signalements"] + 1
            new_grav = max(matched_cluster["gravite_max"], new_sig["gravite"] or 1)
            sigs_cluster = conn.execute("SELECT lat, lng FROM signalements WHERE cluster_id=?", (cluster_id,)).fetchall()
            lats = [s["lat"] or lat for s in sigs_cluster] + [lat]
            lngs = [s["lng"] or lng for s in sigs_cluster] + [lng]
            new_lat, new_lng = coords_centre(lats, lngs)
            conn.execute("UPDATE clusters SET nb_signalements=?, gravite_max=?, lat_centre=?, lng_centre=?, timestamp_maj=datetime('now') WHERE id=?", (new_nb, new_grav, new_lat, new_lng, cluster_id))
            conn.execute("UPDATE signalements SET cluster_id=? WHERE id=?", (cluster_id, new_sig_id))
            conn.commit()
            result = {"cluster_id": cluster_id, "cluster_nb": new_nb, "is_new_cluster": False, "alerte": None}
            if new_nb >= CLUSTER_MIN_REPORTS and not matched_cluster["alerte_generee"]:
                result["alerte"] = declencher_alerte(cluster_id, conn)
            return result
        else:
            cur = conn.execute("INSERT INTO clusters (type_env, zone, lat_centre, lng_centre, nb_signalements, gravite_max, timestamp_debut) VALUES (?,?,?,?,1,?,datetime('now'))", (type_env, new_sig["zone"], lat, lng, new_sig["gravite"] or 1))
            cluster_id = cur.lastrowid
            conn.execute("UPDATE signalements SET cluster_id=? WHERE id=?", (cluster_id, new_sig_id))
            conn.commit()
            return {"cluster_id": cluster_id, "cluster_nb": 1, "is_new_cluster": True, "alerte": None}

def declencher_alerte(cluster_id, conn):
    cluster = dict(conn.execute("SELECT * FROM clusters WHERE id=?", (cluster_id,)).fetchone())
    sigs = [dict(r) for r in conn.execute("SELECT * FROM signalements WHERE cluster_id=?", (cluster_id,)).fetchall()]
    analyse = analyser_cluster(sigs, cluster)
    score = analyse.get("score_confiance", 0.7)
    conn.execute("UPDATE clusters SET resume_ia=?, score_confiance=?, alerte_generee=1 WHERE id=?", (analyse.get("resume"), score, cluster_id))
    if score >= CLUSTER_SCORE_SEUIL:
        conn.execute("INSERT INTO alertes (cluster_id, titre, message, niveau, nb_citoyens, zone) VALUES (?,?,?,?,?,?)", (cluster_id, analyse.get("titre_alerte"), analyse.get("resume") + " | " + analyse.get("recommandation_autorites",""), analyse.get("niveau_alerte"), cluster["nb_signalements"], cluster["zone"] or "Gabès"))
        conn.commit()
    else:
        conn.commit()
    return {"niveau": analyse.get("niveau_alerte"), "titre": analyse.get("titre_alerte"), "resume": analyse.get("resume"), "recommandation": analyse.get("recommandation_autorites"), "score_confiance": score, "facteurs": analyse.get("facteurs", []), "alerte_publiee": score >= CLUSTER_SCORE_SEUIL}

# ── Enregistrement des Blueprints existants
register_blueprints(app)
register_culture_blueprints(app)

# ── Routes existantes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('carte.html')

@app.route('/culture')
def culture_home():
    return send_from_directory('static/culture', 'carte_culture.html')

@app.route('/culture/resultats')
def culture_resultats():
    return send_from_directory('static/culture', 'resultats_culture.html')

@app.route('/culture/carbone')
def culture_carbone():
    return send_from_directory('static/culture', 'dashboard_carbone.html')

@app.route('/culture/intro')
def culture_intro():
    return send_from_directory('static/culture', 'intro.html')

# ── Routes Gabès Voix (Signalements)
@app.route("/reclamation")
def reclamation_index():
    return render_template("reclamation_index.html")

@app.route("/reclamation/dashboard")
def reclamation_dashboard():
    return render_template("reclamation_dashboard.html")

@app.route("/api/signaler", methods=["POST"])
def signaler():
    data  = request.get_json()
    texte = data.get("texte", "").strip()
    lat   = data.get("lat")
    lng   = data.get("lng")
    if not texte: return jsonify({"error": "Texte vide"}), 400
    analyse = analyser_signalement(texte)
    final_zone = analyse.get("zone") or data.get("zone")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("INSERT INTO signalements (texte, langue, type_env, gravite, zone, lat, lng, reponse_ia) VALUES (?,?,?,?,?,?,?,?)", (texte, analyse.get("langue"), analyse.get("type_env"), analyse.get("gravite"), final_zone, lat, lng, analyse.get("reponse_citoyen")))
        conn.commit()
        sig_id = cur.lastrowid
    cl = run_clustering(sig_id)
    return jsonify({"id": sig_id, "reponse": analyse.get("reponse_citoyen"), "type_env": analyse.get("type_env"), "gravite": analyse.get("gravite"), "langue": analyse.get("langue"), "zone": final_zone, "cluster_id": cl["cluster_id"], "cluster_nb": cl["cluster_nb"], "is_new_cluster": cl["is_new_cluster"], "alerte": cl["alerte"]})

@app.route("/api/signalements")
def get_signalements():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM signalements ORDER BY timestamp DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/clusters")
def get_clusters():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT c.*, (SELECT COUNT(*) FROM signalements WHERE cluster_id=c.id) as nb_reel FROM clusters c WHERE c.actif=1 ORDER BY c.timestamp_maj DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/alertes")
def get_alertes():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM alertes ORDER BY timestamp DESC LIMIT 20").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/stats_signalements")
def stats_signalements():
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM signalements").fetchone()[0]
        critiques = conn.execute("SELECT COUNT(*) FROM signalements WHERE gravite>=4").fetchone()[0]
        recent = conn.execute("SELECT COUNT(*) FROM signalements WHERE timestamp>=datetime('now','-24 hours')").fetchone()[0]
        clusters = conn.execute("SELECT COUNT(*) FROM clusters WHERE actif=1").fetchone()[0]
        alertes = conn.execute("SELECT COUNT(*) FROM alertes").fetchone()[0]
        par_type = conn.execute("SELECT type_env, COUNT(*) FROM signalements GROUP BY type_env").fetchall()
    return jsonify({"total": total, "critiques": critiques, "recent_24h": recent, "clusters_actifs": clusters, "alertes_total": alertes, "par_type": {r[0]: r[1] for r in par_type}})


if __name__ == '__main__':
    print("🌿 OASIS PHOENIX — Integrated Gabès Voix")
    app.run(debug=True, port=5001)
