from flask import Flask, send_from_directory

app = Flask(__name__, static_folder="static")


@app.route("/")
def home():
    return send_from_directory(app.static_folder, "carte.html")


if __name__ == "__main__":
    app.run(debug=True)
