"""Sentiment scoring: the TF-IDF + Logistic Regression model and the
NLTK lexicon baseline it is measured against.

Both scorers answer the same question for a review: positive or negative,
with a 1-5 star rating derived from it. The classifier is the production
scorer; the lexicon scorer mirrors the logic the Django app used inline and
serves as the baseline in the comparison and as a runtime fallback.
"""

import html
import json
import re

import joblib

from .config import Config

# ---------------------------------------------------------------------------
# Shared label scheme
# ---------------------------------------------------------------------------
# The UCI reviews are rated 1-10. We treat >= 7 as positive and <= 4 as
# negative, dropping the ambiguous 5-6 band - the standard binarisation for
# this dataset. The app itself stores a 1-5 star rating, so a probability is
# mapped back onto that 1-5 scale for storage and display.

POSITIVE = 1
NEGATIVE = 0


def clean_text(text):
    """Normalise raw review text (the UCI set is HTML-escaped and quoted)."""
    if text is None:
        return ""
    text = html.unescape(str(text))
    text = text.strip().strip('"')
    text = re.sub(r"\s+", " ", text)
    return text


def star_from_probability(prob_positive):
    """Map a positive-class probability onto a 1-5 star rating."""
    if prob_positive >= 0.80:
        return 5
    if prob_positive >= 0.60:
        return 4
    if prob_positive >= 0.40:
        return 3
    if prob_positive >= 0.20:
        return 2
    return 1


# ---------------------------------------------------------------------------
# Production scorer: trained TF-IDF + Logistic Regression
# ---------------------------------------------------------------------------
class SentimentModel:
    """Wraps the trained scikit-learn pipeline loaded from disk."""

    def __init__(self, pipeline):
        self.pipeline = pipeline

    @classmethod
    def load(cls, path=None):
        path = path or Config.MODEL_PATH
        return cls(joblib.load(path))

    def _positive_index(self):
        classes = list(self.pipeline.classes_)
        return classes.index(POSITIVE)

    def score(self, text):
        """Return sentiment, positive-probability and a 1-5 star rating."""
        cleaned = clean_text(text)
        prob = float(self.pipeline.predict_proba([cleaned])[0][self._positive_index()])
        return {
            "sentiment": "positive" if prob >= 0.5 else "negative",
            "probability": round(prob, 4),
            "rating": star_from_probability(prob),
            "scorer": "model",
        }


# ---------------------------------------------------------------------------
# Baseline scorer: the NLTK opinion-lexicon approach the Django app used
# ---------------------------------------------------------------------------
class LexiconBaseline:
    """Replicates the inline scorer: tokenise, drop stopwords, keep nouns/
    verbs/adjectives, Porter-stem, then count hits against the Hu & Liu
    positive/negative word lists. Both the tokens and the lexicons are
    stemmed so the match is applied consistently.
    """

    _CONTENT_TAGS = {
        "NN", "NNS", "NNP", "NNPS",
        "JJ", "JJR", "JJS",
        "VB", "VBD", "VBG", "VBN", "VBP", "VBZ",
    }

    def __init__(self, positive_path=None, negative_path=None):
        import nltk
        from nltk.corpus import stopwords
        from nltk.stem import PorterStemmer

        self._nltk = nltk
        self._stemmer = PorterStemmer()
        self._stopwords = set(stopwords.words("english"))

        pos = self._read_words(positive_path or Config.POSITIVE_LEXICON)
        neg = self._read_words(negative_path or Config.NEGATIVE_LEXICON)
        self._positive = {self._stemmer.stem(w) for w in pos}
        self._negative = {self._stemmer.stem(w) for w in neg}

    @staticmethod
    def _read_words(path):
        with open(path, encoding="utf-8") as fh:
            return [line.strip().lower() for line in fh if line.strip()]

    def counts(self, text):
        cleaned = clean_text(text).lower()
        pos_hits = neg_hits = 0
        for sentence in self._nltk.sent_tokenize(cleaned):
            tokens = [t for t in self._nltk.word_tokenize(sentence) if t not in self._stopwords]
            tagged = self._nltk.pos_tag(tokens)
            for word, tag in tagged:
                if tag not in self._CONTENT_TAGS:
                    continue
                stem = self._stemmer.stem(word)
                if stem in self._positive:
                    pos_hits += 1
                elif stem in self._negative:
                    neg_hits += 1
        return pos_hits, neg_hits

    def predict(self, text):
        """Binary prediction. Ties and no-hits fall back to the majority
        (positive) class, matching the app's non-negative default."""
        pos_hits, neg_hits = self.counts(text)
        if neg_hits > pos_hits:
            return NEGATIVE
        return POSITIVE

    def score(self, text):
        pos_hits, neg_hits = self.counts(text)
        total = pos_hits + neg_hits
        if total == 0:
            rating = 3
        else:
            senti = (pos_hits - neg_hits) / total
            rating = int(round((senti + 1) / 2 * 4)) + 1  # map [-1,1] -> [1,5]
            rating = max(1, min(5, rating))
        return {
            "sentiment": "negative" if neg_hits > pos_hits else "positive",
            "positive_hits": pos_hits,
            "negative_hits": neg_hits,
            "rating": rating,
            "scorer": "lexicon",
        }


