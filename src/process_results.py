import argparse
import json
import os

import pandas as pd
from tqdm import tqdm

from utils import convert_scores, extract_choice


OCEAN_ALIASES = {
    "pred_open_mindedness": "pred_O",
    "pred_conscientiousness": "pred_C",
    "pred_extraversion": "pred_E",
    "pred_agreeableness": "pred_A",
    "pred_negative_emotionality": "pred_N",
    }


def calculate_big_five_scores(series):
    return pd.Series(convert_scores(series))


def parse_uuid(uuid):
    session_id, question_id, try_id = uuid.rsplit("_", 2)
    parts = session_id.split("_")
    user_id = parts[0] if parts else session_id
    chat_round = parts[2] if len(parts) > 2 else ""
    return session_id, user_id, chat_round, question_id, try_id


def read_response_content(raw_data):
    request_data = {}
    response_data = raw_data

    if isinstance(raw_data, list):
        if raw_data and isinstance(raw_data[0], dict):
            request_data = raw_data[0]
        if len(raw_data) > 1 and isinstance(raw_data[1], dict):
            response_data = raw_data[1]
    elif isinstance(raw_data, dict):
        request_data = raw_data

    uuid = (
        response_data.get("uuid")
        or request_data.get("uuid")
        or response_data.get("custom_id")
        or request_data.get("custom_id")
        )
    model_name = (
        response_data.get("model")
        or request_data.get("model")
        or "unknown_model"
        )
    backend = response_data.get("backend", "")

    content = response_data.get("content")
    choices = response_data.get("choices", [])
    if content is None and choices:
        message = choices[0].get("message", {})
        content = message.get("content", choices[0].get("text", ""))
    if content is None:
        content = ""

    return uuid, model_name, backend, str(content).replace("\n", "").replace("\t", "").strip()


def load_responses(file_paths):
    results = []

    for response_file in tqdm(file_paths, desc="responses"):
        with open(response_file, "r", encoding="utf-8") as file:
            response_data = file.readlines()

        for line_no, line in enumerate(response_data, start=1):
            if not line.strip():
                continue
            raw_data = json.loads(line)
            uuid, model_name, backend, content = read_response_content(raw_data)
            if not uuid:
                raise ValueError(f"Missing uuid in {response_file}:{line_no}")

            session_id, user_id, chat_round, question_id, try_id = parse_uuid(uuid)
            pred = extract_choice(content)

            results.append({
                "model_name": model_name,
                "backend": backend,
                "session_id": session_id,
                "user_id": user_id,
                "chat_round": chat_round,
                "question_id": question_id,
                "try_id": try_id,
                "pred": pred,
                "content": content
                })

    return pd.DataFrame(results)


def process_data(df):
    df = df.copy()
    df["pred"] = pd.to_numeric(df["pred"], errors="coerce").replace(-1, pd.NA)

    pivot_df = df.pivot_table(
        index=["model_name", "backend", "user_id", "session_id", "chat_round", "try_id"],
        columns=["question_id"],
        values=["pred"],
        aggfunc="mean",
        )

    results_df = pivot_df.apply(calculate_big_five_scores, axis=1).reset_index()
    for source, alias in OCEAN_ALIASES.items():
        if source in results_df:
            results_df[alias] = results_df[source]
    return results_df


def main(args):
    response_df = load_responses(args.response_paths)
    if response_df.empty:
        raise ValueError("No model responses were loaded.")

    results_df = process_data(response_df)
    os.makedirs(os.path.dirname(args.output_path) or ".", exist_ok=True)
    results_df.to_csv(args.output_path, index=False)
    print(results_df.head())
    print(f"Wrote OCEAN scores to {args.output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--response_paths",
        nargs="+",
        default=["outputs/response.jsonl"],
        help="One or more JSONL files produced by run_local_inference.py or an OpenAI-compatible batch processor.",
        )
    parser.add_argument("--output_path", default="outputs/ocean_scores.csv")
    main(parser.parse_args())
