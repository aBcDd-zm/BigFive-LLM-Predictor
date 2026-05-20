# BFI Item Metadata Review

本文档用于人工复核 `Constant.BFI_ITEMS` 的维度归属和反向计分标记。

当前阶段采用“机制优先”策略：

- `trait` 按原代码硬编码顺序派生：`index % 5` 依次对应 `extraversion`、`agreeableness`、`conscientiousness`、`negative_emotionality`、`open_mindedness`。
- `reverse` 暂时全部为 `False`，仅表示尚未人工确认。
- 这不代表量表最终反向键值。确认每题是否反向后，再更新 `src/constant.py` 中的 `Constant.BFI_ITEMS`。
- 原始题目中存在编号重复或跳号，例如 `X18` 出现两次；本阶段保留原仓库文本，不自行修正。

| index | id | trait | reverse | text |
|---:|---|---|---|---|
| 0 | X3 | extraversion | False | 我是一个性格外向、喜欢交际的人 |
| 1 | X4 | agreeableness | False | 我是一个心肠柔软、有同情心的人 |
| 2 | X5 | conscientiousness | False | 我是一个有条理的人 |
| 3 | X6 | negative_emotionality | False | 我是一个焦躁、很难处理压力的人 |
| 4 | X7 | open_mindedness | False | 我是一个对艺术感兴趣的人 |
| 5 | X8 | extraversion | False | 我是一个性格坚定自信、敢于表达自己的观点的人 |
| 6 | X9 | agreeableness | False | 我是一个为人恭敬、谦虚、尊重他人的人 |
| 7 | X10 | conscientiousness | False | 我是一个比较懒的人 |
| 8 | X11 | negative_emotionality | False | 我是一个经历挫折后仍能保持积极心态的人 |
| 9 | X12 | open_mindedness | False | 我是一个对许多不同的事物都感兴趣的人 |
| 10 | X13 | extraversion | False | 我是一个经常觉得兴奋或者特别想要做什么的人 |
| 11 | X14 | agreeableness | False | 我是一个常常包容别人的毛病的人 |
| 12 | X18 | conscientiousness | False | 我是一个比较活泼的人 |
| 13 | X16 | negative_emotionality | False | 我是一个喜怒无常、情绪起伏较多的人 |
| 14 | X17 | open_mindedness | False | 我是一个善于创造、能找到聪明的方法来做事的人 |
| 15 | X18 | extraversion | False | 我是一个比较安静的人 |
| 16 | X19 | agreeableness | False | 我是一个对他人有同情心的人 |
| 17 | X20 | conscientiousness | False | 我是一个做事有计划有条理的人 |
| 18 | X21 | negative_emotionality | False | 我是一个容易紧张的人 |
| 19 | X22 | open_mindedness | False | 我是一个着迷与艺术、音乐和文学的人 |
| 20 | X23 | extraversion | False | 我是一个常常处于主导地位、像一个领导一样的人 |
| 21 | X24 | agreeableness | False | 我是一个常与他人意见统一的人 |
| 22 | X25 | conscientiousness | False | 我是一个很容易行动起来去完成一项任务的人 |
| 23 | X26 | negative_emotionality | False | 我是一个觉得没有安全感、对自己不满意的人 |
| 24 | X27 | open_mindedness | False | 我是一个喜欢知识性或者哲学性强的讨论的人 |
| 25 | X28 | extraversion | False | 我是一个比别人有活力的人 |
| 26 | X29 | agreeableness | False | 我是一个宽宏大量的人 |
| 27 | X30 | conscientiousness | False | 我是一个总是有责任心的人 |
| 28 | X31 | negative_emotionality | False | 我是一个情绪不稳定、易生气的人 |
| 29 | X32 | open_mindedness | False | 我是一个有创造性的人 |
| 30 | X33 | extraversion | False | 我是一个很少害羞、比较外向的人 |
| 31 | X34 | agreeableness | False | 我是一个乐于助人、对待别人无私的人 |
| 32 | X35 | conscientiousness | False | 我是一个习惯让事物保持整洁有序的人 |
| 33 | X36 | negative_emotionality | False | 我是一个时常忧心忡忡担心很多事情的人 |
| 34 | X37 | open_mindedness | False | 我是一个重视艺术与审美的人 |
| 35 | X38 | extraversion | False | 我感觉自己容易对他人产生影响 |
| 36 | X39 | agreeableness | False | 我是一个对人比较体贴的人 |
| 37 | X40 | conscientiousness | False | 我是一个有效率、做事有始有终的人 |
| 38 | X41 | negative_emotionality | False | 我是一个时常觉得悲伤的人 |
| 39 | X42 | open_mindedness | False | 我是一个思想深刻的人 |
| 40 | X43 | extraversion | False | 我是一个精力充沛的人 |
| 41 | X44 | agreeableness | False | 我是一个相信别人、相信别人意图的人 |
| 42 | X45 | conscientiousness | False | 我是一个可靠的、总是值得他人信赖的人 |
| 43 | X46 | negative_emotionality | False | 我是一个很难控制自己的情绪的人 |
| 44 | X47 | open_mindedness | False | 我是一个充满想象力的人 |
| 45 | X48 | extraversion | False | 我是一个爱说话、健谈的人 |
| 46 | X49 | agreeableness | False | 我是一个会对人热情、关心他人的人 |
| 47 | X50 | conscientiousness | False | 我是一个整洁的、爱收拾的人 |
| 48 | X51 | negative_emotionality | False | 我是一个时常觉得焦虑、或者害怕的人 |
| 49 | X52 | open_mindedness | False | 我是一个觉得诗歌、戏剧很有趣的人 |
| 50 | X53 | extraversion | False | 我是一个更喜欢自己来领头负责的人 |
| 51 | X54 | agreeableness | False | 我是一个待人谦逊礼让的人 |
| 52 | X55 | conscientiousness | False | 我是一个有恒心、能坚持把事情做完的人 |
| 53 | X56 | negative_emotionality | False | 我是一个时常觉得郁郁寡欢的人 |
| 54 | X57 | open_mindedness | False | 我是一个对抽象的概念和想法很有兴趣的人 |
| 55 | X58 | extraversion | False | 我是一个充满热情的人 |
| 56 | X59 | agreeableness | False | 我是一个把人往最好的方面想的人 |
| 57 | X60 | conscientiousness | False | 我是一个总是会做出负责任的行为的人 |
| 58 | X61 | negative_emotionality | False | 我是一个情绪多变、容易愤怒的人 |
| 59 | X62 | open_mindedness | False | 我是一个有创意、能想出新点子的人 |

## 人工复核建议

1. 确认论文实际使用的是哪一个 BFI 版本或中文修订版本。
2. 对照该版本的正式计分键，逐题确认 `trait` 和 `reverse`。
3. 对确认需要反向计分的题目，将 `Constant.BFI_ITEMS` 对应项的 `reverse` 改为 `True`。
4. 重新运行 `tests/test_convert_scores.py` 和完整 mock 流程，确认 OCEAN 输出符合预期。
