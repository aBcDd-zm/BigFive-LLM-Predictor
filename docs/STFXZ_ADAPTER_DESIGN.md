# STFXZ Adapter Design

本阶段只为 STFXZ 职场剧情项目预留最小数据适配层，不接后端数据库，也不改变现有 BFI pipeline。

## 目标

当前 BFI pipeline 使用的 session 格式是：

```python
{
    "session_id": "...",
    "user": "...",
    "chat_round": "...",
    "timestamp": "...",
    "utterance_li": [
        {"speaker": "咨询师", "utter": "..."},
        {"speaker": "来访者", "utter": "..."},
    ],
}
```

STFXZ 项目未来可能产生的是游戏日志，包括场景、玩家发言、玩家选择、NPC 回应、任务选项和行为证据。`src/adapters/stfxz_adapter.py` 的职责是把这些日志先转换成上述 session dict，让后续可以复用现有 BFI 请求生成逻辑。

## 最小输入约定

adapter 接受一个 dict，推荐字段如下：

```python
{
    "session_id": "stfxz_p001_day1",
    "user_id": "p001",
    "day": "day1",
    "timestamp": "2026-05-20T10:00:00",
    "scene": "项目晨会中，主管要求你说明延期原因。",
    "events": [
        {
            "task_option": "向主管说明风险并提出补救计划",
            "player_dialogue": "我先说明当前阻塞，再给出新的排期。",
            "player_choice": "主动沟通",
            "behavior_evidence": ["承担责任", "提前同步风险"],
            "npc_response": "主管要求你今天下班前给出详细计划。"
        }
    ]
}
```

兼容别名：

- session id：`session_id`、`log_id`、`id`
- user：`user`、`user_id`、`player_id`
- round：`chat_round`、`day`、`chapter`
- timestamp：`timestamp`、`created_at`、`time`
- events：`events`、`turns`、`records`

## 输出映射

- 顶层 `scene/scenario/context` 会转换成第一条 `咨询师` 话语：`你正在经历一个职场情境：...`
- event 中的 `scene/context/situation` 和 `task/task_option/objective` 会转换成 `咨询师` 话语。
- event 中的 `player_dialogue/player_choice/player_action/behavior_evidence` 会合并成 `来访者` 话语。
- event 中的 `npc_response/npc_reply/response` 会转换成 `咨询师` 话语。

示例输出：

```python
{
    "session_id": "stfxz_p001_day1",
    "user": "p001",
    "chat_round": "day1",
    "timestamp": "2026-05-20T10:00:00",
    "utterance_li": [
        {
            "speaker": "咨询师",
            "utter": "你正在经历一个职场情境：项目晨会中，主管要求你说明延期原因。"
        },
        {
            "speaker": "咨询师",
            "utter": "任务/选项：向主管说明风险并提出补救计划"
        },
        {
            "speaker": "来访者",
            "utter": "玩家发言：我先说明当前阻塞，再给出新的排期。；玩家选择：主动沟通；行为证据：承担责任；提前同步风险"
        },
        {
            "speaker": "咨询师",
            "utter": "NPC回应：主管要求你今天下班前给出详细计划。"
        }
    ]
}
```

## 非目标

- 不直接读取数据库。
- 不定义最终 STFXZ 后端 schema。
- 不把 adapter 自动接入 `generate_bfi_requests.py`。
- 不判断玩家行为对应哪个人格维度；人格预测仍交给后续 BFI prompt + LLM 流程。

## 后续接入建议

1. 等 STFXZ 日志 schema 稳定后，固定输入字段并减少别名。
2. 增加批量转换函数，把多个 log dict 写成当前 pipeline 可读的中间格式。
3. 如果要复用 `generate_bfi_requests.py`，可新增一个入口参数，让它既能读取 `data/dialogues/*.txt`，也能读取 adapter 生成的 session list。
4. 在真实接入前，补充脱敏规则，避免玩家日志中的真实个人信息进入模型请求。
