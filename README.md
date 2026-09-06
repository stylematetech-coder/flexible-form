# flexible-form（問卷微服務 Demo）

獨立問卷微服務：設計工作室（Designer）+ 填寫端（Runtime）+ FastAPI / MongoDB 後端。支援 **AI 對話改稿**（zh-TW：Ollama Cloud 優先，其次 OpenAI，否則 MOCK）。

## 架構

| 服務 | 路徑 | 埠 | 說明 |
|------|------|----|------|
| MongoDB | compose | **27017** | 資料庫 |
| Backend | backend/ | **8000** | FastAPI API |
| Designer | designer/ | **5173** | 問卷設計工作室（zh-TW）+ AI 對話 |
| Runtime | runtime/ | **5175** | 填寫端（zh-TW） |

Designer / Runtime 透過 Vite proxy 將 /api 轉到 http://127.0.0.1:8000。

## 快速開始

1. 專案根目錄啟動 Mongo（埠 27017）
2. 執行 `scripts/dev.sh`（或 `make` 的 `dev` 目標）
3. 開啟 Designer http://localhost:5173/ 與 Runtime http://localhost:5175/f/demo
4. 健康檢查 http://localhost:8000/health

`dev.sh` 會建立 Python venv、安裝前後端依賴、啟動 API 與兩個 SPA，並 seed demo。

手動方式：backend 用 venv + uvicorn 埠 8000；designer 埠 5173；runtime 埠 5175。

## AI 對話改稿

編輯頁右側有 **AI 對話** 面板。優先順序：

1. **`OLLAMA_API_KEY`（推薦）**：呼叫 [Ollama Cloud](https://ollama.com) `POST /api/chat`（原生 `format: "json"`），依目前 definition + 對話回傳 JSON 定義更新。
   - 建立 API key：https://ollama.com/settings/keys
   - 匯出：`export OLLAMA_API_KEY=...`（或寫入 `backend/.env`）
   - 可選：`OLLAMA_BASE_URL`（預設 `https://ollama.com`）、`OLLAMA_MODEL`（預設 `gpt-oss:20b`）
   - 測試可用免費 starter 模型／`gpt-oss:20b`
2. **`OPENAI_API_KEY`（備援）**：OpenAI-compatible chat。
   - 可選：`OPENAI_BASE_URL`（預設 `https://api.openai.com/v1`）、`OPENAI_MODEL`（預設 `gpt-4o-mini`）
3. **皆未設定**：內建 **MOCK**，可解析簡單中文意圖，例如：
   - 「加一題滿意度評分」→ 新增題目
   - 「刪掉就讀學校」→ 依標題/id 子字串刪題
   - 「改標題春季問卷」→ 更新 schema 標題（套用時寫入）

Ollama / OpenAI 呼叫失敗時會回退 MOCK，並在回覆前綴錯誤說明。

AI 回傳 `proposed_definition` 時，UI 顯示變更摘要與「套用到草稿」；套用會寫入目前 DRAFT（若無則自動建立）。

API：

- `POST /schemas/{id}/ai/chat` body `{ messages: [{role, content}] }` → `{ reply, proposed_definition, proposed_schema_title? }`
- `POST /schemas/{id}/ai/apply` body `{ definition, schema_title? }` → 更新 draft version

## 點擊路徑

1. Designer 列表點示範問卷（slug demo）
2. 編輯題目卡片，或用 AI 對話 → 「套用到草稿」→ 「儲存」「預覽」「部署上線」
3. Runtime 開啟 /f/demo 填寫並提交
4. 詳見 DEMO.md

## API 摘要

- GET /health
- POST/GET /schemas, GET /schemas/{id}
- POST /schemas/{id}/versions, PATCH draft versions
- POST preview / publish / rollback
- POST /schemas/{id}/ai/chat, POST /schemas/{id}/ai/apply
- GET /public/forms/{slug}, GET /public/preview/{token}
- POST/PATCH responses, POST submit

Swagger: http://localhost:8000/docs

## 資料模型

schemas / schema_versions / responses（字串 id）。已發布版本不可變；回滾=重發舊 definition。

## 環境變數（backend/.env）

```
MONGO_URI=mongodb://localhost:27017
MONGO_DB=form_service
CORS_ORIGINS=*
# 推薦 AI（Ollama Cloud）：
# OLLAMA_API_KEY=          # https://ollama.com/settings/keys
# OLLAMA_BASE_URL=https://ollama.com
# OLLAMA_MODEL=gpt-oss:20b
# 備援 AI（OpenAI-compatible）：
# OPENAI_API_KEY=
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o-mini
```

## 備註（本機無 Docker 時）

若環境沒有 Docker，`scripts/dev.py` 會改用 `.tools` 下的 mongod 二進位，資料目錄 `/tmp/form-service-mongo`。有 Docker 時仍用 compose 的 27017。
