# 做成在线（别人用链接打开）

本地 `localhost` 只有你能开。要让同学/助教点开链接就能用，需要部署到云端。

## 推荐：Streamlit Community Cloud（免费）

1. 安装 Git，把本项目推到你的 GitHub 仓库  
2. 打开 https://share.streamlit.io 并用 GitHub 登录  
3. New app → 选择仓库 → Main file path 填：`app.py`  
4. 等待构建完成，会得到类似：  
   `https://xxxx.streamlit.app`

依赖会读仓库里的 `requirements.txt`。  
运行时需要的文件：
- `app.py`
- `models/best_model.joblib`
- `data/processed/shanghai_listings.csv`
- `skills/`、`src/`

## 备选：Hugging Face Spaces

1. 新建 Space，SDK 选 Streamlit  
2. 上传本项目代码（或连 GitHub）  
3. 得到 `https://huggingface.co/spaces/你的用户名/空间名`

## 注意
- 不需要 API Key，也没有密钥要藏  
- 数据是历史挂牌，页面已有“仅供参考”提示  
- 仓库请勿提交 `.env`、账号密码  

## 若暂时不上线
按课程要求：交 GitHub/云盘 + README，助教本机运行  
`python -m streamlit run app.py` 也可。
