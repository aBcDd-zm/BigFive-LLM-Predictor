from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evaluate_ocean import evaluate_predictions


def _truth_df():
    return pd.DataFrame({
        "session_id": ["s1", "s2"],
        "open_mindedness": [1.0, 3.0],
        "conscientiousness": [2.0, 4.0],
        "extraversion": [3.0, 5.0],
        "agreeableness": [4.0, 2.0],
        "negative_emotionality": [5.0, 1.0],
        })


def _pred_df(**extra_cols):
    df = pd.DataFrame({
        "session_id": ["s1", "s2"],
        "pred_open_mindedness": [1.0, 3.0],
        "pred_conscientiousness": [2.0, 4.0],
        "pred_extraversion": [3.0, 5.0],
        "pred_agreeableness": [4.0, 2.0],
        "pred_negative_emotionality": [5.0, 1.0],
        })
    for column, values in extra_cols.items():
        df[column] = values
    return df


def test_evaluate_without_group_columns_returns_overall_metrics():
    metrics = evaluate_predictions(_pred_df(), _truth_df())

    assert len(metrics) == 5
    assert "backend" not in metrics.columns
    assert set(metrics["trait"]) == {
        "open_mindedness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "negative_emotionality",
        }
    assert np.allclose(metrics["pcc"].dropna(), 1.0)
    assert metrics["mae"].eq(0.0).all()


def test_evaluate_groups_by_backend_without_mixing():
    predictions = pd.concat([
        _pred_df(backend=["mock", "mock"]),
        _pred_df(backend=["api", "api"]).assign(pred_open_mindedness=[3.0, 1.0]),
        ], ignore_index=True)

    metrics = evaluate_predictions(predictions, _truth_df())
    open_metrics = metrics[metrics["trait"] == "open_mindedness"].set_index("backend")

    assert len(metrics) == 10
    assert set(metrics["backend"]) == {"mock", "api"}
    assert open_metrics.loc["mock", "mae"] == 0.0
    assert np.isclose(open_metrics.loc["mock", "pcc"], 1.0)
    assert open_metrics.loc["api", "mae"] == 2.0
    assert np.isclose(open_metrics.loc["api", "pcc"], -1.0)


def test_evaluate_raises_clear_error_for_missing_id_column():
    predictions = _pred_df().drop(columns=["session_id"])

    with pytest.raises(ValueError, match="Both files must contain id column: session_id"):
        evaluate_predictions(predictions, _truth_df())


def test_evaluate_raises_clear_error_for_missing_trait_column():
    predictions = _pred_df().drop(columns=["pred_open_mindedness"])

    with pytest.raises(ValueError, match="Missing columns for open_mindedness"):
        evaluate_predictions(predictions, _truth_df())
