# BigFive-LLM-Predictor 推理复现交接文档

这份文档用于交接给后续 GPT/协作者，帮助其理解当前仓库已经完成了哪些复现工作、代码如何串起来、哪些地方是对原仓库的必要修改，以及后续如果要继续真实模型推理应从哪里接。

当前工作目录：

```bash
/Users/chenhongmiao/Downloads/心里比赛与llm/BigFive-LLM-Predictor
```

目标是复现论文 **Predicting the Big Five Personality Traits in Chinese Counselling Dialogues Using Large Language Models** 的公开代码推理流程，只做推理链路，不做 DPO/SFT 微调。

## 一、当前完成状态

已完成：

1. 克隆公开仓库 `https://github.com/kuri-leo/BigFive-LLM-Predictor`。
2. 创建 Python 虚拟环境 `.venv/`。
3. 安装依赖，并根据本机 Python 3.12 做了兼容调整。
4. 在 `data/dialogues/` 下创建 3 个匿名中文咨询对话样例。
5. 创建 `data/ground_truth.csv` 作为玩具真值文件。
6. 修复/增强 `src/utils.py`，使其能读取“咨询师：”“来访者：”全角冒号格式。
7. 运行 `src/generate_bfi_requests.py`，生成 180 条 BFI 请求到 `outputs/bfi_requests/request.jsonl`。
8. 新增 `src/run_local_inference.py`，支持 Hugging Face 本地推理、OpenAI-compatible API 推理、自动选择后端、mock 冒烟测试。
9. 改造 `src/process_results.py`，让它能从 JSONL 模型输出生成会话级 OCEAN 分数 CSV。
10. 新增 `src/evaluate_ocean.py`，读取预测分和真值，计算五个维度的 PCC 和 MAE。
11. 新增 `README_REPRODUCE.md`，记录完整命令、输入输出格式和常见问题。
12. 已用 `mock` 后端完整跑通流程。

已生成输出：

```text
outputs/bfi_requests/request.jsonl
outputs/bfi_requests/run.sh
outputs/response.jsonl
outputs/ocean_scores.csv
outputs/evaluation_metrics.csv
```

注意：`outputs/response.jsonl` 当前是 mock 响应，不是真实 Gemma 模型输出。mock 仅用于确认文件链路和处理脚本没有问题。

## 二、依赖环境

原仓库 `requirements.txt` 中：

```text
torch==2.1.1
transformers==4.38.2
```

本机是 Python 3.12.6，`torch==2.1.1` 没有可用 wheel，因此已调整为：

```text
torch==2.2.2
transformers==4.42.4
accelerate==0.31.0
```

原因：

- `torch==2.2.2` 支持当前 Python 3.12 环境。
- `transformers==4.42.4` 更适合加载 Gemma 2 系列模型。
- `accelerate` 用于 Hugging Face 大模型加载和设备映射。

环境创建命令：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果 pip 遇到本机证书问题，可用：

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

本机设备检测：

```text
CUDA: False
MPS: True
```

因此 Mac 上可以尝试 MPS 本地推理，但真实 2B 模型可能仍受内存和速度限制。

## 三、数据文件

新增样例对话：

```text
data/dialogues/p001_chat_6_202605200001.txt
data/dialogues/p002_chat_7_202605200002.txt
data/dialogues/p003_chat_6_202605200003.txt
```

文件命名遵循原仓库约定：

```text
{Client_ID}_chat_{Chatround_ID}_{Timestamp}.txt
```

对话格式：

```text
咨询师：欢迎你来聊聊，今天最想讨论的是什么？
来访者：最近工作节奏有点快，我想理清优先级，避免把事情都压到最后。
```

这些文本都是虚构匿名样例，不包含真实隐私信息。

新增真值：

```text
data/ground_truth.csv
```

字段：

```csv
session_id,user_id,extraversion,agreeableness,conscientiousness,negative_emotionality,open_mindedness
```

当前真值只是示例，用于验证评估脚本能运行，不代表论文真实数据。

## 四、原始请求生成流程

使用原仓库脚本：

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

当前样例共有 3 个 session，每个 session 生成 60 道 BFI 题请求，所以总计：

```text
180 outputs/bfi_requests/request.jsonl
```

请求 JSONL 每行结构类似：

