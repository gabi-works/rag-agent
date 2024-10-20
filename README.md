# 🔍💬 Knowledge Navigator Agent

This repository implements an agent that downloads documents from provided links, constructs a Retrieval-Augmented Generation (RAG) system, and uses it to answer user queries. The project is built using LangGraph, FastAPI, and Streamlit.

## Quickstart
Run with docker
```
echo 'OPENAI_API_KEY=your-key' >> .env
docker compose watch
```
Run directly in python
```
echo 'OPENAI_API_KEY=your-key' >> .env

pip install uv
uv sync --frozon
# "uv sync" creates .venv automatically

source .venv/bin/activate
python service/run_server.py

# In another shell
source .venv/bin/activate
streamlit run service/run_streamlit.py
```

## Key Features
1. LangGraph 
2. FastAPI for REST API
3. Streamlit for UI
4. Docker Support