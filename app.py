from flask import Flask, render_template

from routes import register_blueprints
from services.data_loader import get_dataframe

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('carte.html')


register_blueprints(app)

# Warm dataset cache on startup.
get_dataframe(force=True)


if __name__ == '__main__':
    app.run(debug=True)