# ---------------------------------------------------------------------------
# Training + evaluation
# ---------------------------------------------------------------------------
def _load_frame(path):
    import pandas as pd

    df = pd.read_csv(path, sep="\t")
    df = df[["review", "rating"]].dropna()
    df["review"] = df["review"].map(clean_text)
    df = df[df["review"].str.len() > 0]
    # binarise: >=7 positive, <=4 negative, drop the ambiguous middle
    df = df[(df["rating"] >= 7) | (df["rating"] <= 4)].copy()
    df["label"] = (df["rating"] >= 7).astype(int)
    return df


def train(train_tsv, test_tsv, model_out=None, metrics_out=None, baseline_sample=8000,
          random_state=42):
    """Train the classifier, evaluate it and the lexicon baseline on the same
    held-out test sample, persist the model and return the metrics."""
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.pipeline import Pipeline

    model_out = model_out or Config.MODEL_PATH

    train_df = _load_frame(train_tsv)
    test_df = _load_frame(test_tsv)

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=20000,
            min_df=5,
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("clf", LogisticRegression(max_iter=1000, C=4.0, class_weight="balanced")),
    ])

    pipeline.fit(train_df["review"], train_df["label"])

    # Full test set for the model (vectorise + predict is cheap)
    model_pred_full = pipeline.predict(test_df["review"])
    model_metrics_full = {
        "accuracy": round(accuracy_score(test_df["label"], model_pred_full), 4),
        "f1": round(f1_score(test_df["label"], model_pred_full), 4),
        "f1_macro": round(f1_score(test_df["label"], model_pred_full, average="macro"), 4),
    }

    # Apples-to-apples sample for the baseline (POS-tagging is the slow part)
    sample = test_df.sample(
        n=min(baseline_sample, len(test_df)), random_state=random_state
    ).reset_index(drop=True)

    baseline = LexiconBaseline()
    baseline_pred = np.array([baseline.predict(t) for t in sample["review"]])
    model_pred_sample = pipeline.predict(sample["review"])
    y_sample = sample["label"].to_numpy()

    def _m(pred):
        return {
            "accuracy": round(accuracy_score(y_sample, pred), 4),
            "f1": round(f1_score(y_sample, pred), 4),
            "f1_macro": round(f1_score(y_sample, pred, average="macro"), 4),
        }

    metrics = {
        "dataset": "UCI Drug Review (drugs.com)",
        "train_examples": int(len(train_df)),
        "test_examples_full": int(len(test_df)),
        "comparison_sample": int(len(sample)),
        "label_scheme": "rating>=7 positive, <=4 negative, 5-6 dropped",
        "model_full_test": model_metrics_full,
        "comparison": {
            "model": _m(model_pred_sample),
            "lexicon_baseline": _m(baseline_pred),
        },
    }

    joblib.dump(pipeline, model_out)
    if metrics_out:
        with open(metrics_out, "w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2)
    return metrics
