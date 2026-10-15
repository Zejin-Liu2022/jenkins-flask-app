"""Flask application for the Jenkins CI/CD lab."""

import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello, CI/CD with Jenkins!"


@app.route("/health")
def health():
    return jsonify(status="ok", revision=os.environ.get("APP_REVISION", "development"))


if __name__ == "__main__":  # pragma: no cover
    app.run(host="127.0.0.1", port=int(os.environ.get("APP_PORT", "5001")))
