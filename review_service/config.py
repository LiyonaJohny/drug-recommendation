"""Runtime configuration, read from environment variables with safe defaults.

A local .env file (see .env.example) is loaded automatically when present so
the service can be configured without exporting variables by hand.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"


class Config:
    # MongoDB
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.environ.get("MONGO_DB", "drug_reviews")
    MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "reviews")

    # Trained model + lexicon artifacts
    MODEL_PATH = os.environ.get("MODEL_PATH", str(ARTIFACTS_DIR / "model.joblib"))
    POSITIVE_LEXICON = os.environ.get(
        "POSITIVE_LEXICON", str(ARTIFACTS_DIR / "positive.txt")
    )
    NEGATIVE_LEXICON = os.environ.get(
        "NEGATIVE_LEXICON", str(ARTIFACTS_DIR / "negative.txt")
    )

    # Source MySQL database (used only by the backfill script)
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "drug_recomdendation")

    # Backfill tuning
    BACKFILL_BATCH_SIZE = int(os.environ.get("BACKFILL_BATCH_SIZE", "500"))
    BACKFILL_CHECKPOINT = os.environ.get(
        "BACKFILL_CHECKPOINT", str(BASE_DIR / "backfill_checkpoint.json")
    )
