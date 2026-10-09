"""HTTP endpoints for scoring and reading reviews."""

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("reviews", __name__)


def _components():
    return current_app.extensions["review"]


@bp.post("/reviews")
def create_review():
    """Score a review and store it.

    Body (JSON): {"drug_id": int, "review": str, "user_id": optional}
    Uses the trained model; falls back to the lexicon scorer if the model is
    unavailable so a scoring request never hard-fails.
    """
    data = request.get_json(silent=True) or {}
    drug_id = data.get("drug_id")
    review = data.get("review")

    if drug_id is None or review is None or str(review).strip() == "":
        return jsonify({"error": "drug_id and review are required"}), 400
    try:
        drug_id = int(drug_id)
    except (TypeError, ValueError):
        return jsonify({"error": "drug_id must be an integer"}), 400

    comp = _components()
    model, baseline, store = comp["model"], comp["baseline"], comp["store"]

    if model is not None:
        try:
            scored = model.score(review)
        except Exception:
            scored = baseline.score(review)
    else:
        scored = baseline.score(review)

    doc = store.add_review(
        drug_id=drug_id,
        review=review,
        rating=scored["rating"],
        sentiment=scored["sentiment"],
        user_id=data.get("user_id"),
    )

    return jsonify({
        "id": str(doc["_id"]),
        "drug_id": drug_id,
        "rating": scored["rating"],
        "sentiment": scored["sentiment"],
        "scorer": scored.get("scorer"),
    }), 201


@bp.get("/drugs/<int:drug_id>/rating")
def drug_rating(drug_id):
    """Average rating and review count for a drug."""
    store = _components()["store"]
    return jsonify(store.average_rating(drug_id))


@bp.get("/health")
def health():
    comp = _components()
    return jsonify({
        "status": "ok",
        "model_loaded": comp["model"] is not None,
    })
