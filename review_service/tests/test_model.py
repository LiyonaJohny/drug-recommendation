"""Scorer tests: helpers, the lexicon baseline, and the trained model.

The lexicon and trained-model tests are skipped automatically if their
prerequisites (NLTK corpora / a trained model.joblib) are not available, so
the suite still passes on a bare checkout.
"""

import os

import pytest

from review_service.config import Config
from review_service.model import clean_text, star_from_probability


def test_clean_text_unescapes_and_trims():
    # HTML entities are decoded and runs of whitespace collapsed.
    assert clean_text("worked&#039;s  really   well") == "worked's really well"
    # UCI reviews are wrapped in double quotes; the wrapping quotes are removed.
    assert clean_text('"&quot;great&quot;"') == 'great'
    assert clean_text(None) == ""


@pytest.mark.parametrize("prob,stars", [
    (0.95, 5), (0.7, 4), (0.5, 3), (0.3, 2), (0.05, 1),
])
def test_star_from_probability(prob, stars):
    assert star_from_probability(prob) == stars


def _nltk_ready():
    try:
        import nltk  # noqa: F401
        from nltk.corpus import stopwords
        stopwords.words("english")
        nltk.pos_tag(["good"])
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _nltk_ready(), reason="NLTK data not installed")
def test_lexicon_baseline_direction():
    from review_service.model import LexiconBaseline
    b = LexiconBaseline()
    pos = b.score("This medicine was excellent and worked wonderfully, great relief.")
    neg = b.score("Horrible side effects, useless and painful, a terrible experience.")
    assert pos["sentiment"] == "positive"
    assert neg["sentiment"] == "negative"
    assert 1 <= pos["rating"] <= 5


@pytest.mark.skipif(not os.path.exists(Config.MODEL_PATH), reason="trained model not present")
def test_trained_model_classifies():
    from review_service.model import SentimentModel
    m = SentimentModel.load()
    pos = m.score("This drug completely cured my symptoms, I feel great with no side effects.")
    neg = m.score("Made everything worse, awful nausea and dizziness, would not recommend.")
    assert pos["sentiment"] == "positive"
    assert neg["sentiment"] == "negative"
    assert 1 <= pos["rating"] <= 5