```json
{
  "uuid": "p001_chat_6_202605200001_0_0",
  "model": "kurileo/Gemma-2-2b-it-BFI-Anonymous",
  "messages": [
    {"role": "system", "content": "Act like a real human..."},
    {"role": "user", "content": "欢迎你来聊聊，今天最想讨论的是什么？"},
    {"role": "assistant", "content": "最近工作节奏有点快..."},
    {"role": "user", "content": "在本次心理咨询结束之前，请根据聊天内容..."}
  ],
  "max_tokens": 256,
  "skip_special_tokens": true,
  "stop": []
}
```

`uuid` 解析规则：

```text
{session_id}_{question_id}_{try_id}
```

例如：

```text
p001_chat_6_202605200001_0_0
```

表示 session 为 `p001_chat_6_202605200001`，第 0 道 BFI 题，第 0 次尝试。

## 五、对 `src/utils.py` 的修改

原仓库的 `parse_session_data()` 用 `line.split(":")` 解析，只支持半角冒号，而且对中文全角冒号 `：` 会失败。

现在改成正则解析：

```python
match = re.match(r'^(咨询师|来访者)\s*[：:]\s*(.*)$', stripped)
```

这使得以下格式都可以读取：

```text
咨询师：你好
咨询师: 你好
来访者：最近有点累
来访者: 最近有点累
```

还修复了 `extract_choice()`：

原代码中：

```python
if text_match and len(text_match.group(0)) == 1:
```

中文选项如“非常不同意”长度不可能是 1，导致中文选项无法被正确抽取。

现在逻辑是：

```python
if text_match:
    return CHOICES[text_match.group(0)]
```

因此模型回答：

```text
我选择比较同意，因为...
```

可以被抽取为 `4`。

另外 `calculate_trait_scores()` 改为兼容字符串列名和整数列名，并对缺失值使用 `np.nanmean()`。

## 六、新增推理脚本 `src/run_local_inference.py`

这是本次复现的核心新增脚本。

默认模型：

```python
DEFAULT_MODEL = "kurileo/Gemma-2-2b-it-BFI-Anonymous"
```

支持后端：

```text
auto   自动检测。有 CUDA/MPS 就走 local，否则走 API。
local  Hugging Face Transformers 本地推理。
api    OpenAI-compatible /v1/chat/completions API。
mock   不下载模型、不调用 API，只生成占位响应，用于冒烟测试。
```

### 1. 本地推理

命令：

```bash
python src/run_local_inference.py \
  --backend local \
  --model_name kurileo/Gemma-2-2b-it-BFI-Anonymous \
  --requests_path outputs/bfi_requests/request.jsonl \
  --output_path outputs/response.jsonl
```

设备选择逻辑：

```python
def detect_device():
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"
```

如果是 CPU，默认不跑本地模型，会提示用 API；除非显式加：

```bash
--allow_cpu
```

### 2. Gemma system role 兼容

原始 `generate_bfi_requests.py` 会生成 `system` role，但 Gemma chat template 常常不接受 system role。

因此本地推理时加了 fallback：

```python
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
```

也就是：如果 tokenizer 的 chat template 不接受 `system`，就把 system prompt 合并到第一条 user 消息里。

API 后端不做这个转换，仍发送原始 messages。

### 3. API 推理

命令：

```bash
export BFI_API_URL="http://127.0.0.1:8000/v1/chat/completions"
export BFI_API_KEY="YOUR_API_KEY"
export BFI_API_MODEL="kurileo/Gemma-2-2b-it-BFI-Anonymous"

python src/run_local_inference.py \
  --backend api \
  --requests_path outputs/bfi_requests/request.jsonl \
  --output_path outputs/response.jsonl
```

也可以不用环境变量，直接传：

```bash
--api_url
--api_key
--api_model
```

API 请求体：

```python
payload = {
    "model": api_model,
    "messages": job["messages"],
    "max_tokens": args.max_new_tokens or job.get("max_tokens", 256),
    "temperature": args.temperature,
}
```

### 4. Mock 推理

已用这个模式跑通：

```bash
python src/run_local_inference.py \
  --backend mock \
  --requests_path outputs/bfi_requests/request.jsonl \
  --output_path outputs/response.jsonl
```

mock 输出结构：

```json
{
  "uuid": "p001_chat_6_202605200001_0_0",
  "model": "kurileo/Gemma-2-2b-it-BFI-Anonymous",
  "backend": "mock",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "我选择1。这是用于复现流程冒烟测试的占位输出。"
      }
    }
  ]
}
```

