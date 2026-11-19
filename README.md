# 沪租估 · 上海租房公允估价与筛选 Agent

机器学习期末项目：用 Linear / Ridge / Lasso 预测上海整租公允月租，并做成可交互的找房助手。

在线演示：https://shanghai-rent-agent-2q76xragwmybw27uqinqt7.streamlit.app/

## 怎么跑

```powershell
cd rent-agent
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

一键复现训练与评估：

```powershell
python run_all.py
```

## 项目结构

- `app.py`：网页入口
- `src/agent_core.py`：任务编排
- `skills/rent_filter_skill.py`：筛选 + 估价建议
- `src/preprocess.py` / `train.py` / `evaluate.py`：数据与模型
- `tests/`：可复现样例
- `docs/`：说明与报告材料
- `data/DATA_SOURCE.md`：数据来源

## 结果摘要

见 `results/train_report.json`：当前默认模型为 Lasso，测试集 MAE 约 2243，优于单价基线约 2969。样例测试见 `results/sample_test_report.json`。

## 部署

见 `DEPLOY.md`。仓库已部署到 Streamlit Cloud，入口文件为 `app.py`。
