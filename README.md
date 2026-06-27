# LeaveIQ Backend

FastAPI backend for LeaveIQ.

## Environment

Copy `.env.example` to `.env` for local development. Do not commit `.env`.

Required production variables include database, JWT, mail, Groq/OpenRouter, Pinecone, and `CORS_ORIGINS`.

Set `CORS_ORIGINS` to the Vercel frontend URL:

```text
CORS_ORIGINS=https://leaveiq-frontend.vercel.app
```

## Local

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Render

Import `https://github.com/sabari7251/leaveiq-backend` in Render or use `render.yaml`.

Settings:

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add all variables from `.env.example` in Render Environment.

If Render logs show `Running 'uvicorn main:app --reload'`, update the service's Start Command in the Render dashboard to:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Policy uploads are saved under `UPLOAD_DIR` and indexed into Pinecone using `rag/new_ingest.py` and `rag/new_retriever.py`; Chroma DB files are not required for production.