注意：mock 是固定规则，不代表真实模型预测。

## 七、改造后的 `src/process_results.py`

原仓库 `process_results.py` 有两个问题：

1. 写死了绝对路径：

```python
response_files = ['/path/to/response.jsonl']
output_file = '/path/to/output.csv'
```

2. 假设响应格式是 OpenAI cookbook parallel processor 返回的 list 格式。

现在改成命令行脚本：

```bash
python src/process_results.py \
  --response_paths outputs/response.jsonl \
  --output_path outputs/ocean_scores.csv
```

兼容两类 JSONL：

1. 本次 `run_local_inference.py` 输出的 dict 格式。
2. OpenAI-compatible batch/processor 可能输出的 list 格式。

核心读取逻辑：

```python
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
```

OCEAN 分数逻辑沿用原仓库：

```python
traits = {
    "extraversion": range(0, 56, 5),
    "agreeableness": range(1, 57, 5),
    "conscientiousness": range(2, 58, 5),
    "negative_emotionality": range(3, 59, 5),
    "open_mindedness": range(4, 60, 5)
}
```

也就是 60 个 BFI 条目按每 5 个循环对应一个人格维度，取均值。

输出：

```text
outputs/ocean_scores.csv
```

字段：

```csv
model_name,backend,user_id,session_id,chat_round,try_id,
pred_extraversion,pred_agreeableness,pred_conscientiousness,
pred_negative_emotionality,pred_open_mindedness,
pred_O,pred_C,pred_E,pred_A,pred_N
```

当前 mock 输出得到 3 行，每个 session 一行。

## 八、新增评估脚本 `src/evaluate_ocean.py`

命令：

```bash
python src/evaluate_ocean.py \
  --pred_path outputs/ocean_scores.csv \
  --truth_path data/ground_truth.csv \
  --output_path outputs/evaluation_metrics.csv
```

评估维度：

```python
TRAITS = {
    "open_mindedness": {"pred": ["pred_open_mindedness", "pred_O"], "truth": ["open_mindedness", "O"]},
    "conscientiousness": {"pred": ["pred_conscientiousness", "pred_C"], "truth": ["conscientiousness", "C"]},
    "extraversion": {"pred": ["pred_extraversion", "pred_E"], "truth": ["extraversion", "E"]},
    "agreeableness": {"pred": ["pred_agreeableness", "pred_A"], "truth": ["agreeableness", "A"]},
    "negative_emotionality": {"pred": ["pred_negative_emotionality", "pred_N"], "truth": ["negative_emotionality", "N"]},
}
```

计算：

- PCC：Pearson correlation。
- MAE：Mean Absolute Error。

输出字段：

```csv
trait,pcc,mae,n,prediction_column,ground_truth_column
```

注意：当前 mock 预测每个 session 的值相同，因此 PCC 是空值，这是数学上正常的，因为预测列没有方差。真实模型输出才有统计解释价值。

## 九、已经实际跑通的命令

以下命令已经运行成功：

```bash
python src/generate_bfi_requests.py \
  --model_name kurileo/Gemma-2-2b-it-BFI-Anonymous \
  --source_path data/dialogues \
  --output_path outputs/bfi_requests
```

结果：

```text
Total number of files: 3
Total number of jobs: 180
Bash script generated:
bash outputs/bfi_requests/run.sh
```

```bash
python src/run_local_inference.py \
  --backend mock \
  --requests_path outputs/bfi_requests/request.jsonl \
  --output_path outputs/response.jsonl
```

结果：

```text
Wrote 180 responses to outputs/response.jsonl
```

```bash
python src/process_results.py \
  --response_paths outputs/response.jsonl \
  --output_path outputs/ocean_scores.csv
```

结果：

```text
Wrote OCEAN scores to outputs/ocean_scores.csv
```

```bash
python src/evaluate_ocean.py \
  --pred_path outputs/ocean_scores.csv \
  --truth_path data/ground_truth.csv \
  --output_path outputs/evaluation_metrics.csv
```

结果：

```text
Wrote evaluation metrics to outputs/evaluation_metrics.csv
```

语法检查也已通过：

```bash
python -m py_compile \
  src/generate_bfi_requests.py \
  src/run_local_inference.py \
  src/process_results.py \
  src/evaluate_ocean.py \
  src/utils.py
```

