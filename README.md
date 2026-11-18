# 上海租房公允估价与筛选 Agent

课程：《机器学习》期末项目（租金预测 + Agent）

## 文档要求对照

| 要求 | 本项目落点 |
|------|------------|
| 任务入口 | 网页 `app.py` / CLI `src/agent.py`：输入预算区域面积，输出建议与复核 |
| 任务流程 | `src/agent_core.py` 七步状态机，页面逐步展示作用 |
| 机器学习组件 | Linear/Ridge/Lasso 回归，`models/best_model.joblib` |
| 工具或数据连接 | 本地上海链家房源库 `data/processed/shanghai_listings.csv` |
| 失败与安全 | 输入校验、无匹配、高偏差人工复核 |
| 可复现交付 | `requirements.txt`、`tests/sample_queries.json`、`run_all.py` |
| 开源 skills | sklearn 深入分析 + 自研 `rent_filter_skill` + 消融 |

## 推荐运行（网页）
```powershell
cd d:\FP\rent-agent
python -m streamlit run app.py
```
打开 http://localhost:8501  

> 别人默认打不开你的 localhost。  
> 要做成在线链接：见 `DEPLOY.md`（Streamlit Cloud / Hugging Face Spaces）。  
> 也可交代码+README，助教本机运行。

## 一键复现
```powershell
cd d:\FP\rent-agent
python -m pip install -r requirements.txt
python run_all.py
```

## 目录
- `app.py` 网页 Agent  
- `src/agent_core.py` 编排与成功判定  
- `skills/rent_filter_skill.py` 筛选建议 skill  
- `src/preprocess.py` / `train.py` / `evaluate.py`  
- `tests/` 可复现样例  
- `docs/` 项目定义、复用清单、sklearn 核验、报告草稿  
- `data/DATA_SOURCE.md` 数据来源与边界  

## 关键结果（摘要）
见 `results/train_report.json`：Lasso 测试 MAE 约 2243，优于基线约 2969；样例测试见 `results/sample_test_report.json`。
