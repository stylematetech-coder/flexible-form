import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Schema } from "../types";

export default function SchemaList() {
  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
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
      {!loading && schemas.length === 0 && <p className="muted">尚無問卷</p>}
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
