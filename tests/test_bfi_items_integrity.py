from copy import deepcopy
from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from constant import Constant  # noqa: E402
from constant import BFI_REVERSE_ITEM_NUMBERS  # noqa: E402
from scripts.check_bfi_items import validate_bfi_items  # noqa: E402


def test_bfi_items_integrity():
    stats = validate_bfi_items(Constant.BFI_ITEMS)

    assert stats["total_items"] == 60
    assert sum(stats["trait_counts"].values()) == 60
    assert sum(stats["reverse_counts"].values()) == 60
    assert set(stats["trait_counts"].values()) == {12}
    assert stats["reverse_counts"][True] == 30
    assert stats["reverse_counts"][False] == 30


def test_bfi_items_use_official_bfi2_reverse_key():
    reverse_item_numbers = {
        item["index"] + 1
        for item in Constant.BFI_ITEMS
        if item["reverse"]
        }

    assert reverse_item_numbers == BFI_REVERSE_ITEM_NUMBERS


def test_bfi_items_validation_rejects_duplicate_ids():
    items = deepcopy(Constant.BFI_ITEMS)
    items[1]["id"] = items[0]["id"]

    with pytest.raises(ValueError, match="Duplicate BFI item id"):
        validate_bfi_items(items)


def test_bfi_items_validation_rejects_non_bool_reverse():
    items = deepcopy(Constant.BFI_ITEMS)
    items[0]["reverse"] = "False"

    with pytest.raises(ValueError, match="non-bool reverse"):
        validate_bfi_items(items)
