# scikit-learn 回归 Pipeline 说明与核验

## 解决的问题

根据房源特征预测月租金，供 Agent 判断挂牌价是否偏贵，并参与排序。

## 输入输出

- 输入：`area, rooms, halls, has_metro, lng, lat`，以及 `orient, district`（独热编码）
- 目标：挂牌月租 `price`
- 输出：预测租金；系数用于看特征影响

## 依赖

- 本地训练与推理，不调用外部付费 API
- `scikit-learn==1.6.0`（BSD-3-Clause）

## 限制

- 线性模型，对特殊溢价拟合有限
- 行政区由文本/坐标近似，可能有误差
- 挂牌价不等于成交价
- 系数表示相关，不代表因果

## 核验做法

1. 按官方文档搭 Pipeline（标准化 + 独热 + 回归）
2. `random_state=42`，划分 train / valid / test
3. 在验证集上选模型，在测试集上报告 MAE、RMSE、R²、MAPE
4. 与基线「租类型中位单价 × 面积」对比
5. 检查面积系数方向是否合理（见 `results/feature_influence_*.csv`）
6. 关闭模型做消融，确认建议能力依赖回归组件

## 结果摘要

见 `results/train_report.json`：

- 选用：Lasso
- 测试集 MAE ≈ 2243；基线 MAE ≈ 2969
- 测试集 R² ≈ 0.695

## 自己做的适配

- 数据清洗与行政区推断：`src/preprocess.py`
- Pipeline 参数与训练脚本：`src/train.py`
- 预测接入筛选与建议：`skills/rent_filter_skill.py`
- 输入校验、无匹配处理、消融开关
- 测试样例：`tests/sample_queries.json`
