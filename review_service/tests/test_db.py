"""MongoDB layer tests (mongomock-backed)."""

from datetime import datetime, timedelta, timezone


def test_add_and_count(store):
    assert store.count() == 0
    store.add_review(drug_id=5, review="worked well", rating=5, sentiment="positive")
    assert store.count() == 1


def test_average_rating_aggregation(store):
    store.add_review(drug_id=5, review="a", rating=4, sentiment="positive")
    store.add_review(drug_id=5, review="b", rating=2, sentiment="negative")
    store.add_review(drug_id=9, review="c", rating=5, sentiment="positive")

    result = store.average_rating(5)
    assert result["drug_id"] == 5
    assert result["review_count"] == 2
    assert result["average_rating"] == 3.0  # (4 + 2) / 2

    # a different drug is unaffected
    assert store.average_rating(9)["average_rating"] == 5.0


def test_average_rating_missing_drug(store):
    result = store.average_rating(123)
    assert result["review_count"] == 0
    assert result["average_rating"] is None


def test_upsert_is_idempotent(store):
    doc = {"drug_id": 5, "review": "x", "rating": 5}
    store.upsert_review(101, doc)
    store.upsert_review(101, doc)  # same source id again
    assert store.collection.count_documents({"source_review_id": 101}) == 1


def test_compound_index_exists(store):
    names = set(store.collection.index_information().keys())
    assert "drug_id_created_at" in names


def test_latest_reviews_newest_first(store):
    now = datetime.now(timezone.utc)
    store.add_review(drug_id=5, review="old", rating=3, created_at=now - timedelta(days=2))
    store.add_review(drug_id=5, review="new", rating=4, created_at=now)
    latest = store.latest_reviews(5, limit=5)
    assert [d["review"] for d in latest] == ["new", "old"]
