def _first_present(data, keys, default=""):
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return default


def _as_text(value):
    if value in (None, ""):
        return ""
    if isinstance(value, list):
        return "；".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if item not in (None, ""):
                parts.append(f"{key}：{item}")
        return "；".join(parts)
    return str(value).strip()


def _append_utterance(utterances, speaker, utter):
    utter = _as_text(utter)
    if utter:
        utterances.append({"speaker": speaker, "utter": utter})


def _event_scene_text(event):
    scene = _first_present(event, ["scene", "context", "situation"])
    task = _first_present(event, ["task", "task_option", "objective"])
    parts = []
    if scene:
        parts.append(f"当前职场情境：{scene}")
    if task:
        parts.append(f"任务/选项：{task}")
    return "；".join(parts)


def _event_player_text(event):
    parts = []
    player_text = _first_present(event, ["player_dialogue", "player_text", "utterance", "message"])
    player_choice = _first_present(event, ["player_choice", "choice", "selected_option"])
    player_action = _first_present(event, ["player_action", "action"])
    evidence = _first_present(event, ["behavior_evidence", "evidence", "behavior"])

    if player_text:
        parts.append(f"玩家发言：{_as_text(player_text)}")
    if player_choice:
        parts.append(f"玩家选择：{_as_text(player_choice)}")
    if player_action:
        parts.append(f"玩家行动：{_as_text(player_action)}")
    if evidence:
        parts.append(f"行为证据：{_as_text(evidence)}")

    return "；".join(parts)


def convert_stfxz_log_to_session(log_json: dict) -> dict:
    """
    Convert a STFXZ workplace-game log into the session format used by this BFI pipeline.
    """
    if not isinstance(log_json, dict):
        raise ValueError("log_json must be a dict.")

    session_id = _first_present(log_json, ["session_id", "log_id", "id"], "stfxz_session")
    user = _first_present(log_json, ["user", "user_id", "player_id"], "unknown_user")
    chat_round = _first_present(log_json, ["chat_round", "day", "chapter"], "")
    timestamp = _first_present(log_json, ["timestamp", "created_at", "time"], "")

    utterances = []
    scenario = _first_present(log_json, ["scenario", "scene", "context"])
    if scenario:
        _append_utterance(utterances, "咨询师", f"你正在经历一个职场情境：{_as_text(scenario)}")

    events = _first_present(log_json, ["events", "turns", "records"], [])
    if isinstance(events, dict):
        events = [events]

    for event in events:
        if not isinstance(event, dict):
            _append_utterance(utterances, "来访者", f"玩家行为证据：{_as_text(event)}")
            continue

        _append_utterance(utterances, "咨询师", _event_scene_text(event))
        _append_utterance(utterances, "来访者", _event_player_text(event))

        npc_response = _first_present(event, ["npc_response", "npc_reply", "response"])
        if npc_response:
            _append_utterance(utterances, "咨询师", f"NPC回应：{_as_text(npc_response)}")

    if not utterances:
        _append_utterance(utterances, "咨询师", "你正在经历一个职场情境：暂无场景描述。")

    return {
        "session_id": str(session_id),
        "user": str(user),
        "chat_round": str(chat_round),
        "timestamp": str(timestamp),
        "utterance_li": utterances,
        }
