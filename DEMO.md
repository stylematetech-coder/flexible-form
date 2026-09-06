# flexible-form 展示手冊（給 Harry）

## 啟動

1. 專案根目錄啟動 Mongo（27017）
2. 執行 `scripts/dev.sh` 或 `python3 scripts/dev.py`
3. 確認 http://localhost:8000/health 回傳 ok

## A. 設計工作室

1. 開啟 http://localhost:5173/
2. 點「示範問卷」（slug: demo）
3. 編輯卡片 → 「儲存」
4. 「預覽」→ 藍框 URL：http://localhost:5175/preview/<token>
5. 「部署上線」→ http://localhost:5175/f/demo
6. 可選：歷史版本「回滾」

## A2. AI 對話（MOCK）

1. 編輯頁右側「AI 對話」
2. 輸入例如：`加一題滿意度評分` → 送出
3. 看到回覆與變更摘要 → 按「套用到草稿」→ 卡片刷新
4. 再試：`刪掉滿意度`、`改標題春季問卷`
5. 未設定 `OPENAI_API_KEY` 時走 MOCK；有 key 則走 OpenAI-compatible API

curl 範例（MOCK）：

```bash
# 取得 schema id
curl -s http://localhost:8000/schemas | python3 -c "import sys,json; print([s['id'] for s in json.load(sys.stdin) if s['slug']=='demo'][0])"

SID=...  # 上一步的 id
curl -s -X POST http://localhost:8000/schemas/$SID/ai/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"加一題滿意度評分"}]}'
```

## B. 填寫端

1. 開啟 http://localhost:5175/f/demo
2. 填姓名、電話 → 「開始填寫」
3. 選「學生」→ 出現「就讀學校名稱」（showIf）
4. 複選主題、評分、建議 → 「提交」→ 成功頁

## C. 驗證 Mongo

在 backend venv 中：`from app.db import get_db; list(get_db().responses.find())`

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
