#!/bin/bash

REQUEST_FILE="outputs/bfi_requests/request.jsonl"
RESPONSE_FILE="outputs/bfi_requests/response.jsonl"
ERROR_FILE="outputs/bfi_requests/error.jsonl"

SCRIPT_FILE=""
API_KEY=""
REQUEST_URL=""

python "$SCRIPT_FILE" \
    --request_url="$REQUEST_URL" \
    --api_key="$API_KEY" \
    --requests_filepath="$REQUEST_FILE" \
    --save_filepath="$RESPONSE_FILE" \
    --error_filepath="$ERROR_FILE" \
    --max_attempts=5 \
    --max_requests_per_minute=2048 \
    --max_tokens_per_minute=99999999 \
    --max_task=120 \
    --logging_level=30 \
    --resume