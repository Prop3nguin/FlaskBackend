from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

@app.route("/")
def home():
    return "WORKING"

@app.route("/translate", methods=["POST"])
def translate():
    return {"result": "test"}

@app.route("/lexicon")
def lexicon():
    return {}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)