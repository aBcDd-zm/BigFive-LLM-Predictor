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


def extract_choice(sentence):
    sentence = str(sentence)
    text_match = TEXT_PATTERN.search(sentence)
    if text_match:
        return CHOICES[text_match.group(0)]

    number_match = NUMBER_PATTERN.search(sentence)
    if number_match and len(number_match.group(1)) == 1:
        return int(number_match.group(1))

    return -1


def calculate_trait_scores(series, trait_indices):
    values = []
    for idx in trait_indices:
        value = np.nan
        pred_series = series.get('pred', {})
        if str(idx) in pred_series:
            value = pred_series[str(idx)]
        elif idx in pred_series:
            value = pred_series[idx]
        values.append(value)
    return np.nanmean(values)


def convert_scores(series):
    traits = {
        "extraversion": range(0, 56, 5),
        "agreeableness": range(1, 57, 5),
        "conscientiousness": range(2, 58, 5),
        "negative_emotionality": range(3, 59, 5),
        "open_mindedness": range(4, 60, 5)
        }

    scores = {}
    for trait, indices in traits.items():
        pred_score = calculate_trait_scores(series, indices)
        scores[f"pred_{trait}"] = pred_score

    return scores
