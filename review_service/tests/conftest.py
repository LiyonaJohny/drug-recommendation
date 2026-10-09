"""Shared test fixtures.

The database tests run against mongomock, so no real MongoDB is needed. The
API tests use a deterministic fake scorer so they stay fast and do not depend
on NLTK data or a trained model; the real scorers are exercised separately in
test_model.py.
"""

import mongomock
import pytest

from review_service.app import create_app
from review_service.db import ReviewStore


class FakeScorer:
    """Scores by a couple of keywords - deterministic and dependency-free."""

    def score(self, text):
        low = (text or "").lower()
        positive = any(w in low for w in ("good", "great", "effective", "helped"))
        return {
            "sentiment": "positive" if positive else "negative",
            "probability": 0.9 if positive else 0.1,
            "rating": 5 if positive else 1,
            "scorer": "fake",
        }


@pytest.fixture
def store():
    client = mongomock.MongoClient()
    return ReviewStore(client=client, db_name="test_db", collection_name="reviews")


@pytest.fixture
def app(store):
    scorer = FakeScorer()
    return create_app(store=store, model=scorer, baseline=scorer)


@pytest.fixture
def client(app):
    return app.test_client()
