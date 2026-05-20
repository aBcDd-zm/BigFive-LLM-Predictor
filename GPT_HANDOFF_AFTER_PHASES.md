# 给 GPT 的交接文档：Big Five / OCEAN 复现流水线阶段优化后状态

这份文档用于交接给另一个 GPT 或协作者，帮助其快速理解当前项目已经做到哪里、代码结构是什么、哪些问题已经解决、哪些问题仍需要讨论。

当前仓库路径：

```text
/Users/chenhongmiao/Downloads/心里比赛与llm/BigFive-LLM-Predictor
```

当前状态：

- 分阶段优化计划的阶段 1 到阶段 6 已全部完成。
- 当前 `git status --short` 无输出，工作区干净。
- 当前测试全部通过：`18 passed`。
- 目前仍然只复现推理流程，不包含 SFT / DPO 微调。

## 1. 项目现在在做什么

这是一个 Big Five / OCEAN 人格预测复现流水线。核心流程是：

```text
中文心理咨询对话 txt
  -> 生成 60 道 BFI 问卷请求 request.jsonl
  -> local / api / mock 推理得到 response.jsonl
  -> 从模型回答中提取 1-5 分
  -> 汇总成 OCEAN 五维人格分数 ocean_scores.csv
  -> 与 ground_truth.csv 对比，计算 PCC / MAE
```

主命令路径已经写在：

```text
README_REPRODUCE.md
```

最简单的冒烟测试是：

```bash
scripts/run_reproduce_mock.sh
```

Windows PowerShell 版：

```powershell
.\scripts\run_reproduce_mock.ps1
```

注意：mock 只验证流水线，不代表真实模型效果。

## 2. 已完成的 6 个阶段

### 阶段 1：JSON 输出解析

目的：解决模型自然语言回答容易被误读的问题。

已完成：

- `generate_bfi_requests.py` 的 prompt 已要求模型严格输出 JSON：

```json
{
  "choice": 1,
  "label": "非常不同意",
  "reason": "一句话说明理由"
}
```

- `utils.py` 新增 `extract_choice_json()`。
- `process_results.py` 改为优先用 `extract_choice_json()`。
- fallback 支持中文标签和显式选择文本，例如：

```text
我选择比较同意，因为这符合我的情况。
我有3个理由，所以最终选择5。
```

相关测试：

```text
tests/test_extract_choice.py
```

### 阶段 2：BFI 题目元数据化 + 反向计分机制

目的：让 60 道 BFI 题不再只靠题号位置硬编码算分。

已完成：

- `constant.py` 保留 `Constant.BFI_ITEM_LI`。
- 新增 `Constant.BFI_ITEMS`，每题包含：

```python
{
    "index": 0,
    "id": "X3",
    "text": "我是一个性格外向、喜欢交际的人",
    "trait": "extraversion",
    "reverse": False,
}
```

- `utils.convert_scores()` 改为读取 `BFI_ITEMS`。
- 如果某题 `reverse=True`，计分会执行：

```python
score = 6 - score
```

重要说明：

- 当前所有 `reverse` 都是 `False`。
- 这是“机制优先”，不是最终量表键值。
- 需要后续人工确认哪些题应该反向计分。

人工复核文档：

```text
docs/BFI_ITEM_REVIEW.md
```

相关测试：

```text
tests/test_convert_scores.py
```

### 阶段 3：分组评估

目的：避免把不同模型、不同后端、不同 try_id 的结果混在一起算指标。

已完成：

- `evaluate_ocean.py` 新增 `evaluate_predictions()`。
- 如果预测文件中存在以下列，会分组计算：

```text
model_name
backend
try_id
```

- 如果这些列不存在，则保持整体评估。

输出在有分组列时类似：

```text
model_name,backend,try_id,trait,pcc,mae,n,prediction_column,ground_truth_column
```

相关测试：

```text
tests/test_evaluate_ocean.py
```

### 阶段 4：一键 mock 复现脚本

目的：用一条命令跑通完整流程。

已完成：

```text
scripts/run_reproduce_mock.sh
scripts/run_reproduce_mock.ps1
```

脚本会执行：

```text
generate_bfi_requests.py
run_local_inference.py --backend mock
process_results.py
evaluate_ocean.py
```

输出：

```text
outputs/bfi_requests/request.jsonl
outputs/response.jsonl
outputs/ocean_scores.csv
outputs/evaluation_metrics.csv
```

### 阶段 5：README_REPRODUCE 更新

目的：让新手能照文档复现。

已完成：

```text
README_REPRODUCE.md
```

文档已覆盖：

