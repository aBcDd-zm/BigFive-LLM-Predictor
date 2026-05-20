from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adapters.stfxz_adapter import convert_stfxz_log_to_session


def test_convert_stfxz_log_to_session_basic_workplace_log():
    log = {
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
                "npc_response": "主管要求你今天下班前给出详细计划。",
                }
            ],
        }

    session = convert_stfxz_log_to_session(log)

    assert session["session_id"] == "stfxz_p001_day1"
    assert session["user"] == "p001"
    assert session["chat_round"] == "day1"
    assert session["timestamp"] == "2026-05-20T10:00:00"
    assert session["utterance_li"][0] == {
        "speaker": "咨询师",
        "utter": "你正在经历一个职场情境：项目晨会中，主管要求你说明延期原因。",
        }
    assert any("玩家选择：主动沟通" in item["utter"] for item in session["utterance_li"])
    assert any("行为证据：承担责任；提前同步风险" in item["utter"] for item in session["utterance_li"])
    assert session["utterance_li"][-1]["speaker"] == "咨询师"
    assert "NPC回应" in session["utterance_li"][-1]["utter"]


def test_convert_stfxz_log_to_session_supports_aliases():
    log = {
        "log_id": "log-42",
        "player_id": "player-42",
        "chapter": "chapter-2",
        "created_at": "2026-05-20",
        "turns": {
            "context": "同事临时请你帮忙收尾。",
            "selected_option": "先确认边界再答应",
            "action": "询问截止时间和交付标准",
            "npc_reply": "同事补充了任务细节。",
            },
        }

    session = convert_stfxz_log_to_session(log)

    assert session["session_id"] == "log-42"
    assert session["user"] == "player-42"
    assert session["chat_round"] == "chapter-2"
    assert session["timestamp"] == "2026-05-20"
    assert any("当前职场情境：同事临时请你帮忙收尾。" in item["utter"] for item in session["utterance_li"])
    assert any("玩家选择：先确认边界再答应" in item["utter"] for item in session["utterance_li"])
    assert any("玩家行动：询问截止时间和交付标准" in item["utter"] for item in session["utterance_li"])


def test_convert_stfxz_log_to_session_rejects_non_dict():
    with pytest.raises(ValueError, match="log_json must be a dict"):
        convert_stfxz_log_to_session(["not", "a", "dict"])


def test_convert_stfxz_log_to_session_adds_default_scene_for_empty_log():
    session = convert_stfxz_log_to_session({})

    assert session["session_id"] == "stfxz_session"
    assert session["user"] == "unknown_user"
    assert session["utterance_li"] == [
        {"speaker": "咨询师", "utter": "你正在经历一个职场情境：暂无场景描述。"}
        ]
