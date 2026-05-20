from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from constant import Constant
from utils import convert_scores


def test_convert_scores_uses_forward_scores():
    series = pd.Series({
        "pred": {
            "0": 5,
            "1": 4,
            "2": 3,
            "3": 2,
            "4": 1,
            }
        })

    scores = convert_scores(series)

    assert scores["pred_extraversion"] == 5
    assert scores["pred_agreeableness"] == 4
    assert scores["pred_conscientiousness"] == 3
    assert scores["pred_negative_emotionality"] == 4
    assert scores["pred_open_mindedness"] == 5


def test_convert_scores_applies_reverse_scoring(monkeypatch):
    items = deepcopy(Constant.BFI_ITEMS)
    items[0]["reverse"] = True
    monkeypatch.setattr(Constant, "BFI_ITEMS", items)
    series = pd.Series({"pred": {"0": 5}})

    scores = convert_scores(series)

    assert scores["pred_extraversion"] == 1


def test_convert_scores_ignores_missing_values(monkeypatch):
    items = [
        {"index": 0, "id": "X3", "text": "item 0", "trait": "extraversion", "reverse": False},
        {"index": 5, "id": "X8", "text": "item 5", "trait": "extraversion", "reverse": False},
        {"index": 1, "id": "X4", "text": "item 1", "trait": "agreeableness", "reverse": False},
        ]
    monkeypatch.setattr(Constant, "BFI_ITEMS", items)
    series = pd.Series({"pred": {"0": 4}})

    scores = convert_scores(series)

    assert scores["pred_extraversion"] == 4
    assert np.isnan(scores["pred_agreeableness"])


def test_convert_scores_output_columns():
    scores = convert_scores(pd.Series({"pred": {}}))

    assert set(scores) == {
        "pred_extraversion",
        "pred_agreeableness",
        "pred_conscientiousness",
        "pred_negative_emotionality",
        "pred_open_mindedness",
        }
