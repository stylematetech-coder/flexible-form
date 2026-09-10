# flexible-form 展示手冊（給 Harry）

## 啟動

1. 專案根目錄啟動 Mongo（27017）
2. 執行 `scripts/dev.sh` 或 `python3 scripts/dev.py`
3. 確認 http://localhost:8000/health 回傳 ok
4. `git pull` 後若已在跑服務，重啟一次 backend／designer

## A. 設計工作室

1. 開啟 http://localhost:5173/
2. 列表上方可編輯 **Owner Token**（預設 `dev-token`）
   - 改成 `anonymous` → 「套用並重新載入」可看到 seed「示範問卷」
   - 用兩個 token（例如 `alice` / `bob`）各自新建問卷，可驗證列表互不可見
3. 點問卷進入編輯：題目卡片（StepsEditor）+ 右側 AI + 上方 DeployBar
4. 「儲存」→「預覽」→「部署上線」→ http://localhost:5175/f/<slug>
5. 可選：歷史版本「回滾」

## A2. AI 對話（從零口述 + MOCK）

1. 建議：用 `dev-token` **新建空白問卷**，進入編輯（steps 為空）
2. 右側 AI 輸入：`幫我做一份顧客滿意度問卷，含評分與建議` → 送出
3. 應看到多題建議定義與變更摘要 → 「套用到草稿」
4. 也可增量：`加一題滿意度評分`、`刪掉…`、`改標題…`
5. AI 優先：`OLLAMA_API_KEY` → `OPENAI_API_KEY` → MOCK

curl 範例（MOCK + owner）：

```bash
# 以 anonymous 看 seed
curl -s -H 'Authorization: Bearer anonymous' http://localhost:8000/schemas

SID=...  # demo 的 id，或先 POST 建立空白 schema
curl -s -X POST http://localhost:8000/schemas/$SID/ai/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer anonymous' \
  -d '{"messages":[{"role":"user","content":"幫我做一份顧客滿意度問卷，含評分與建議"}]}'
```

多 owner 驗證：

```bash
curl -s -X POST http://localhost:8000/schemas \
  -H 'Authorization: Bearer alice' -H 'Content-Type: application/json' \
  -d '{"title":"Alice 問卷","slug":"alice-form"}'
curl -s -H 'Authorization: Bearer bob' http://localhost:8000/schemas
# bob 不應看到 alice-form
```

## B. 填寫端（公開，不需 token）

1. 開啟 http://localhost:5175/f/demo
2. 填姓名、電話 → 「開始填寫」
3. 選「學生」→ 出現「就讀學校名稱」（showIf）
4. 複選主題、評分、建議 → 「提交」→ 成功頁

## C. 驗證 Mongo

在 backend venv 中：`from app.db import get_db; list(get_db().schemas.find({}, {"title":1,"owner_id":1,"slug":1}))`

## 埠一覽

| 用途 | URL |
|------|-----|
| Designer | http://localhost:5173/ |
| Runtime demo | http://localhost:5175/f/demo |
| API health | http://localhost:8000/health |
| API docs | http://localhost:8000/docs |
| Mongo | localhost:27017 |

## 目前環境狀態

此 box 無 Docker 時，Mongo 以 `.tools` 內 mongod 跑在 `/tmp/form-service-mongo:27017`。
API/Designer/Runtime 重啟請用：`python3 scripts/dev.py`
