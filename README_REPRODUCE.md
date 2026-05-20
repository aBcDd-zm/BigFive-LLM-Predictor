# Big Five / OCEAN 推理流程复现说明

本文档说明如何复现论文公开代码的推理链路：从中文心理咨询对话生成 BFI 问卷请求，得到模型回答，再汇总 OCEAN 五维人格分数并计算 PCC / MAE。当前只覆盖推理与评估，不包含 SFT / DPO 微调。

完整流水线：

```text
中文咨询对话 txt
  -> generate_bfi_requests.py
  -> outputs/bfi_requests/request.jsonl
  -> run_local_inference.py 或 API
  -> outputs/response.jsonl
  -> process_results.py
  -> outputs/ocean_scores.csv
  -> evaluate_ocean.py
  -> outputs/evaluation_metrics.csv
```

所有命令默认在仓库根目录运行，所有路径均使用相对路径。

## 1. 环境准备

```bash
git clone https://github.com/kuri-leo/BigFive-LLM-Predictor.git
cd BigFive-LLM-Predictor

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果本机 pip 遇到证书校验问题，可以临时使用：

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

本复现环境使用 Python 3.12。原仓库的 `torch==2.1.1` 没有 Python 3.12 wheel，因此当前 `requirements.txt` 使用 `torch==2.2.2`；为了支持 Gemma 2 checkpoint，也升级了 `transformers` 并补充 `accelerate`。

## 2. 输入数据格式

示例对话位于：

```text
data/dialogues/
```

每个 session 一个 `.txt` 文件，文件名格式：

```text
{Client_ID}_chat_{Chatround_ID}_{Timestamp}.txt
```

每行一轮话语，支持中文或英文冒号：

```text
咨询师：欢迎你来聊聊，今天最想讨论的是什么？
来访者：最近工作节奏有点快，我想理清优先级。
咨询师: 你通常会怎么安排这些任务？
来访者: 我会先列清单。
```

示例真值文件：

```text
data/ground_truth.csv
```

字段：

```text
session_id,user_id,extraversion,agreeableness,conscientiousness,negative_emotionality,open_mindedness
```

当前样例均为虚构匿名内容，不包含真实隐私信息。

## 3. 一键 Mock 复现

最推荐先用 mock 跑通整条链路。mock 不下载模型、不调用 API，只验证输入输出、解析、计分和评估脚本是否能串起来。

macOS / Linux：

```bash
scripts/run_reproduce_mock.sh
```

Windows PowerShell：

```powershell
.\scripts\run_reproduce_mock.ps1
```

脚本会顺序执行：

```text
generate_bfi_requests.py
run_local_inference.py --backend mock
process_results.py
evaluate_ocean.py
```

生成或刷新：

```text
outputs/bfi_requests/request.jsonl
outputs/response.jsonl
outputs/ocean_scores.csv
outputs/evaluation_metrics.csv
```

重要：mock 结果只能用于流程测试，不能当作真实人格预测结果或论文复现实验结论。

## 4. 手动生成 Request JSONL

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

`request.jsonl` 每行是一道 BFI 题的 chat completion 请求。3 个示例对话 × 60 道 BFI 题会生成 180 条请求。

关键字段示例：

```json
{
  "uuid": "p001_chat_6_202605200001_0_0",
  "model": "kurileo/Gemma-2-2b-it-BFI-Anonymous",
  "messages": [{"role": "system", "content": "..."}],
  "max_tokens": 256
}
```

`uuid` 末尾两个字段分别是 `question_id` 和 `try_id`。

当前 prompt 会要求模型严格输出 JSON：

```json
{
  "choice": 1,
  "label": "非常不同意",
  "reason": "一句话说明理由"
}
```

## 5. 推理方式

推理脚本：

```text
src/run_local_inference.py
```

### Mock 推理

```bash
python src/run_local_inference.py \
  --backend mock \
  --requests_path outputs/bfi_requests/request.jsonl \
  --output_path outputs/response.jsonl
```

mock 输出兼容 chat completion JSONL：

```json
{
  "uuid": "p001_chat_6_202605200001_0_0",
  "model": "kurileo/Gemma-2-2b-it-BFI-Anonymous",
  "backend": "mock",
  "choices": [{"message": {"role": "assistant", "content": "我选择1。..."}}]
}
```

### API 推理

API 后端要求 OpenAI-compatible `/v1/chat/completions` 接口，例如 vLLM、sglang 或远程服务：

```bash
export BFI_API_URL="http://127.0.0.1:8000/v1/chat/completions"
export BFI_API_KEY="YOUR_API_KEY"
export BFI_API_MODEL="kurileo/Gemma-2-2b-it-BFI-Anonymous"

python src/run_local_inference.py \
  --backend api \
  --requests_path outputs/bfi_requests/request.jsonl \
  --output_path outputs/response.jsonl
```

也可以直接传：

```bash
--api_url
--api_key
--api_model
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

