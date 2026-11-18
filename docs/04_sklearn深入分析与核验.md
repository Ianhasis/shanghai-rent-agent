# 深入分析：scikit-learn 回归 Pipeline（课程第三节必选项）

## 1. 它解决什么子任务
将上海房源特征映射为**月租金预测值**，供 Agent 判断挂牌价是否偏贵/合理，并参与排序。

## 2. 输入 / 输出
- **输入 X**：`area, rooms, halls, has_metro, lng, lat` + `orient, district`（One-Hot）
- **输入 y**：挂牌月租 `price`
- **输出**：连续租金预测；模型系数用于特征影响分析

## 3. 依赖与权限
- 仅本地 CPU 推理/训练
- **无**外部付费 API、**无**系统管理员权限、**无**密钥
- 依赖包：`scikit-learn==1.6.0`（BSD-3-Clause）

## 4. 限制
- 线性假设，非线性溢价（豪宅、特殊装修）拟合不足
- 行政区由文本/GPS 近似，存在错分风险
- 历史挂牌 ≠ 当前成交价
- 系数是相关关系，不能直接当因果

## 5. 我们如何阅读并核验
1. 阅读 sklearn 文档中 `Pipeline` / `Ridge` / `Lasso` / `OneHotEncoder` 用法  
2. 固定 `random_state=42`，划分 train/valid/test  
3. 在 valid 上选模型，在 test 上报告 MAE/RMSE/R2/MAPE  
4. 与基线「租类型中位单价 × 面积」对照  
5. 检查面积系数符号为正（见 `results/feature_influence_*.csv`）  
6. 用消融：关闭模型后 Agent 无法给出公允价建议  

## 6. 核验结果（本机已跑）
见 `results/train_report.json`：
- 选用模型：Lasso（valid MAE 最优）
- Test MAE ≈ 2243；Baseline MAE ≈ 2969（模型优于基线）
- Test R² ≈ 0.695

## 7. 集成中的适配工作（我们写的部分）
- 自研特征工程与行政区推断（`src/preprocess.py`）
- Pipeline：`StandardScaler` + `OneHotEncoder(handle_unknown='ignore')`
- 将预测接入 `RentFilterSkill` 的筛选/建议/人工复核阈值
- 增加输入校验、无匹配处理、消融开关
- 补充测试样例 `tests/sample_queries.json`
