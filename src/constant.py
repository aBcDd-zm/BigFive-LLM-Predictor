from dataclasses import dataclass


BFI_TRAIT_ORDER = (
    "extraversion",
    "agreeableness",
    "conscientiousness",
    "negative_emotionality",
    "open_mindedness",
    )

BFI_REVERSE_ITEM_NUMBERS = {
    3, 4, 5, 8, 9, 11, 12, 16, 17, 22,
    23, 24, 25, 26, 28, 29, 30, 31, 36, 37,
    42, 44, 45, 47, 48, 49, 50, 51, 55, 58,
    }


def _parse_bfi_item(index, item):
    item_id, text = item.split(".", 1)
    bfi2_item_number = index + 1
    return {
        "index": index,
        "id": item_id.strip(),
        "text": text.strip(),
        "trait": BFI_TRAIT_ORDER[index % len(BFI_TRAIT_ORDER)],
        "reverse": bfi2_item_number in BFI_REVERSE_ITEM_NUMBERS,
        }


def build_bfi_items(items):
    return [_parse_bfi_item(index, item) for index, item in enumerate(items)]


@dataclass
class Constant:
    API_KEY = ""  # Your OpenAI API key
    REQUEST_URL = ""  # Endpoint for the API request, e.g. "http://127.0.0.1:8009/v1/chat/completions" or OpenAI API endpoint
    SCRIPT_FILE = ""  # https://github.com/openai/openai-cookbook/blob/main/examples/api_request_parallel_processor.py

    BFI_ITEM_LI = ['X3. 我是一个性格外向、喜欢交际的人',
                   'X4. 我是一个心肠柔软、有同情心的人',
                   'X5. 我是一个缺乏条理的人',
                   'X6. 我是一个从容、善于处理压力的人',
                   'X7. 我是一个对艺术没有什么兴趣的人',
                   'X8. 我是一个性格坚定自信、敢于表达自己的观点的人',
                   'X9. 我是一个为人恭谦、尊重他人的人',
                   'X10.我是一个比较懒的人',
                   'X11.我是一个经历挫折后仍能保持积极心态的人',
                   'X12.我是一个对许多不同的事物都感兴趣的人',
                   'X13.我是一个很少觉得兴奋或者特别想要做什么的人',
                   'X14.我是一个常常挑别人毛病的人',
                   'X15.我是一个可信赖的、可靠的人',
                   'X16.我是一个喜怒无常、情绪起伏较多的人',
                   'X17.我是一个善于创造、能找到聪明的方法来做事的人',
                   'X18.我是一个比较安静的人',
                   'X19.我是一个对他人没有什么同情心的人',
                   'X20.我是一个做事有计划有条理的人',
                   'X21.我是一个容易紧张的人',
                   'X22.我是一个着迷于艺术、音乐或文学的人',
                   'X23.我是一个常常处于主导地位、像个领导一样的人',
                   'X24.我是一个常与他人意见不和的人',
                   'X25.我是一个很难开始行动起来去完成一项任务的人',
                   'X26.我是一个觉得有安全感、对自己满意的人',
                   'X27.我是一个不喜欢知识性或者哲学性强的讨论的人',
                   'X28.我是一个不如别人有活力的人',
                   'X29.我是一个宽宏大量的人',
                   'X30.我是一个有时比较没有责任心的人',
                   'X31.我是一个情绪稳定、不易生气的人',
                   'X32.我是一个几乎没有什么创造性的人',
                   'X33.我是一个有时会害羞、比较内向的人',
                   'X34.我是一个乐于助人、待人无私的人',
                   'X35.我是一个习惯让事物保持整洁有序的人',
                   'X36.我是一个时常忧心忡忡、担心很多事情的人',
                   'X37.我是一个重视艺术与审美的人',
                   'X38.我感觉自己很难对他人产生影响',
                   'X39.我是一个有时对人比较粗鲁的人',
                   'X40.我是一个有效率、做事有始有终的人',
                   'X41.我是一个时常觉得悲伤的人',
                   'X42.我是一个思想深刻的人',
                   'X43.我是一个精力充沛的人',
                   'X44.我是一个不相信别人、怀疑别人意图的人',
                   'X45.我是一个可靠的、总是值得他人信赖的人',
                   'X46.我是一个能够控制自己的情绪的人',
                   'X47.我是一个缺乏想象力的人',
                   'X48.我是一个爱说话、健谈的人',
                   'X49.我是一个有时对人冷淡、漠不关心的人',
                   'X50.我是一个乱糟糟的、不爱收拾的人',
                   'X51.我是一个很少觉得焦虑或者害怕的人',
                   'X52.我是一个觉得诗歌、戏剧很无聊的人',
                   'X53.我是一个更喜欢让别人来领头负责的人',
                   'X54.我是一个待人谦逊礼让的人',
                   'X55.我是一个有恒心、能坚持把事情做完的人',
                   'X56.我是一个时常觉得郁郁寡欢的人',
                   'X57.我是一个对抽象的概念和想法没什么兴趣的人',
                   'X58.我是一个充满热情的人',
                   'X59.我是一个把人往最好的方面想的人',
                   'X60.我是一个有时候会做出一些不负责任的行为的人',
                   'X61.我是一个情绪多变、容易愤怒的人',
                   'X62.我是一个有创意、能想出新点子的人'
                   ]


Constant.BFI_ITEMS = build_bfi_items(Constant.BFI_ITEM_LI)
