from flask import Flask, render_template, send_from_directory
from routes import register_blueprints
from services.data_loader import get_dataframe
from culture import register_culture_blueprints

app = Flask(__name__)
register_blueprints(app)
register_culture_blueprints(app)

# ── Point d'entrée unifié
@app.route('/')
def index():
    return render_template('index.html')

# ── Dashboard collègues
@app.route('/dashboard')
def dashboard():
    return render_template('carte.html')

# ── Routes culture
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

get_dataframe(force=True)

if __name__ == '__main__':
    app.run(debug=True)