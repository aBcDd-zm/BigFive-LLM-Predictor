from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utils import extract_choice_json


def test_extract_json_int():
    assert extract_choice_json('{"choice": 5}') == 5


def test_extract_json_str():
    assert extract_choice_json('{"choice": "4"}') == 4


def test_extract_json_markdown_block():
    assert extract_choice_json('```json\n{"choice": 3}\n```') == 3


def test_extract_text_label_fallback():
    assert extract_choice_json("我选择比较同意，因为这符合我的情况。") == 4


def test_extract_choose_number_not_first_number():
    assert extract_choice_json("我有3个理由，所以最终选择5。") == 5


def test_extract_invalid():
    assert extract_choice_json("无法判断") == -1
