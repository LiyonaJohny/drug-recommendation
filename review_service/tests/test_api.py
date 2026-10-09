"""HTTP endpoint tests (Flask test client + mongomock + fake scorer)."""


def test_post_review_scores_and_stores(client, store):
    resp = client.post("/reviews", json={"drug_id": 5, "review": "this helped a lot, great"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["drug_id"] == 5
    assert body["sentiment"] == "positive"
    assert body["rating"] == 5
    assert store.count() == 1


def test_post_review_negative(client):
    resp = client.post("/reviews", json={"drug_id": 7, "review": "terrible, made me sick"})
    assert resp.status_code == 201
    assert resp.get_json()["sentiment"] == "negative"


def test_post_review_requires_fields(client):
    assert client.post("/reviews", json={"drug_id": 5}).status_code == 400
    assert client.post("/reviews", json={"review": "hi"}).status_code == 400
    assert client.post("/reviews", json={"drug_id": 5, "review": "  "}).status_code == 400


def test_post_review_bad_drug_id(client):
    resp = client.post("/reviews", json={"drug_id": "abc", "review": "good"})
    assert resp.status_code == 400


def test_drug_rating_endpoint(client):
    client.post("/reviews", json={"drug_id": 5, "review": "good and effective"})
    client.post("/reviews", json={"drug_id": 5, "review": "awful"})
    resp = client.get("/drugs/5/rating")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["drug_id"] == 5
    assert body["review_count"] == 2
    assert body["average_rating"] == 3.0  # (5 + 1) / 2


def test_drug_rating_unknown_drug(client):
    body = client.get("/drugs/999/rating").get_json()
    assert body["review_count"] == 0
    assert body["average_rating"] is None


def test_health(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok"
