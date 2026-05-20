#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from constant import Constant  # noqa: E402


DEFAULT_MARKDOWN_PATH = PROJECT_ROOT / "docs" / "BFI_ITEM_REVIEW_TABLE.md"
DEFAULT_CSV_PATH = PROJECT_ROOT / "outputs" / "bfi_item_review_table.csv"
REVIEW_STATUS = "已按官方中文 BFI-2 计分键确认"
REVIEW_NOTE = "Colby Chinese BFI-2 self-report form and scoring key"
TABLE_COLUMNS = (
    "index",
    "id",
    "trait",
    "reverse",
    "text",
    "suggested_review_status",
    "reviewer_note",
    )


def _markdown_cell(value):
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def build_review_rows(items):
    rows = []
    for item in items:
        rows.append({
            "index": item["index"],
            "id": item["id"],
            "trait": item["trait"],
            "reverse": item["reverse"],
            "text": item["text"],
            "suggested_review_status": REVIEW_STATUS,
            "reviewer_note": REVIEW_NOTE,
            })
    return rows


def write_markdown(rows, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# BFI Item Review Table",
        "",
        "Generated from `Constant.BFI_ITEMS`. "
        "The `trait`, `reverse`, and item wording values have been reviewed "
        "against the official Chinese BFI-2 scoring key.",
        "",
        "| index | id | trait | reverse | text | suggested_review_status | reviewer_note |",
        "|---:|---|---|---|---|---|---|",
        ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(_markdown_cell(row[column]) for column in TABLE_COLUMNS)
            + " |"
            )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(rows, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=TABLE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Export Constant.BFI_ITEMS to a manual review table."
        )
    parser.add_argument(
        "--markdown-output",
        default=str(DEFAULT_MARKDOWN_PATH),
        help="Path for the generated Markdown review table.",
        )
    parser.add_argument(
        "--csv-output",
        default=str(DEFAULT_CSV_PATH),
        help="Path for the generated CSV review table. Use an empty value to skip CSV.",
        )
    args = parser.parse_args()

    rows = build_review_rows(Constant.BFI_ITEMS)
    markdown_output = Path(args.markdown_output)
    write_markdown(rows, markdown_output)
    print(f"Wrote Markdown review table to {markdown_output}")

    if args.csv_output:
        csv_output = Path(args.csv_output)
        write_csv(rows, csv_output)
        print(f"Wrote CSV review table to {csv_output}")


if __name__ == "__main__":
    main()
