import json
import os
import re
from glob import glob

import numpy as np

from constant import Constant


def parse_session_data(data_path: str):
    file_li = sorted(glob(os.path.join(data_path, "*.txt")))
    print(f"Total number of files: {len(file_li)}")
    session_li = []
    for file_path in file_li:
        utterance_li = []
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            match = re.match(r'^(咨询师|来访者)\s*[：:]\s*(.*)$', stripped)
            if not match:
                raise ValueError(
                    f"Invalid dialogue line in {file_path}:{line_no}. "
                    "Expected '咨询师：...' or '来访者：...'."
                    )
            utterance_li.append({
                "speaker": match.group(1),
                "utter": match.group(2).strip()
                })
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        name_parts = file_name.split('_')
        session_li.append({
            "session_id": file_name,
            "user": name_parts[0] if name_parts else file_name,
            "chat_round": name_parts[2] if len(name_parts) > 2 else "",
            "timestamp": name_parts[3] if len(name_parts) > 3 else "",
            "utterance_li": utterance_li
            })

    return session_li


def generate_bash_script(working_path):
    request_file = f"{working_path}/request.jsonl"
    response_file = f"{working_path}/response.jsonl"
    error_file = f"{working_path}/error.jsonl"

    bash_script = f"""#!/bin/bash

REQUEST_FILE="{request_file}"
RESPONSE_FILE="{response_file}"
ERROR_FILE="{error_file}"

SCRIPT_FILE="{Constant.SCRIPT_FILE}"
API_KEY="{Constant.API_KEY}"
REQUEST_URL="{Constant.REQUEST_URL}"

python "$SCRIPT_FILE" \\
    --request_url="$REQUEST_URL" \\
    --api_key="$API_KEY" \\
    --requests_filepath="$REQUEST_FILE" \\
    --save_filepath="$RESPONSE_FILE" \\
    --error_filepath="$ERROR_FILE" \\
    --max_attempts=5 \\
    --max_requests_per_minute=2048 \\
    --max_tokens_per_minute=99999999 \\
    --max_task=120 \\
    --logging_level=30 \\
    --resume"""

    with open(f"{working_path}/run.sh", "w") as f:
        f.write(bash_script)

    print("Bash script generated:")
    print(f"bash {working_path}/run.sh")


# Define choices for extract_choice function
CHOICES = {
    "非常不同意": 1,
    "不太同意": 2,
    "中立": 3,
    "比较同意": 4,
    "非常同意": 5
    }

TEXT_PATTERN = re.compile(r'非常不同意|不太同意|中立|比较同意|非常同意')
NUMBER_PATTERN = re.compile(r'([1-5])')
MARKDOWN_JSON_PATTERN = re.compile(r'```(?:json)?\s*(\{.*?\})\s*```', re.DOTALL | re.IGNORECASE)
EXPLICIT_CHOICE_PATTERN = re.compile(
    r'(?:最终)?(?:我)?(?:的)?(?:答案是|选项是|选择|选)\s*[:：]?\s*([1-5])'
    )


def extract_choice(sentence):
    sentence = str(sentence)
    text_match = TEXT_PATTERN.search(sentence)
    if text_match:
        return CHOICES[text_match.group(0)]

    number_match = NUMBER_PATTERN.search(sentence)
    if number_match and len(number_match.group(1)) == 1:
        return int(number_match.group(1))

    return -1


def _coerce_choice(value):
    if isinstance(value, str):
        value = value.strip()
    try:
        choice = int(value)
    except (TypeError, ValueError):
        return -1
    return choice if 1 <= choice <= 5 else -1


def _extract_json_object(content):
    stripped = str(content).strip()
    candidates = [stripped]

    markdown_match = MARKDOWN_JSON_PATTERN.search(stripped)
    if markdown_match:
        candidates.insert(0, markdown_match.group(1).strip())

    decoder = json.JSONDecoder()
    brace_positions = [idx for idx, char in enumerate(stripped) if char == "{"]
    for idx in brace_positions:
        candidates.append(stripped[idx:])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            try:
                parsed, _ = decoder.raw_decode(candidate)
            except json.JSONDecodeError:
                continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _extract_explicit_text_choice(content):
    text_match = TEXT_PATTERN.search(str(content))
    if text_match:
        return CHOICES[text_match.group(0)]

    number_match = EXPLICIT_CHOICE_PATTERN.search(str(content))
    if number_match:
        return _coerce_choice(number_match.group(1))

    return extract_choice(content)


def extract_choice_json(content):
    """
    Prefer parsing a JSON object with a choice field, then fall back to text extraction.

    Supported examples:
    {"choice": 5}
    {"choice": "5"}
    ```json
    {"choice": 4}
    ```
    """
    parsed = _extract_json_object(content)
    if parsed is not None:
        return _coerce_choice(parsed.get("choice"))

    return _extract_explicit_text_choice(content)


def _get_pred_value(series, item_index):
    pred_series = series.get('pred', {})
    if hasattr(pred_series, "get"):
        value = pred_series.get(str(item_index), np.nan)
        if not _is_missing(value):
            return value
        return pred_series.get(item_index, np.nan)
    return np.nan


def _is_missing(value):
    try:
        return bool(np.isnan(value))
    except TypeError:
        return value is None


def _to_numeric_score(value):
    try:
        score = float(value)
    except (TypeError, ValueError):
        return np.nan
    return np.nan if np.isnan(score) else score


def _score_bfi_item(series, item):
    score = _to_numeric_score(_get_pred_value(series, item["index"]))
    if np.isnan(score):
        return np.nan
    return 6 - score if item.get("reverse", False) else score


def calculate_trait_scores(series, trait_items):
    values = [_score_bfi_item(series, item) for item in trait_items]
    valid_values = [value for value in values if not np.isnan(value)]
    if not valid_values:
        return np.nan
    return float(np.mean(valid_values))


def convert_scores(series):
    trait_order = [
        "extraversion",
        "agreeableness",
        "conscientiousness",
        "negative_emotionality",
        "open_mindedness",
        ]
    scores = {}
    for trait in trait_order:
        trait_items = [item for item in Constant.BFI_ITEMS if item["trait"] == trait]
        pred_score = calculate_trait_scores(series, trait_items)
        scores[f"pred_{trait}"] = pred_score

    return scores
