import argparse
import os

import numpy as np
import pandas as pd


TRAITS = {
    "open_mindedness": {"pred": ["pred_open_mindedness", "pred_O"], "truth": ["open_mindedness", "O"]},
    "conscientiousness": {"pred": ["pred_conscientiousness", "pred_C"], "truth": ["conscientiousness", "C"]},
    "extraversion": {"pred": ["pred_extraversion", "pred_E"], "truth": ["extraversion", "E"]},
    "agreeableness": {"pred": ["pred_agreeableness", "pred_A"], "truth": ["agreeableness", "A"]},
    "negative_emotionality": {"pred": ["pred_negative_emotionality", "pred_N"], "truth": ["negative_emotionality", "N"]},
    }


def first_existing(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def pearson_corr(x, y):
    valid = pd.concat([x, y], axis=1).dropna()
    if len(valid) < 2:
        return np.nan
    if valid.iloc[:, 0].nunique() < 2 or valid.iloc[:, 1].nunique() < 2:
        return np.nan
    return float(valid.iloc[:, 0].corr(valid.iloc[:, 1], method="pearson"))


def mae(x, y):
    valid = pd.concat([x, y], axis=1).dropna()
    if valid.empty:
        return np.nan
    return float((valid.iloc[:, 0] - valid.iloc[:, 1]).abs().mean())


def main(args):
    predictions = pd.read_csv(args.pred_path)
    ground_truth = pd.read_csv(args.truth_path)

    if args.id_col not in predictions or args.id_col not in ground_truth:
        raise ValueError(f"Both files must contain id column: {args.id_col}")

    group_cols = [args.id_col]
    for optional_col in ["model_name", "backend", "try_id"]:
        if optional_col in predictions:
            group_cols.append(optional_col)

    merged = predictions.merge(ground_truth, on=args.id_col, suffixes=("_pred", "_true"))
    rows = []
    for trait, mapping in TRAITS.items():
        pred_col = first_existing(merged.columns, mapping["pred"])
        truth_col = first_existing(merged.columns, mapping["truth"])
        if not pred_col or not truth_col:
            raise ValueError(
                f"Missing columns for {trait}. "
                f"Prediction candidates={mapping['pred']}, truth candidates={mapping['truth']}."
                )
        rows.append({
            "trait": trait,
            "pcc": pearson_corr(merged[pred_col], merged[truth_col]),
            "mae": mae(merged[pred_col], merged[truth_col]),
            "n": int(pd.concat([merged[pred_col], merged[truth_col]], axis=1).dropna().shape[0]),
            "prediction_column": pred_col,
            "ground_truth_column": truth_col,
            })

    metrics = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(args.output_path) or ".", exist_ok=True)
    metrics.to_csv(args.output_path, index=False)
    print(metrics)
    print(f"Wrote evaluation metrics to {args.output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred_path", default="outputs/ocean_scores.csv")
    parser.add_argument("--truth_path", default="data/ground_truth.csv")
    parser.add_argument("--output_path", default="outputs/evaluation_metrics.csv")
    parser.add_argument("--id_col", default="session_id")
    main(parser.parse_args())
