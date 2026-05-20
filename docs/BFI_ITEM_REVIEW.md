# BFI Item Metadata Review

本文档记录 `Constant.BFI_ITEMS` 的维度归属、反向计分标记和人工复核状态。

## 复核结论

当前题干、`trait` 和 `reverse` 已按官方中文 BFI-2 self-report form and scoring key 复核并落入代码。

权威来源：

- Colby Personality Lab: <https://www.colby.edu/academics/departments-and-programs/psychology/research-opportunities/personality-lab/the-bfi-2/>
- Chinese BFI-2 self-report form and scoring key: <https://www.colby.edu/wp-content/uploads/2020/05/bfi2-form-chinese.pdf>
- BFI-2 item list by domain and facet: <https://www.colby.edu/wp-content/uploads/2013/08/bfi2-item-list.pdf>
- SPSS scoring syntax: <https://www.personalitylab.org/storage/bfi2-syntax.sps>

复核后的结构：

- 共 60 题。
- 每个大五维度 12 题。
- 共 30 道反向计分题。
- 维度命名沿用 BFI-2 口径：`extraversion`、`agreeableness`、`conscientiousness`、`negative_emotionality`、`open_mindedness`。

## 当前实现口径

- `trait` 按当前代码的固定顺序派生：`index % 5` 依次对应 `extraversion`、`agreeableness`、`conscientiousness`、`negative_emotionality`、`open_mindedness`。
- `reverse` 按官方中文 BFI-2 计分键设置，反向计分机制仍为 `score = 6 - score`。
- `scripts/check_bfi_items.py` 会检查 60 题完整性、每维 12 题、30 道反向题和字段类型。
- 如果后续确认论文使用的不是 BFI-2，而是 BFI-44、NEO-FFI 或自定义中文改编版，需要重新复核，不能直接套用当前键值。

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

生成表格中的 `trait` 和 `reverse` 均原样来自当前代码，`suggested_review_status` 标记为 `已按官方中文 BFI-2 计分键确认`。

## 后续使用建议

1. 阶段 8 真实模型/API 推理可以按技术联调口径继续推进。
2. 若要把输出作为正式心理测量结论，仍需确认论文数据与本仓库题干使用的是同一个 BFI-2 中文版本。
3. 每次修改题干、维度或反向计分后，都应重新运行 `python scripts/check_bfi_items.py`、`python -m pytest` 和完整 mock 流程。
