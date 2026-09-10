# flexible-form（問卷微服務 Demo）

獨立問卷微服務：設計工作室（Designer）+ 填寫端（Runtime）+ FastAPI / MongoDB 後端。支援 **AI 對話改稿**（zh-TW：Ollama Cloud 優先，其次 OpenAI，否則 MOCK）與簡易 **Owner Bearer 隔離**（APP 準備）。

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

## Owner 隔離（簡易 Bearer）

Designer / schema 變更與列表 API 依 **owner** 過濾：

- Header：`Authorization: Bearer <token>` **或** `X-Owner-Id: <id>`
- `owner_id` = token 字串本身（demo 不做 JWT 驗證）
- **未帶 header 時**後端退回 `owner_id=anonymous`（僅方便本機 curl；**APP 應一律送 token**）
- Seed 示範問卷 `slug=demo` 的 `owner_id=anonymous`
- Designer 預設讀 `localStorage.ff_owner_token` 或 `?token=`，否則 `dev-token`，並以 Bearer 呼叫 API
- 列表頁可編輯目前 owner token，切換後重新載入即可示範多業主隔離
- **公開填寫** `/public/*` 不需 owner（Runtime 維持公開）
- 跨 owner 存取回 403

範例：

```bash
# 看不到 anonymous 的 demo（因為 token 不同）
curl -s -H 'Authorization: Bearer alice' http://localhost:8000/schemas

# 看到 seed demo
curl -s -H 'Authorization: Bearer anonymous' http://localhost:8000/schemas
# 或省略 header → anonymous
curl -s http://localhost:8000/schemas
```

## AI 對話改稿

編輯頁右側有 **AI 對話** 面板（元件：`AiChatPanel`）。優先順序：

1. **`OLLAMA_API_KEY`（推薦）**：呼叫 [Ollama Cloud](https://ollama.com) `POST /api/chat`（原生 `format: "json"`），依目前 definition + 對話回傳 JSON 定義更新。
   - 建立 API key：https://ollama.com/settings/keys
   - 匯出：`export OLLAMA_API_KEY=...`（或寫入 `backend/.env`）
   - 可選：`OLLAMA_BASE_URL`（預設 `https://ollama.com`）、`OLLAMA_MODEL`（預設 `gpt-oss:20b`）
2. **`OPENAI_API_KEY`（備援）**：OpenAI-compatible chat。
3. **皆未設定**：內建 **MOCK**，可解析：
   - **從零口述**：「幫我做一份顧客滿意度問卷，含評分與建議」→ 產生 4–8 題完整定義
   - 「加一題滿意度評分」→ 新增題目
   - 「刪掉就讀學校」→ 依標題/id 子字串刪題
   - 「改標題春季問卷」→ 更新 schema 標題（套用時寫入）

草稿 `steps` 為空時，MOCK / system prompt 會偏向完整生成。

Ollama / OpenAI 呼叫失敗時會回退 MOCK，並在回覆前綴錯誤說明。

AI 回傳 `proposed_definition` 時，UI 顯示變更摘要與「套用到草稿」；套用會寫入目前 DRAFT（若無則自動建立）。

API：

- `POST /schemas/{id}/ai/chat` body `{ messages: [{role, content}] }` → `{ reply, proposed_definition, proposed_schema_title? }`
- `POST /schemas/{id}/ai/apply` body `{ definition, schema_title? }` → 更新 draft version

## Designer 元件拆分

`SchemaEditor` 頁面保持精簡，面板拆到：

- `components/AiChatPanel.tsx` — 對話、建議摘要、套用
- `components/StepsEditor.tsx` — 題目卡片列表與增刪排序
- `components/DeployBar.tsx` — 儲存／預覽／部署／回滾與狀態訊息

## 點擊路徑

1. Designer 列表：必要時把 owner token 改成 `anonymous` 以看到 seed demo，或用 `dev-token` 新建
2. 編輯題目卡片，或用 AI 從零口述 → 「套用到草稿」→ 「儲存」「預覽」「部署上線」
3. Runtime 開啟 /f/demo 填寫並提交
4. 詳見 DEMO.md

## API 摘要

- GET /health
- POST/GET /schemas, GET /schemas/{id}（需 owner；列表依 owner_id 過濾）
- POST /schemas/{id}/versions, PATCH draft versions
- POST preview / publish / rollback
- POST /schemas/{id}/ai/chat, POST /schemas/{id}/ai/apply
- GET /public/forms/{slug}, GET /public/preview/{token}（公開）
- POST/PATCH responses, POST submit（公開）

Swagger: http://localhost:8000/docs

## 資料模型

schemas（含 `owner_id`）/ schema_versions / responses（字串 id）。已發布版本不可變；回滾=重發舊 definition。

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
