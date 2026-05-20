# 推理流程复现说明

本文档只复现论文公开代码的推理链路，不包含 DPO/SFT 微调。所有命令默认在仓库根目录运行，所有路径均使用相对路径。

## 1. 克隆仓库

```bash
git clone https://github.com/kuri-leo/BigFive-LLM-Predictor.git
cd BigFive-LLM-Predictor
```

## 2. 创建环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果本机 pip 遇到证书校验问题，可以临时使用：

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

本复现环境使用 Python 3.12。原仓库的 `torch==2.1.1` 没有 Python 3.12 wheel，因此已改为 `torch==2.2.2`；为了支持 Gemma 2 checkpoint，也将 `transformers` 升级到 `4.42.4` 并补充 `accelerate`。

## 3. 示例输入数据

匿名样例对话位于：

```text
data/dialogues/
```

文件名格式：

```text
{Client_ID}_chat_{Chatround_ID}_{Timestamp}.txt
```

每行格式支持中文或英文冒号：

```text
咨询师：欢迎你来聊聊，今天最想讨论的是什么？
来访者：最近工作节奏有点快，我想理清优先级。
```

示例真值文件：

```text
data/ground_truth.csv
```

字段：

```text
session_id,user_id,extraversion,agreeableness,conscientiousness,negative_emotionality,open_mindedness
```

这些样例均为虚构内容，不包含真实隐私信息。

## 4. 生成 BFI 请求

```bash
python src/generate_bfi_requests.py \
  --model_name kurileo/Gemma-2-2b-it-BFI-Anonymous \
  --source_path data/dialogues \
  --output_path outputs/bfi_requests
```

输出：

```text
outputs/bfi_requests/request.jsonl
outputs/bfi_requests/run.sh
```

`request.jsonl` 每行是一道 BFI 题的 chat completion 请求，关键字段包括：

```json
{
  "uuid": "p001_chat_6_202605200001_0_0",
  "model": "kurileo/Gemma-2-2b-it-BFI-Anonymous",
  "messages": [{"role": "system", "content": "..."}],
  "max_tokens": 256
}
```

uuid 末尾两个字段分别是 `question_id` 和 `try_id`。3 个对话 × 60 道 BFI 题会生成 180 条请求。

## 5. 运行推理

新增脚本：

```text
src/run_local_inference.py
```

### 本地 Hugging Face 推理

优先使用公开 checkpoint：

```bash
python src/run_local_inference.py \
  --backend local \
  --model_name kurileo/Gemma-2-2b-it-BFI-Anonymous \
  --requests_path outputs/bfi_requests/request.jsonl \
  --output_path outputs/response.jsonl
```

`--backend auto` 会在检测到 CUDA/MPS GPU 时走本地模型，否则走 API 后端。

如果需要 Hugging Face token，可先登录：

```bash
huggingface-cli login
```

### 无 GPU 时使用 API

API 后端要求 OpenAI-compatible `/v1/chat/completions` 接口：

```bash
export BFI_API_URL="http://127.0.0.1:8000/v1/chat/completions"
export BFI_API_KEY="YOUR_API_KEY"
export BFI_API_MODEL="kurileo/Gemma-2-2b-it-BFI-Anonymous"

python src/run_local_inference.py \
  --backend api \
  --requests_path outputs/bfi_requests/request.jsonl \
  --output_path outputs/response.jsonl
```

也可以直接传 `--api_url`、`--api_key`、`--api_model`。

### 离线冒烟测试

不下载模型、不调用 API，只验证文件链路：

```bash
python src/run_local_inference.py \
  --backend mock \
  --requests_path outputs/bfi_requests/request.jsonl \
  --output_path outputs/response.jsonl
```

输出 JSONL 每行兼容 chat completion 格式：

```json
{
  "uuid": "p001_chat_6_202605200001_0_0",
  "model": "kurileo/Gemma-2-2b-it-BFI-Anonymous",
  "backend": "local",
  "choices": [{"message": {"role": "assistant", "content": "我选择4。..."}}]
}
```

## 6. 生成 OCEAN 分数

`src/process_results.py` 已改为命令行脚本，可读取本地脚本输出或 OpenAI-compatible batch 输出：

```bash
python src/process_results.py \
  --response_paths outputs/response.jsonl \
  --output_path outputs/ocean_scores.csv
```

输出字段：

```text
model_name,backend,user_id,session_id,chat_round,try_id,
pred_extraversion,pred_agreeableness,pred_conscientiousness,
pred_negative_emotionality,pred_open_mindedness,pred_O,pred_C,pred_E,pred_A,pred_N
```

计分逻辑沿用原仓库：60 个 BFI 条目按 E/A/C/N/O 每 5 题分组求均值；无法抽取 1-5 选项的回答记为缺失值。

## 7. 评估 PCC 和 MAE

新增脚本：

```text
src/evaluate_ocean.py
```

运行：

```bash
python src/evaluate_ocean.py \
  --pred_path outputs/ocean_scores.csv \
  --truth_path data/ground_truth.csv \
  --output_path outputs/evaluation_metrics.csv
```

输出字段：

```text
trait,pcc,mae,n,prediction_column,ground_truth_column
```

mock 输出是固定占位分数，PCC 可能为空；真实模型或 API 输出才适合解读相关系数。

## 8. 本次已验证命令

```bash
python src/generate_bfi_requests.py --model_name kurileo/Gemma-2-2b-it-BFI-Anonymous --source_path data/dialogues --output_path outputs/bfi_requests
python src/run_local_inference.py --backend mock --requests_path outputs/bfi_requests/request.jsonl --output_path outputs/response.jsonl
python src/process_results.py --response_paths outputs/response.jsonl --output_path outputs/ocean_scores.csv
python src/evaluate_ocean.py --pred_path outputs/ocean_scores.csv --truth_path data/ground_truth.csv --output_path outputs/evaluation_metrics.csv
```

生成文件：

```text
outputs/bfi_requests/request.jsonl
outputs/bfi_requests/run.sh
outputs/response.jsonl
outputs/ocean_scores.csv
outputs/evaluation_metrics.csv
```

## 常见问题

### `torch==2.1.1` 无法安装

Python 3.12 环境下没有该版本 wheel。使用本复现版 `requirements.txt` 中的 `torch==2.2.2`，或换 Python 3.10/3.11 后再尝试原始依赖。

### 没有 GPU

默认不要在 CPU 上跑 2B 模型。使用 `--backend api` 连接本地 vLLM/sglang/OpenAI-compatible 服务。确实要 CPU 测试时可加 `--allow_cpu`，但会很慢。

### 下载 Hugging Face 模型失败

先确认网络、磁盘空间和 Hugging Face 登录状态。可设置 `HF_TOKEN` 或运行 `huggingface-cli login`。

### Gemma chat template 不接受 system role

原始请求会生成 `system` prompt。`run_local_inference.py` 在本地 Hugging Face 推理时会自动把 `system` 内容合并到第一条 `user` 消息；API 后端仍发送原始 messages。

### `process_results.py` 生成 NaN

通常是模型回答没有包含可抽取的 1-5 数字或中文选项文本。建议提示模型以“我选择4。”开头，或检查 `outputs/response.jsonl` 中的 `choices[0].message.content`。

### 评估 PCC 为空

样本数少于 2、预测值全相同、真值全相同都会导致 PCC 无定义。示例 mock 输出固定，因此 PCC 为空是正常现象。
