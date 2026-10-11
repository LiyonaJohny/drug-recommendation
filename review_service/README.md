# Review Scoring Service

*Added in 2026 to extend the Drug Recommendation System (originally my MCA project, 2022–2023).*

A Flask microservice that scores free-text drug reviews with a machine-learning
classifier, stores them in MongoDB, and serves per-drug average ratings. It
replaces the inline NLTK opinion-lexicon scorer that the Django Drug
Recommendation System used, and keeps that lexicon scorer as both the baseline
it is measured against and the runtime fallback.

## Why replace the lexicon scorer

The original scorer counted positive and negative dictionary words (the Hu & Liu
opinion lexicon) in each review and turned the balance into a star rating. It is
simple but shallow: it ignores word order, negation and context, and only reacts
to words that happen to be in the lexicon.

The replacement is a TF-IDF + Logistic Regression classifier trained on the
[UCI Drug Review dataset](https://archive.ics.uci.edu/ml/datasets/Drug+Review+Dataset+%28Drugs.com%29)
(~215,000 drugs.com reviews). Reviews rated 7-10 are treated as positive and
1-4 as negative (the ambiguous 5-6 band is dropped), the standard binarisation
for this dataset.

## Results

Both scorers were evaluated on the same held-out UCI test split. The classifier
is scored on the full test set; both are scored on an identical 8,000-review
sample for a like-for-like comparison (the lexicon scorer's POS-tagging makes
the full set slow). Numbers come from `artifacts/metrics.json`, produced by the
training run.

| Scorer | Accuracy | F1 (positive) | Macro-F1 |
|--------|---------:|--------------:|---------:|
| TF-IDF + Logistic Regression | **0.90** | **0.93** | **0.88** |
| NLTK opinion-lexicon baseline | 0.66 | 0.74 | 0.62 |

*(8,000-review held-out sample. On the full 48,937-review test set the
classifier scores accuracy 0.8985, F1 0.9278, macro-F1 0.8785.)*

- Training examples: 146,941
- Test examples (full): 48,937
- The macro-F1 jump from **0.62 to 0.88** is the headline: the classifier is far
  more balanced across both positive and negative reviews, where the lexicon
  scorer leans positive and misses negative sentiment it has no words for.

To reproduce, download the dataset and run the training (see below); the table
is regenerated into `artifacts/metrics.json`.

## Architecture

```
Django app  --HTTP /reviews-->  Flask service  --score-->  TF-IDF + LogReg model
     |                               |
     |                               +--store--> MongoDB (reviews collection)
     |
     +-- if the service is down, falls back to the inline NLTK scorer
```

- `app.py` - application factory, wires the model, baseline and Mongo store and
  registers the blueprint.
- `reviews.py` - `POST /reviews` (score + store) and `GET /drugs/<id>/rating`.
- `model.py` - the classifier wrapper, the lexicon baseline, and the training
  routine.
- `db.py` - MongoDB layer: one document per review, a compound index on
  `(drug_id, created_at desc)`, and an aggregation pipeline (`$match` -> `$group`)
  for average ratings.
- `backfill.py` - staged, resumable, idempotent copy of the existing MySQL
  reviews into MongoDB.

## API

Score and store a review:

```
POST /reviews
{ "drug_id": 5, "review": "This worked well with no side effects", "user_id": 3 }
-> 201
{ "id": "...", "drug_id": 5, "rating": 5, "sentiment": "positive", "scorer": "model" }
```

Average rating for a drug:

```
GET /drugs/5/rating
-> 200
{ "drug_id": 5, "average_rating": 4.2, "review_count": 37 }
```

## Running it

### With Docker (includes MongoDB)

```
cd review_service
docker compose up --build
```

The service listens on `http://localhost:5005` and MongoDB on `localhost:27017`.

### Locally

Requires a MongoDB reachable at `MONGO_URI` (default `mongodb://localhost:27017`).

```
pip install -r requirements.txt
python -m nltk.downloader punkt punkt_tab stopwords averaged_perceptron_tagger averaged_perceptron_tagger_eng
python -m review_service.app        # from the project root
```

Configuration is read from environment variables (see `.env.example`).

## Training the model

```
# 1. download the dataset
curl -L -o drugsCom_raw.zip \
  https://archive.ics.uci.edu/ml/machine-learning-databases/00462/drugsCom_raw.zip
unzip drugsCom_raw.zip

# 2. train (writes artifacts/model.joblib and artifacts/metrics.json)
python -m review_service.train \
  --train drugsComTrain_raw.tsv \
  --test  drugsComTest_raw.tsv
```

A pre-trained `artifacts/model.joblib` is committed, so the service runs without
retraining.

## Backfilling existing reviews

Copies the Django app's MySQL `review` table into MongoDB in batches, writing a
checkpoint after each batch so it can resume, and upserting on the source review
id so re-running is safe:

```
python -m review_service.backfill          # run or resume
python -m review_service.backfill --reset  # start over
```

It prints source and destination counts at the end and flags any mismatch.

## Tests

```
pip install -r requirements.txt
python -m pytest
```

The database and API tests run against `mongomock`, so no MongoDB instance is
needed. The model tests skip automatically if the NLTK data or the trained model
are not present.

## Integration with the Django app

`drugrecomendationapp/views.py::review` posts each new review to this service and
stores the returned rating in MySQL (which the medicine pages rank by). If the
service cannot be reached within `REVIEW_SERVICE_TIMEOUT` seconds, it falls back
to the inline NLTK scorer so no review is ever lost. The service URL and timeout
are set in `drugrecomendation/settings.py` (`REVIEW_SERVICE_URL`,
`REVIEW_SERVICE_TIMEOUT`).
