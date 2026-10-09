"""Review scoring microservice for the Drug Recommendation System.

A small Flask application that scores free-text drug reviews with a
TF-IDF + Logistic Regression classifier trained on the UCI Drug Review
dataset, stores the reviews in MongoDB, and exposes average ratings per
drug. It replaces the inline NLTK lexicon scorer used by the Django app
while keeping that scorer available as a fallback and as a baseline.
"""

__version__ = "1.0.0"