- 项目整体流水线
- 输入数据格式
- 一键 mock 复现
- API / local / mock 推理
- OCEAN 输出说明
- evaluation metrics 说明
- JSON 输出解析
- BFI 元数据与反向计分
- 常见问题

### 阶段 6：STFXZ 职场项目 adapter

目的：为 STFXZ 职场剧情游戏日志预留接入层。

已完成：

```text
src/adapters/stfxz_adapter.py
docs/STFXZ_ADAPTER_DESIGN.md
tests/test_stfxz_adapter.py
```

核心函数：

```python
def convert_stfxz_log_to_session(log_json: dict) -> dict:
    ...
```

它会把 STFXZ 游戏日志转换成当前 BFI pipeline 可用的 session 格式：

```python
{
    "session_id": "...",
    "user": "...",
    "chat_round": "...",
    "timestamp": "...",
    "utterance_li": [
        {"speaker": "咨询师", "utter": "..."},
        {"speaker": "来访者", "utter": "..."}
    ]
}
```

当前 adapter 只做格式转换，不接数据库，不自动接入 `generate_bfi_requests.py`。

## 3. 当前关键文件索引

核心流程：

```text
src/generate_bfi_requests.py
src/run_local_inference.py
src/process_results.py
src/evaluate_ocean.py
src/utils.py
src/constant.py
```

STFXZ adapter：

```text
src/adapters/stfxz_adapter.py
docs/STFXZ_ADAPTER_DESIGN.md
```

复现说明和复核文档：

```text
README_REPRODUCE.md
docs/BFI_ITEM_REVIEW.md
```

一键脚本：

```text
scripts/run_reproduce_mock.sh
scripts/run_reproduce_mock.ps1
```

测试：

```text
tests/test_extract_choice.py
tests/test_convert_scores.py
tests/test_evaluate_ocean.py
tests/test_stfxz_adapter.py
```

示例数据：

```text
data/dialogues/
data/ground_truth.csv
```

## 4. 当前验证情况

已运行：

```bash
source .venv/bin/activate && python -m pytest
```

结果：

```text
18 passed
```

也已跑通过：

```bash
scripts/run_reproduce_mock.sh
```

mock 输出会刷新：

```text
outputs/bfi_requests/request.jsonl
outputs/response.jsonl
outputs/ocean_scores.csv
outputs/evaluation_metrics.csv
```

## 5. 目前最需要和 GPT 讨论的问题

下面这些才是后续真正影响“实验结果是否有意义”的问题。

### 问题 A：是否现在跑真实模型

当前 mock 只验证链路。下一步如果要得到真实 OCEAN 预测，需要选择：

1. 本机 Hugging Face local 推理。
2. OpenAI-compatible API 推理，例如 vLLM / sglang / 远程 GPU 服务。
3. 继续只做 mock，不跑真实模型。

建议优先讨论 API / 远程 GPU，因为本机跑 2B 模型可能慢或受内存限制。

### 问题 B：BFI 反向计分键值如何确认

当前 `reverse=False` 只是占位。后续必须确认：

- 论文实际使用的是哪一个 BFI 版本。
- 60 道中文题分别属于哪个维度。
- 哪些题需要反向计分。

确认后再更新 `Constant.BFI_ITEMS` 的 `reverse`。

### 问题 C：STFXZ 日志 schema 是否稳定

adapter 当前支持宽松字段别名，但真实接入前应讨论：

- 游戏日志最终字段名是什么。
- 玩家选择、行为证据、NPC 回应的粒度是什么。
- 是否需要脱敏。
- 是否要把 adapter 自动接入 `generate_bfi_requests.py`。

### 问题 D：OCEAN 结果如何给用户解释

当前只输出 CSV 分数和指标。后续产品化需要讨论：

- 分数解释文案。
- 用户画像报告。
- 置信度或证据引用。
- 是否展示“人格维度不是诊断”的免责声明。

## 6. 建议下一步路线

推荐顺序：

1. 先确认 BFI 反向计分键值。
2. 再跑真实模型/API 推理。
3. 对真实输出跑 `process_results.py` 和 `evaluate_ocean.py`。
4. 如果要接 STFXZ，先拿 1-3 条真实或模拟游戏日志，用 adapter 转换并人工检查文本是否合理。
5. 最后再考虑报告生成、可视化或产品接入。

## 7. 交接给 GPT 的一句话

这个项目现在已经不是“零散脚本”，而是一条可测试、可 mock 复现、支持 JSON 解析、元数据计分、分组评估，并预留 STFXZ 游戏日志接入的 Big Five / OCEAN 推理流水线；下一步讨论重点应从“代码能不能跑”转向“反向计分是否正确、真实模型怎么跑、STFXZ 数据如何解释”。
