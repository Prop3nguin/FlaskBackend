from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
CORS(app)

# -----------------------------
# DATABASE CONFIG (Render-safe)
# -----------------------------
uri = os.getenv("DATABASE_URL")

if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------
# DATABASE MODEL
# -----------------------------
class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    english = db.Column(db.String(100), unique=True, nullable=False)
    conlang = db.Column(db.String(100), nullable=False)

# Create tables (runs once safely)
with app.app_context():
    db.create_all()

# -----------------------------
# ROUTES
# -----------------------------

# Health check
@app.route("/")
def home():
    return "API is running"

# Get full lexicon
@app.route("/lexicon", methods=["GET"])
def get_lexicon():
    words = Word.query.all()
    result = {w.english: w.conlang for w in words}
    return jsonify(result)

# Add or update word
@app.route("/add", methods=["POST"])
def add_word():
    data = request.json

    if not data or "english" not in data or "conlang" not in data:
        return jsonify({"error": "Invalid input"}), 400

    english = data["english"].lower()
    conlang = data["conlang"]

    existing = Word.query.filter_by(english=english).first()

    if existing:
        existing.conlang = conlang
    else:
        new_word = Word(english=english, conlang=conlang)
        db.session.add(new_word)

    db.session.commit()
    return jsonify({"status": "ok"})

# Translate text
@app.route("/translate", methods=["POST"])
def translate():
    data = request.json

    if not data or "text" not in data:
        return jsonify({"error": "Invalid input"}), 400

    words = data["text"].lower().split()
    result = []

    for word in words:
        entry = Word.query.filter_by(english=word).first()
        result.append(entry.conlang if entry else f"[{word}]")

    return jsonify({"result": " ".join(result)})

# -----------------------------
# LOCAL RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)