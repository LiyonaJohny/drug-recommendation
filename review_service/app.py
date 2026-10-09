"""Application factory for the review scoring service.

Run directly for local development:

    python -m review_service.app

or through a WSGI server (gunicorn review_service.app:app) in a container.
Dependencies (model, lexicon baseline, Mongo store) are attached to the app so
they can be swapped for test doubles via create_app(...).
"""

import os

from flask import Flask

from .config import Config
from .model import LexiconBaseline, SentimentModel
from .reviews import bp as reviews_bp


def _load_model():
    try:
        return SentimentModel.load()
    except Exception:
        # No trained model on disk yet - the service still runs and scores
        # through the lexicon fallback until a model is trained.
        return None


def create_app(config_object=Config, store=None, model=None, baseline=None):
    app = Flask(__name__)
    app.config.from_object(config_object)

    if baseline is None:
        baseline = LexiconBaseline()
    if model is None:
        model = _load_model()
    if store is None:
        from .db import ReviewStore
        store = ReviewStore()

    app.extensions["review"] = {"model": model, "baseline": baseline, "store": store}
    app.register_blueprint(reviews_bp)
    return app


# Module-level app for WSGI servers.
app = None
if os.environ.get("REVIEW_SERVICE_EAGER", "1") == "1":
    try:
        app = create_app()
    except Exception:
        # Defer failures (e.g. Mongo not reachable at import time) to runtime.
        app = None


if __name__ == "__main__":
    if app is None:
        app = create_app()
    app.run(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "5005")))