如果需要 Hugging Face token：

```bash
huggingface-cli login
```

没有 GPU 时默认不要在 CPU 上跑 2B 模型。确实要 CPU 测试时可加 `--allow_cpu`，但会很慢。

## 6. 生成 OCEAN 分数

```bash
python src/process_results.py \
  --response_paths outputs/response.jsonl \
  --output_path outputs/ocean_scores.csv
```

输出字段：

```text
model_name,backend,user_id,session_id,chat_round,try_id,
pred_extraversion,pred_agreeableness,pred_conscientiousness,
pred_negative_emotionality,pred_open_mindedness,
pred_O,pred_C,pred_E,pred_A,pred_N
```

`process_results.py` 会优先解析模型输出中的 JSON `choice` 字段；如果模型没有按 JSON 输出，会 fallback 到中文标签和显式选择文本，例如：

```text
我选择比较同意，因为这符合我的情况。
我有3个理由，所以最终选择5。
```

无法抽取 1-5 选项的回答会记为缺失值，不参与该维度均值。

## 7. BFI 元数据与反向计分

`src/constant.py` 现在保留原始 `Constant.BFI_ITEM_LI`，并新增结构化 `Constant.BFI_ITEMS`。每题包含：

```python
{
    "index": 0,
    "id": "X3",
    "text": "我是一个性格外向、喜欢交际的人",
    "trait": "extraversion",
    "reverse": False,
}
```

`src/utils.py` 的 `convert_scores()` 现在基于 `BFI_ITEMS` 计算分数，而不是靠硬编码题号范围。若某题未来确认 `reverse=True`，计分时会执行：

```python
score = 6 - score
```

当前 60 道题的题干、维度归属和反向计分已按官方中文 BFI-2 self-report form and scoring key 复核。共 30 道题 `reverse=True`。复核记录见：

```text
docs/BFI_ITEM_REVIEW.md
```

## 8. 评估 PCC 和 MAE

```bash
python src/evaluate_ocean.py \
  --pred_path outputs/ocean_scores.csv \
  --truth_path data/ground_truth.csv \
  --output_path outputs/evaluation_metrics.csv
```

输出字段在有分组列时为：

```text
model_name,backend,try_id,trait,pcc,mae,n,prediction_column,ground_truth_column
```

如果预测文件没有 `model_name`、`backend`、`try_id`，则输出整体评估：

```text
trait,pcc,mae,n,prediction_column,ground_truth_column
```

指标含义：

- `trait`：五个人格维度之一。
- `pcc`：预测分与真值之间的 Pearson correlation。
- `mae`：预测分与真值之间的 Mean Absolute Error。
- `n`：该维度参与评估的有效样本数。
- `prediction_column` / `ground_truth_column`：实际使用的预测列和真值列。

mock 输出是固定占位分数，PCC 可能为空；真实模型或 API 输出才适合解读相关系数。

## 9. 已验证命令

```bash
scripts/run_reproduce_mock.sh
source .venv/bin/activate && python -m pytest
source .venv/bin/activate && python -m py_compile src/generate_bfi_requests.py src/run_local_inference.py src/process_results.py src/evaluate_ocean.py
```

当前测试覆盖：

- JSON / 文本答案抽取。
- BFI 元数据计分和反向计分机制。
- evaluate 分组评估与缺列报错。

## 10. 常见问题

### `torch==2.1.1` 无法安装

Python 3.12 环境下没有该版本 wheel。使用当前 `requirements.txt` 中兼容 Python 3.12 的 torch 版本，或换 Python 3.10/3.11 后再尝试原始依赖。

### 没有 GPU

使用 `--backend api` 连接本地或远程 OpenAI-compatible 服务。`--allow_cpu` 只建议做极小规模测试。

### 下载 Hugging Face 模型失败

检查网络、磁盘空间和 Hugging Face 登录状态。可设置 `HF_TOKEN` 或运行：

```bash
huggingface-cli login
```

### Gemma chat template 不接受 system role

原始请求会生成 `system` prompt。`run_local_inference.py` 在本地 Hugging Face 推理时会自动把 `system` 内容合并到第一条 `user` 消息；API 后端仍发送原始 messages。

### `process_results.py` 生成 NaN

通常是模型回答没有包含可抽取的 JSON `choice`、中文选项文本或显式“选择5”格式。优先让模型输出：

```json
{"choice": 5, "label": "非常同意", "reason": "一句话说明理由"}
```

### 评估 PCC 为空

样本数少于 2、预测值全相同、真值全相同都会导致 PCC 无定义。示例 mock 输出固定，因此 PCC 为空是正常现象。

### mock 结果能不能当实验结果

不能。mock 只验证代码链路，不能证明模型预测人格有效，也不能用于论文结论复现。

### 分组评估后输出列变多

这是预期行为。预测文件中存在 `model_name`、`backend`、`try_id` 时，评估脚本会按这些列分组，避免把不同模型或不同推理后端的结果混在一起。
