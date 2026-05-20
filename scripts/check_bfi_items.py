#!/usr/bin/env python3
from collections import Counter
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from constant import BFI_TRAIT_ORDER, Constant  # noqa: E402


REQUIRED_FIELDS = ("index", "id", "text", "trait", "reverse")
VALID_TRAITS = set(BFI_TRAIT_ORDER)


def _describe_item(item, position):
    item_id = item.get("id") if isinstance(item, dict) else None
    return f"item at position {position}" + (f" (id={item_id})" if item_id else "")


def validate_bfi_items(items):
    if items is None:
        raise ValueError("Constant.BFI_ITEMS does not exist or is None.")

    if not isinstance(items, list):
        raise ValueError(f"Constant.BFI_ITEMS must be a list, got {type(items).__name__}.")

    if len(items) != 60:
        raise ValueError(f"Constant.BFI_ITEMS must contain exactly 60 items, got {len(items)}.")

    seen_ids = set()
    trait_counts = Counter()
    reverse_counts = Counter()

    for position, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"{_describe_item(item, position)} must be a dict.")

        missing_fields = [field for field in REQUIRED_FIELDS if field not in item]
        if missing_fields:
            raise ValueError(
                f"{_describe_item(item, position)} is missing required fields: "
                f"{', '.join(missing_fields)}."
                )

        if item["index"] != position:
            raise ValueError(
                f"{_describe_item(item, position)} has index={item['index']}, "
                f"expected {position}."
                )

        item_id = item["id"]
        if item_id in seen_ids:
            raise ValueError(f"Duplicate BFI item id found: {item_id}.")
        seen_ids.add(item_id)

        if not str(item["text"]).strip():
            raise ValueError(f"{_describe_item(item, position)} has empty text.")

        trait = item["trait"]
        if trait not in VALID_TRAITS:
            raise ValueError(
                f"{_describe_item(item, position)} has invalid trait={trait!r}. "
                f"Valid traits: {', '.join(sorted(VALID_TRAITS))}."
                )
        trait_counts[trait] += 1

        reverse = item["reverse"]
        if not isinstance(reverse, bool):
            raise ValueError(
                f"{_describe_item(item, position)} has non-bool reverse="
                f"{reverse!r} ({type(reverse).__name__})."
                )
        reverse_counts[reverse] += 1

    return {
        "total_items": len(items),
        "trait_counts": trait_counts,
        "reverse_counts": reverse_counts,
        }


def print_stats(stats):
    print("BFI_ITEMS integrity check passed.")
    print()
    print(f"Total items: {stats['total_items']}")
    print()
    print("Trait distribution:")
    for trait in BFI_TRAIT_ORDER:
        print(f"- {trait}: {stats['trait_counts'].get(trait, 0)}")
    print()
    print("Reverse items:")
    print(f"- reverse=True: {stats['reverse_counts'].get(True, 0)}")
    print(f"- reverse=False: {stats['reverse_counts'].get(False, 0)}")
    print()
    print("Note:")
    print("Current reverse values may still be placeholders.")
    print("Please confirm final BFI keying manually before running real model evaluation.")


def main():
    stats = validate_bfi_items(getattr(Constant, "BFI_ITEMS", None))
    print_stats(stats)


if __name__ == "__main__":
    main()
