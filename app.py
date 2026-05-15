from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://prop3nguin.github.io"])  # lock it down

@app.route("/")
def home():
    return "WORKING"

@app.route("/lexicon", methods=["GET"])
def lexicon():
    return jsonify([])  # will return your words list once DB is wired up

@app.route("/lexicon", methods=["POST"])
def add_word():
    data = request.get_json()
    # add to DB here
    return jsonify({"status": "ok"}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)