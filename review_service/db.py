"""MongoDB access layer.

Stores one document per review and computes per-drug average ratings with an
aggregation pipeline. A compound index on (drug_id ascending, created_at
descending) backs both the per-drug lookups and the newest-first ordering.
"""

from datetime import datetime, timezone

from pymongo import ASCENDING, DESCENDING, MongoClient

from .config import Config


class ReviewStore:
    def __init__(self, client=None, db_name=None, collection_name=None):
        self._client = client or MongoClient(Config.MONGO_URI)
        self._db = self._client[db_name or Config.MONGO_DB]
        self.collection = self._db[collection_name or Config.MONGO_COLLECTION]
        self.ensure_indexes()

    def ensure_indexes(self):
        self.collection.create_index(
            [("drug_id", ASCENDING), ("created_at", DESCENDING)],
            name="drug_id_created_at",
        )
        # Lets the backfill upsert idempotently on the source MySQL review id.
        self.collection.create_index(
            [("source_review_id", ASCENDING)],
            name="source_review_id_unique",
            unique=True,
            sparse=True,
        )

    def add_review(self, drug_id, review, rating, sentiment=None, user_id=None,
                   created_at=None, source_review_id=None, extra=None):
        doc = {
            "drug_id": int(drug_id),
            "review": review,
            "rating": int(rating),
            "sentiment": sentiment,
            "user_id": user_id,
            "created_at": created_at or datetime.now(timezone.utc),
        }
        if source_review_id is not None:
            doc["source_review_id"] = int(source_review_id)
        if extra:
            doc.update(extra)
        result = self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    def upsert_review(self, source_review_id, doc):
        """Insert or replace by source id - safe to re-run during backfill."""
        payload = dict(doc)
        payload["source_review_id"] = int(source_review_id)
        self.collection.update_one(
            {"source_review_id": int(source_review_id)},
            {"$set": payload},
            upsert=True,
        )

    def average_rating(self, drug_id):
        """Average rating and review count for one drug, via $match -> $group."""
        pipeline = [
            {"$match": {"drug_id": int(drug_id)}},
            {"$group": {
                "_id": "$drug_id",
                "average_rating": {"$avg": "$rating"},
                "review_count": {"$sum": 1},
            }},
        ]
        result = list(self.collection.aggregate(pipeline))
        if not result:
            return {"drug_id": int(drug_id), "average_rating": None, "review_count": 0}
        row = result[0]
        return {
            "drug_id": int(drug_id),
            "average_rating": round(row["average_rating"], 2),
            "review_count": row["review_count"],
        }

    def latest_reviews(self, drug_id, limit=20):
        cursor = (
            self.collection.find({"drug_id": int(drug_id)})
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        out = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            out.append(doc)
        return out

    def count(self):
        return self.collection.count_documents({})
