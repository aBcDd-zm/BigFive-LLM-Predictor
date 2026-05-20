import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    tqdm = lambda x, **_: x


DEFAULT_MODEL = "kurileo/Gemma-2-2b-it-BFI-Anonymous"


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield json.loads(line)


def append_jsonl(path, item):
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(item, ensure_ascii=False) + "\n")


def existing_uuids(path):
    if not os.path.exists(path):
        return set()
    uuids = set()
    for item in load_jsonl(path):
        if isinstance(item, dict) and item.get("uuid"):
            uuids.add(item["uuid"])
    return uuids


def detect_device():
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def build_local_runner(model_name, allow_cpu=False):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = detect_device()
    if device == "cpu" and not allow_cpu:
        raise RuntimeError(
            "No CUDA/MPS GPU was detected. Use --backend api for an OpenAI-compatible "
            "endpoint, or pass --allow_cpu if you really want slow CPU inference."
        )

    dtype = torch.float16 if device in {"cuda", "mps"} else torch.float32
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    if device == "cuda":
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map="auto",
            )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            )
        model.to(device)

    model.eval()

    def fold_system_messages(messages):
        system_parts = []
        folded = []
        for message in messages:
            if message["role"] == "system":
                system_parts.append(message["content"])
            else:
                folded.append(dict(message))
        if not system_parts:
            return messages

        system_prompt = "\n".join(system_parts)
        if folded and folded[0]["role"] == "user":
            folded[0]["content"] = f"{system_prompt}\n\n{folded[0]['content']}"
        else:
            folded.insert(0, {"role": "user", "content": system_prompt})
        return folded

    def render_prompt(messages):
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                )
        except Exception:
            folded_messages = fold_system_messages(messages)
            if folded_messages == messages:
                raise
            return tokenizer.apply_chat_template(
                folded_messages,
                tokenize=False,
                add_generation_prompt=True,
                )

    def run(job, max_new_tokens, temperature):
        prompt = render_prompt(job["messages"])
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        do_sample = temperature > 0
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=do_sample,
                temperature=temperature if do_sample else None,
                pad_token_id=tokenizer.eos_token_id,
                )
        generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
        return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    return run


def call_api(job, args):
    api_url = args.api_url or os.environ.get("BFI_API_URL")
    api_key = args.api_key or os.environ.get("BFI_API_KEY")
    api_model = args.api_model or os.environ.get("BFI_API_MODEL") or job.get("model")
    if not api_url:
        raise RuntimeError("API backend requires --api_url or BFI_API_URL.")

    payload = {
        "model": api_model,
        "messages": job["messages"],
        "max_tokens": args.max_new_tokens or job.get("max_tokens", 256),
        "temperature": args.temperature,
        }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API request failed with HTTP {exc.code}: {error_body}") from exc

    response_data["uuid"] = job["uuid"]
    response_data.setdefault("model", api_model)
    response_data["backend"] = "api"
    return response_data


def mock_response(job):
    _, question_id, _ = job["uuid"].rsplit("_", 2)
    choice = int(question_id) % 5 + 1
    content = f"我选择{choice}。这是用于复现流程冒烟测试的占位输出。"
    return {
        "uuid": job["uuid"],
        "model": job.get("model", "mock"),
        "backend": "mock",
        "choices": [{"message": {"role": "assistant", "content": content}}],
        }


def response_from_content(job, model_name, backend, content):
    return {
        "uuid": job["uuid"],
        "model": model_name,
        "backend": backend,
        "choices": [{"message": {"role": "assistant", "content": content}}],
        }


def main(args):
    requests = list(load_jsonl(args.requests_path))
    if args.limit:
        requests = requests[:args.limit]

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    done = existing_uuids(args.output_path) if args.resume else set()
    pending = [job for job in requests if job.get("uuid") not in done]

    backend = args.backend
    if backend == "auto":
        backend = "local" if detect_device() != "cpu" else "api"

    local_runner = None
    if backend == "local":
        local_runner = build_local_runner(args.model_name, allow_cpu=args.allow_cpu)

    for job in tqdm(pending, desc=f"inference:{backend}"):
        if backend == "mock":
            result = mock_response(job)
        elif backend == "api":
            result = call_api(job, args)
        elif backend == "local":
            content = local_runner(
                job,
                max_new_tokens=args.max_new_tokens or job.get("max_tokens", 256),
                temperature=args.temperature,
                )
            result = response_from_content(job, args.model_name, backend, content)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

        append_jsonl(args.output_path, result)
        if args.sleep > 0:
            time.sleep(args.sleep)

    print(f"Wrote {len(pending)} responses to {args.output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests_path", default="outputs/bfi_requests/request.jsonl")
    parser.add_argument("--output_path", default="outputs/response.jsonl")
    parser.add_argument("--model_name", default=DEFAULT_MODEL)
    parser.add_argument("--backend", choices=["auto", "local", "api", "mock"], default="auto")
    parser.add_argument("--api_url", default="")
    parser.add_argument("--api_key", default="")
    parser.add_argument("--api_model", default="")
    parser.add_argument("--max_new_tokens", type=int, default=128)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--allow_cpu", action="store_true")
    main(parser.parse_args())
