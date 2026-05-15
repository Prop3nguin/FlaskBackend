import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from functools import wraps

app = Flask(__name__)
CORS(app, origins=["https://prop3nguin.github.io"])

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- Models ---

class Word(db.Model):
    __tablename__ = "words"
    id          = db.Column(db.Integer, primary_key=True)
    word        = db.Column(db.String(100), nullable=False, unique=True)
    ipa         = db.Column(db.String(200))
    xsampa      = db.Column(db.String(200))
    word_type   = db.Column(db.String(50))
    etymology   = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    syllables   = db.relationship("WordSyllable", back_populates="word", cascade="all, delete")
    examples    = db.relationship("Example", back_populates="word", cascade="all, delete")

class Syllable(db.Model):
    __tablename__ = "syllables"
    id        = db.Column(db.Integer, primary_key=True)
    syllable  = db.Column(db.String(50), nullable=False, unique=True)
    use_count = db.Column(db.Integer, default=0)

class WordSyllable(db.Model):
    __tablename__ = "word_syllables"
    word_id      = db.Column(db.Integer, db.ForeignKey("words.id"), primary_key=True)
    syllable_id  = db.Column(db.Integer, db.ForeignKey("syllables.id"), primary_key=True)
    position     = db.Column(db.Integer)
    word         = db.relationship("Word", back_populates="syllables")
    syllable_rel = db.relationship("Syllable")

class Example(db.Model):
    __tablename__ = "examples"
    id               = db.Column(db.Integer, primary_key=True)
    word_id          = db.Column(db.Integer, db.ForeignKey("words.id"), nullable=False)
    valtare_sentence = db.Column(db.Text)
    translation      = db.Column(db.Text)
    word             = db.relationship("Word", back_populates="examples")

# --- Auth ---

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token != os.environ.get("SECRET_KEY"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# --- Routes ---

@app.route("/")
def home():
    return "WORKING"

@app.route("/lexicon", methods=["GET"])
def get_lexicon():
    words = Word.query.order_by(Word.word).all()
    return jsonify([serialize_word(w) for w in words])

@app.route("/lexicon/<int:word_id>", methods=["GET"])
def get_word(word_id):
    w = db.get_or_404(Word, word_id)
    return jsonify(serialize_word(w))

@app.route("/lexicon", methods=["POST"])
@require_auth
def add_word():
    data = request.get_json()
    w = Word(
        word      = data["word"],
        ipa       = data.get("ipa"),
        xsampa    = data.get("xsampa"),
        word_type = data.get("word_type"),
        etymology = data.get("etymology"),
    )
    db.session.add(w)
    db.session.flush()  # get w.id before committing

    # handle syllables
    for i, syl in enumerate(data.get("syllables", [])):
        s = Syllable.query.filter_by(syllable=syl).first()
        if not s:
            s = Syllable(syllable=syl, use_count=0)
            db.session.add(s)
            db.session.flush()
        s.use_count += 1
        db.session.add(WordSyllable(word_id=w.id, syllable_id=s.id, position=i))

    # handle examples
    for ex in data.get("examples", []):
        db.session.add(Example(
            word_id=w.id,
            valtare_sentence=ex.get("valtare"),
            translation=ex.get("translation")
        ))

    db.session.commit()
    return jsonify(serialize_word(w)), 201

@app.route("/lexicon/<int:word_id>", methods=["DELETE"])
@require_auth
def delete_word(word_id):
    w = db.get_or_404(Word, word_id)
    # decrement syllable use counts
    for ws in w.syllables:
        ws.syllable_rel.use_count = max(0, ws.syllable_rel.use_count - 1)
    db.session.delete(w)
    db.session.commit()
    return jsonify({"status": "deleted"})

@app.route("/init-db")
@require_auth
def init_db():
    db.create_all()
    return jsonify({"status": "tables created"})

@app.route("/syllables", methods=["GET"])
def get_syllables():
    syls = Syllable.query.order_by(Syllable.use_count.desc()).all()
    return jsonify([{"syllable": s.syllable, "use_count": s.use_count} for s in syls])

def serialize_word(w):
    return {
        "id":        w.id,
        "word":      w.word,
        "ipa":       w.ipa,
        "xsampa":    w.xsampa,
        "word_type": w.word_type,
        "etymology": w.etymology,
        "syllables": [
            {"syllable": ws.syllable_rel.syllable, "position": ws.position}
            for ws in sorted(w.syllables, key=lambda x: x.position)
        ],
        "examples":  [
            {"valtare": ex.valtare_sentence, "translation": ex.translation}
            for ex in w.examples
        ],
        "created_at": w.created_at.isoformat() if w.created_at else None,
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)