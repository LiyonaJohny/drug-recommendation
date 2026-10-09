"""Staged backfill of existing reviews from MySQL into MongoDB.

Copies the Django app's `review` table into the Mongo `reviews` collection in
batches ordered by review id. Progress is written to a checkpoint file after
every batch, so an interrupted run resumes where it left off. Writes are
upserts keyed on the source review id, so re-running never duplicates. At the
end it compares source and destination counts.

Usage:
    python -m review_service.backfill           # run / resume
    python -m review_service.backfill --reset   # start over from the beginning
"""

import argparse
import json
import os
from datetime import datetime, time, timezone

import MySQLdb

from .config import Config
from .db import ReviewStore


def _load_checkpoint(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {"last_rid": 0, "copied": 0}


def _save_checkpoint(path, state):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)


def _as_datetime(value):
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value
    # MySQL DATE comes back as a date; store it as midnight UTC.
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def connect_mysql():
    return MySQLdb.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        passwd=Config.MYSQL_PASSWORD,
        db=Config.MYSQL_DB,
        charset="utf8mb4",
    )


def run(batch_size=None, checkpoint_path=None, store=None, reset=False):
    batch_size = batch_size or Config.BACKFILL_BATCH_SIZE
    checkpoint_path = checkpoint_path or Config.BACKFILL_CHECKPOINT
    store = store or ReviewStore()

    if reset and os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    state = _load_checkpoint(checkpoint_path)
    conn = connect_mysql()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM review")
    source_total = cur.fetchone()[0]

    print(f"Source reviews: {source_total}. Resuming from rid > {state['last_rid']}.")

    while True:
        cur.execute(
            "SELECT rid, uid, med_id, date, review, rating FROM review "
            "WHERE rid > %s ORDER BY rid ASC LIMIT %s",
            (state["last_rid"], batch_size),
        )
        rows = cur.fetchall()
        if not rows:
            break

        for rid, uid, med_id, date, review, rating in rows:
            store.upsert_review(
                source_review_id=rid,
                doc={
                    "drug_id": int(med_id),
                    "user_id": uid,
                    "review": review,
                    "rating": int(rating),
                    "created_at": _as_datetime(date),
                },
            )
            state["last_rid"] = rid
            state["copied"] += 1

        _save_checkpoint(checkpoint_path, state)
        print(f"  copied up to rid {state['last_rid']} ({state['copied']} total)")

    dest_total = store.collection.count_documents({"source_review_id": {"$exists": True}})
    cur.close()
    conn.close()

    print("Backfill complete.")
    print(f"  MySQL reviews        : {source_total}")
    print(f"  Mongo backfilled docs: {dest_total}")
    if source_total == dest_total:
        print("  Counts match.")
    else:
        print("  WARNING: counts differ - investigate before trusting the copy.")
    return {"source_total": source_total, "dest_total": dest_total}


def main():
    parser = argparse.ArgumentParser(description="Backfill MySQL reviews into MongoDB.")
    parser.add_argument("--reset", action="store_true", help="ignore any checkpoint and start over")
    parser.add_argument("--batch-size", type=int, default=None)
    args = parser.parse_args()
    run(batch_size=args.batch_size, reset=args.reset)


if __name__ == "__main__":
    main()
