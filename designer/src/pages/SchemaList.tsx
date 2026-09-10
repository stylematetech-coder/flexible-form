import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { getOwnerToken, setOwnerToken } from "../api/owner";
import type { Schema } from "../types";

export default function SchemaList() {
  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [ownerToken, setOwnerTokenState] = useState(() => getOwnerToken());
  const nav = useNavigate();

  const load = () => {
    setLoading(true);
    api
      .listSchemas()
      .then(setSchemas)
      .catch((e) => setError(String(e.message || e)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const applyOwnerToken = () => {
    setOwnerToken(ownerToken);
    setOwnerTokenState(getOwnerToken());
    setError("");
    load();
  };

  const create = async () => {
    setError("");
    if (!title.trim() || !slug.trim()) {
      setError("請填寫標題與 slug");
      return;
    }
    try {
      const s = await api.createSchema(title.trim(), slug.trim());
      nav(`/schemas/${s.id}`);
    } catch (e: unknown) {
      setError(String((e as Error).message || e));
    }
  };

  return (
    <div>
      <h1>問卷列表</h1>
      <p className="muted">建立與編輯問卷 schema（卡片式，無 JSON）</p>

      <div className="card stack" style={{ marginTop: 16 }}>
        <h3>Owner Token（多租戶示範）</h3>
        <p className="muted" style={{ margin: 0 }}>
          以 Bearer token 隔離問卷列表。預設 <code>dev-token</code>；seed 示範問卷屬{" "}
          <code>anonymous</code>。切換 token 可模擬不同 APP 業主。
        </p>
        <label>目前 owner token</label>
        <div className="row">
          <input
            style={{ flex: 1 }}
            value={ownerToken}
            onChange={(e) => setOwnerTokenState(e.target.value)}
            placeholder="例如：dev-token / anonymous / alice"
            onKeyDown={(e) => {
              if (e.key === "Enter") applyOwnerToken();
            }}
          />
          <button className="btn primary" onClick={applyOwnerToken}>
            套用並重新載入
          </button>
        </div>
      </div>

      <div className="card stack" style={{ marginTop: 16 }}>
        <h3>新增問卷</h3>
        <label>標題</label>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="例如：滿意度調查" />
        <label>Slug（公開網址用）</label>
        <input value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="例如：satisfaction" />
        {error && <div className="error">{error}</div>}
        <button className="btn primary" onClick={create}>
          建立
        </button>
      </div>

      <h2 style={{ marginTop: 28 }}>已有問卷</h2>
      {loading && <p className="muted">載入中…</p>}
      {!loading && schemas.length === 0 && (
        <p className="muted">
          尚無問卷（目前 token：<code>{getOwnerToken()}</code>）。可改為{" "}
          <code>anonymous</code> 查看 seed，或新建一份。
        </p>
      )}
      {schemas.map((s) => (
        <Link key={s.id} to={`/schemas/${s.id}`} className="card schema-item">
          <div>
            <strong>{s.title}</strong>
            <div className="muted">
              /{s.slug} · v{s.active_version ?? "—"}
            </div>
          </div>
          <span className={`badge ${s.status}`}>{s.status}</span>
        </Link>
      ))}
    </div>
  );
}
