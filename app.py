from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEXICON_PATH = os.path.join(BASE_DIR, "lexicon.json")

def load_lexicon():
    try:
        with open(LEXICON_PATH, "r") as f:
            return json.load(f)
    except:
        return {}

def save_lexicon():
    with open(LEXICON_PATH, "w") as f:
        json.dump(lexicon, f)

lexicon = load_lexicon()

@app.route("/")
def home():
    return "API is running"

@app.route("/lexicon", methods=["GET"])
def get_lexicon():
    return jsonify(lexicon)

@app.route("/add", methods=["POST"])
def add_word():
    data = request.json
    lexicon[data["english"]] = data["conlang"]
    save_lexicon()
    return jsonify({"status": "ok"})

@app.route("/translate", methods=["POST"])
def translate():
    text = request.json["text"].lower().split()
    result = [lexicon.get(w, f"[{w}]") for w in text]
    return jsonify({"result": " ".join(result)})

@app.route("/debug")
def debug():
    return {
        "lexicon": lexicon,
        "routes": str(app.url_map)
    }

if __name__ == "__main__":
    app.run(debug=True)

print(app.url_map)