# 部署说明

本地 `localhost` 只有本机可访问。要让别人点开链接使用，需要部署到云端。

## Streamlit Community Cloud

1. 代码推到 GitHub
2. 打开 https://share.streamlit.io ，用 GitHub 登录
3. New app → 选仓库 → Main file path 填 `app.py`
4. 部署完成后得到 `https://xxxx.streamlit.app`

依赖读取 `requirements.txt`。运行时需要：

- `app.py`
- `models/best_model.joblib`
- `data/processed/shanghai_listings.csv`
- `skills/`、`src/`

本项目当前在线地址：

https://shanghai-rent-agent-2q76xragwmybw27uqinqt7.streamlit.app/

## 备选：Hugging Face Spaces

新建 Space，SDK 选 Streamlit，连 GitHub 或上传代码即可。

## 注意

- 无 API Key，仓库不要提交 `.env`
- 数据是历史挂牌，页面已提示仅供参考