## 十、推荐给后续 GPT 的理解路径

如果另一个 GPT 接手，建议按这个顺序读：

1. `README_REPRODUCE.md`
   - 先理解用户级复现命令。
2. `data/dialogues/*.txt`
   - 看输入对话格式。
3. `src/generate_bfi_requests.py`
   - 看如何把对话变成 60 道 BFI 请求。
4. `src/utils.py`
   - 看解析对话、抽取选项、OCEAN 计分规则。
5. `src/run_local_inference.py`
   - 看本地/API/mock 推理后端。
6. `src/process_results.py`
   - 看模型回复如何变成 session 级 OCEAN CSV。
7. `src/evaluate_ocean.py`
   - 看预测分和真值如何计算 PCC/MAE。

## 十一、如果要继续做真实模型推理

下一步应该把 mock 输出换成真实输出。

### 方案 A：Mac 本机 MPS 尝试

```bash
source .venv/bin/activate

python src/run_local_inference.py \
  --backend local \
  --model_name kurileo/Gemma-2-2b-it-BFI-Anonymous \
  --requests_path outputs/bfi_requests/request.jsonl \
  --output_path outputs/response.local.jsonl \
  --resume
```

然后：

```bash
python src/process_results.py \
  --response_paths outputs/response.local.jsonl \
  --output_path outputs/ocean_scores.local.csv

python src/evaluate_ocean.py \
  --pred_path outputs/ocean_scores.local.csv \
  --truth_path data/ground_truth.csv \
  --output_path outputs/evaluation_metrics.local.csv
```

### 方案 B：用 vLLM/sglang/API 服务

如果有远程 GPU 或本地服务：

```bash
export BFI_API_URL="http://127.0.0.1:8000/v1/chat/completions"
export BFI_API_KEY="YOUR_API_KEY"
export BFI_API_MODEL="kurileo/Gemma-2-2b-it-BFI-Anonymous"

python src/run_local_inference.py \
  --backend api \
  --requests_path outputs/bfi_requests/request.jsonl \
  --output_path outputs/response.api.jsonl \
  --resume
```

然后同样跑 `process_results.py` 和 `evaluate_ocean.py`。

## 十二、当前工作区状态说明

主要修改/新增文件：

```text
M  requirements.txt
M  src/process_results.py
M  src/utils.py
A  .gitignore
A  README_REPRODUCE.md
A  HANDOFF_FOR_GPT.md
A  data/dialogues/p001_chat_6_202605200001.txt
A  data/dialogues/p002_chat_7_202605200002.txt
A  data/dialogues/p003_chat_6_202605200003.txt
A  data/ground_truth.csv
A  outputs/bfi_requests/request.jsonl
A  outputs/bfi_requests/run.sh
A  outputs/response.jsonl
A  outputs/ocean_scores.csv
A  outputs/evaluation_metrics.csv
A  src/evaluate_ocean.py
A  src/run_local_inference.py
```

`.venv/`、`__pycache__/`、`.DS_Store` 已加入 `.gitignore`，不应提交。

## 十三、重要注意事项

1. 当前复现的是推理流程，不是训练流程。
2. 当前样例数据是虚构匿名样例，不是论文真实数据。
3. 当前 `outputs/response.jsonl` 是 mock 响应，不应拿它解读人格预测效果。
4. 真实模型输出是否稳定，取决于模型、temperature、chat template、设备和 API 服务实现。
5. 如果真实模型回答中没有明确数字或中文选项，`process_results.py` 会把该题记为缺失值。
6. 如果某个维度缺失题目过多，OCEAN 均值和后续 PCC/MAE 都会受影响。
7. 当前 `ground_truth.csv` 只有 3 条玩具数据，PCC 统计意义很弱；真实评估需要更多样本。

## 十四、一句话总结

现在仓库已经从“只能生成 BFI 请求、结果处理还写死路径”的公开代码，补成了一个完整的相对路径推理复现链路：

```text
中文咨询 txt
  -> generate_bfi_requests.py
  -> BFI request.jsonl
  -> run_local_inference.py 或 API
  -> response.jsonl
  -> process_results.py
  -> ocean_scores.csv
  -> evaluate_ocean.py
  -> evaluation_metrics.csv
```

当前链路已通过 mock 后端跑通，后续只需要替换成真实 Hugging Face/API 模型输出即可继续验证论文方法。
