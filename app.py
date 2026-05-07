from flask import Flask, request, jsonify, session, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    return response

@app.route("/")
def home():
    return "WORKING"

if __name__ == "__main__":
    app.run(debug=True)
"""
@app.after_request
def after_request(response):
    response.headers.add(
        "Access-Control-Allow-Origin",
        "*"
    )

    response.headers.add(
        "Access-Control-Allow-Headers",
        "Content-Type,Authorization"
    )

    response.headers.add(
        "Access-Control-Allow-Methods",
        "GET,POST,OPTIONS"
    )

    return response

# -----------------------------
# CONFIG
# -----------------------------
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Fix Render postgres URL
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Restrict CORS to your GitHub Pages site


db = SQLAlchemy(app)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# -----------------------------
# DATABASE MODEL
# -----------------------------
class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    english = db.Column(db.String(100), unique=True, nullable=False)
    conlang = db.Column(db.String(100), nullable=False)

# Create tables
with app.app_context():
    db.create_all()

# -----------------------------
# AUTH DECORATOR
# -----------------------------
def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

# -----------------------------
# PUBLIC ROUTES (API)
# -----------------------------
@app.route("/")
def home():
    return "API is running v0.17"

@app.route("/", methods=["OPTIONS"])
def options():
    return make_response("", 200)

@app.route("/test")
def test():
    return "Test Works"

@app.route("/lexicon", methods=["GET"])
def get_lexicon():
    words = Word.query.all()
    return jsonify({w.english: w.conlang for w in words})

@app.route("/translate", methods=["POST", "OPTIONS"])
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
# LOGIN / AUTH
# -----------------------------
@app.route("/login", methods=["GET", "POST", "OPTIONS"])
def login():
    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")

        return "Wrong password"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -----------------------------
# ADMIN PANEL
# -----------------------------
@app.route("/admin")
@require_admin
def admin_panel():
    words = Word.query.all()
    return render_template("admin.html", words=words)

@app.route("/admin/add", methods=["POST", "OPTIONS"])
@require_admin
def admin_add():
    english = request.form.get("english", "").lower()
    conlang = request.form.get("conlang", "")

    if not english or not conlang:
        return redirect("/admin")

    existing = Word.query.filter_by(english=english).first()

    if existing:
        existing.conlang = conlang
    else:
        db.session.add(Word(english=english, conlang=conlang))

    db.session.commit()
    return redirect("/admin")

@app.route("/admin/delete/<int:id>", methods=["POST", "OPTIONS"])
@require_admin
def delete_word(id):
    word = Word.query.get(id)
    if word:
        db.session.delete(word)
        db.session.commit()
    return redirect("/admin")

# -----------------------------
# RUN LOCAL
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
"""