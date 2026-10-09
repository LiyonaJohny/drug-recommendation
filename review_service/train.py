"""Train the review classifier and write the model + metrics artifacts.

Downloads nothing itself; point it at the two UCI TSV files:

    python -m review_service.train \
        --train path/to/drugsComTrain_raw.tsv \
        --test  path/to/drugsComTest_raw.tsv

Writes artifacts/model.joblib and artifacts/metrics.json and prints the
model-vs-baseline comparison.
"""

import argparse
import json
import os

from .config import ARTIFACTS_DIR, Config
from .model import train


def main():
    parser = argparse.ArgumentParser(description="Train the drug-review sentiment model.")
    parser.add_argument("--train", required=True, help="path to drugsComTrain_raw.tsv")
    parser.add_argument("--test", required=True, help="path to drugsComTest_raw.tsv")
    parser.add_argument("--model-out", default=Config.MODEL_PATH)
    parser.add_argument("--metrics-out", default=str(ARTIFACTS_DIR / "metrics.json"))
    parser.add_argument("--baseline-sample", type=int, default=8000)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.model_out), exist_ok=True)
    metrics = train(
        train_tsv=args.train,
        test_tsv=args.test,
        model_out=args.model_out,
        metrics_out=args.metrics_out,
        baseline_sample=args.baseline_sample,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
