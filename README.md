# Drug Recommendation System

A machine-learning-based, symptom-aware medicine recommendation web application
built with **Django 4.0**, **MySQL**, **MongoDB**, and a **scikit-learn /
Flask** review-scoring service. Patients search for medicines and read
reviews; every review is automatically scored by an NLTK sentiment-analysis
pipeline that turns free-text into a 1–5 star rating, and medicines are ranked
by that rating. The platform also supports real-time patient–doctor chat and a
role-based workflow for four actors: **User (Patient), Doctor, Pharma Company,
and Admin**.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.9, Django 4.0.4 |
| Database | MySQL (via `mysqlclient`) |
| NLP / recommendation | NLTK (tokenising, POS-tagging, Porter stemming, sentiment lexicons) |
| Frontend | Django templates + Bootstrap 5 |

---

## Prerequisites

- **Python 3.9+**
- **MySQL server** running on `127.0.0.1:3306` (e.g. WAMP/XAMPP or standalone MySQL)
- `pip` for installing dependencies

---

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Download the required NLTK data

The sentiment engine needs these NLTK corpora/models. Run once:

```bash
python -c "import nltk; [nltk.download(p) for p in ['punkt','punkt_tab','stopwords','averaged_perceptron_tagger','averaged_perceptron_tagger_eng']]"
```

### 3. Create and load the database

Start your MySQL server first, then create the database and import the dump:

```bash
mysql -u root -e "CREATE DATABASE IF NOT EXISTS drug_recomdendation;"
mysql -u root drug_recomdendation < drug_recomdendation.sql
```

> The database connection is configured in `drugrecomendation/settings.py`
> (`NAME=drug_recomdendation`, `USER=root`, empty password, host `127.0.0.1`,
> port `3306`). Adjust these to match your MySQL setup if needed.

### 4. Apply Django's built-in migrations

The application's own tables (`user`, `login`, `med_details`, `review`, `chat…`,
etc.) come from the SQL dump and are marked `managed = False`, so Django does not
manage them. Django's own auth/admin/session tables still need migrating:

```bash
python manage.py migrate
```

### 5. Run the development server

```bash
python manage.py runserver
```

The app is then available at **http://127.0.0.1:8000/**.

---

## Demo accounts

These ship in the SQL dump (passwords are stored hashed after first login):

| Role | Email / Username | Password |
|------|------------------|----------|
| Admin | `admin@gmail.com` | `admin` |
| User | `pranav@gmail.com` | `23` |
| Company | `cipla@gmail.com` | `1234` |
| Doctor | `john@gmail.com` | `123` |

> New Company and Doctor accounts start **pending** and must be approved by the
> Admin (Companies / Doctors pages) before they can log in.

---

## How the recommendation engine works

When a patient submits a review, `review()` in `drugrecomendationapp/views.py`:

1. **Tokenises & POS-tags** the text with NLTK, keeping only nouns, verbs, and
   adjectives (the words that carry sentiment).
2. **Stems** each kept word to its root with the Porter Stemmer.
3. **Matches** the stemmed words against the `positive` and `negative` lexicon
   tables.
4. **Scores** the balance of positive vs. negative hits into a **1–5 star
   rating**, stored automatically — the patient never picks a star manually.

Medicine lists and search results are then ordered by each medicine's average
rating, so better-reviewed medicines surface first.

---

## Project structure

```
drugrecomendation/            # Django project (settings, urls, wsgi/asgi)
drugrecomendationapp/         # Main app
├── views.py                  # All view logic
├── models.py                 # ORM models (managed=False; tables from SQL dump)
├── forms.py                  # Medicine-upload form
├── templates/                # HTML templates (one dashboard per role)
├── static/                   # CSS, JS, images, video
└── migrations/               # Django migration state
drug_recomdendation.sql       # Database schema + seed data
requirements.txt              # Python dependencies
manage.py
review_service/               # Flask review-scoring microservice (see its README)
```

---

## Review scoring microservice

The sentiment scoring has been moved into a standalone Flask service in
[`review_service/`](review_service/README.md). It scores reviews with a
TF-IDF + Logistic Regression classifier trained on the UCI Drug Review dataset
(macro-F1 **0.88** vs the old NLTK lexicon scorer's **0.62** on a held-out test
set), stores reviews in MongoDB, and exposes per-drug average ratings. The
Django `review` view calls this service and falls back to the original inline
NLTK scorer if the service is unavailable, so reviews are never lost. See
`review_service/README.md` for the full comparison, API, Docker setup, and
backfill instructions.

---

## Why two databases?

The project uses two different databases, each for a different job:

- **MySQL** (`drug_recomdendation`) is the main application database. It holds
  everything the Django website runs on: users, logins, companies, doctors,
  medicines, reviews, chat messages and feedback. This is the database the app
  has always used, and it is what powers the pages and the medicine star
  ratings.
- **MongoDB** (`drug_reviews`) is used only by the review-scoring microservice.
  It stores each scored review as a document and serves per-drug average ratings
  through an aggregation pipeline. It was introduced with the microservice to
  keep the review-analytics workload separate from the transactional app data,
  and because a document store fits free-text reviews naturally.

They are complementary, not a replacement for one another. When a review is
submitted, the service writes it to MongoDB while Django still records it in
MySQL (so the existing medicine ranking, which reads MySQL, keeps working). The
`review_service/backfill.py` script performs a one-time copy of the existing
MySQL reviews into MongoDB so the document store starts with the full history.

MySQL is required to run the website. MongoDB is only needed when you run the
review microservice (for example via `docker compose up` in `review_service/`,
which starts a MongoDB container); the Django site runs without it, and the
review view falls back to the inline NLTK scorer when the service is not up.

---

## Notes

- `DEBUG = True` and the committed `SECRET_KEY` are for **local development
  only**. For any real deployment, set `DEBUG = False`, load `SECRET_KEY` from an
  environment variable, and configure `ALLOWED_HOSTS`.
- MySQL must be started **before** `runserver`; it does not auto-start after a
  reboot on most WAMP/XAMPP setups.
