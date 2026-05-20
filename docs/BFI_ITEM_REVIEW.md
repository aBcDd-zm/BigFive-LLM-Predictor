# BFI Item Metadata Review

本文档用于人工复核 `Constant.BFI_ITEMS` 的维度归属和反向计分标记。

## 阶段 7 说明

当前 `Constant.BFI_ITEMS` 已经支持 `trait` 与 `reverse` 字段，但 `reverse` 仍可能是占位值。

本文件和 `docs/BFI_ITEM_REVIEW_TABLE.md` 用于人工复核：

1. 每道题属于哪个 OCEAN 维度。
2. 每道题是否需要反向计分。
3. 中文翻译是否与原量表含义一致。
4. 是否与论文实际使用的 BFI 版本一致。

在人工确认前，不建议跑真实模型指标，也不建议把结果作为正式心理测量结论。

## 当前实现口径

- `trait` 按当前代码的固定顺序派生：`index % 5` 依次对应 `extraversion`、`agreeableness`、`conscientiousness`、`negative_emotionality`、`open_mindedness`。
- `reverse` 暂时全部为 `False`，仅表示尚未人工确认。
- 这不代表量表最终反向键值。确认每题是否反向后，再更新 `src/constant.py` 中的 `Constant.BFI_ITEMS`。
- `scripts/check_bfi_items.py` 只做结构完整性检查和统计输出，不自动判断心理学键值。

## 复核表生成

运行：

```bash
python scripts/export_bfi_review_table.py
```

会生成：

```text
docs/BFI_ITEM_REVIEW_TABLE.md
outputs/bfi_item_review_table.csv
```

生成表格中的 `trait` 和 `reverse` 均原样来自当前代码，`suggested_review_status` 默认为 `待人工确认`，`reviewer_note` 留给人工填写。

## 人工复核建议

1. 确认论文实际使用的是哪一个 BFI 版本或中文修订版本。
2. 对照该版本的正式计分键，逐题确认 `trait` 和 `reverse`。
3. 对确认需要反向计分的题目，将 `Constant.BFI_ITEMS` 对应项的 `reverse` 改为 `True`。
4. 重新运行 `python scripts/check_bfi_items.py`、`python -m pytest` 和完整 mock 流程，确认 OCEAN 输出符合预期。
