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

GROUP_CANDIDATES = ["model_name", "backend", "try_id"]


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


def metric_rows_for_group(group_df, group_values=None):
    rows = []
    group_values = group_values or {}
    for trait, mapping in TRAITS.items():
        pred_col = first_existing(group_df.columns, mapping["pred"])
        truth_col = first_existing(group_df.columns, mapping["truth"])
        if not pred_col or not truth_col:
            raise ValueError(
                f"Missing columns for {trait}. "
                f"Prediction candidates={mapping['pred']}, truth candidates={mapping['truth']}."
                )
        row = {
            **group_values,
            "trait": trait,
            "pcc": pearson_corr(group_df[pred_col], group_df[truth_col]),
            "mae": mae(group_df[pred_col], group_df[truth_col]),
            "n": int(pd.concat([group_df[pred_col], group_df[truth_col]], axis=1).dropna().shape[0]),
            "prediction_column": pred_col,
            "ground_truth_column": truth_col,
            }
        rows.append(row)
    return rows


def evaluate_predictions(predictions, ground_truth, id_col="session_id"):
    if id_col not in predictions or id_col not in ground_truth:
        raise ValueError(f"Both files must contain id column: {id_col}")

    merged = predictions.merge(ground_truth, on=id_col, suffixes=("_pred", "_true"))
    group_cols = [col for col in GROUP_CANDIDATES if col in merged.columns]

    rows = []
    if group_cols:
        grouped = merged.groupby(group_cols, dropna=False, sort=True)
        for group_key, group_df in grouped:
            if len(group_cols) == 1:
                group_values = {group_cols[0]: group_key[0] if isinstance(group_key, tuple) else group_key}
            else:
                if not isinstance(group_key, tuple):
                    group_key = (group_key,)
                group_values = dict(zip(group_cols, group_key))
            rows.extend(metric_rows_for_group(group_df, group_values))
    else:
        rows.extend(metric_rows_for_group(merged))

    return pd.DataFrame(rows)


def main(args):
    predictions = pd.read_csv(args.pred_path)
    ground_truth = pd.read_csv(args.truth_path)

    metrics = evaluate_predictions(predictions, ground_truth, id_col=args.id_col)
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
