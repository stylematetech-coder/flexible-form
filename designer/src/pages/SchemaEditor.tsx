import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import StepCard from "../components/StepCard";
import type { FormDefinition, Schema, Step, Version } from "../types";

function uid() {
  return `s_${Math.random().toString(36).slice(2, 10)}`;
}

const emptyStep = (): Step => ({
  id: uid(),
  type: "text",
  title: "新問題",
  required: false,
  options: [],
  showIf: null,
});

type ChatMsg = { role: "user" | "assistant"; content: string };

function summarizeChanges(
  before: FormDefinition | null,
  after: FormDefinition,
  title?: string | null
): string {
  const parts: string[] = [];
  if (title) parts.push(`標題 →「${title}」`);
  const beforeIds = new Set((before?.steps || []).map((s) => s.id));
  const afterIds = new Set(after.steps.map((s) => s.id));
  const added = after.steps.filter((s) => !beforeIds.has(s.id));
  const removed = (before?.steps || []).filter((s) => !afterIds.has(s.id));
  if (added.length) parts.push(`新增 ${added.length} 題：${added.map((s) => s.title).join("、")}`);
  if (removed.length) parts.push(`刪除 ${removed.length} 題：${removed.map((s) => s.title).join("、")}`);
  const beforeCount = before?.steps?.length ?? 0;
  if (!parts.length && after.steps.length !== beforeCount) {
    parts.push(`題數 ${beforeCount} → ${after.steps.length}`);
  }
  if (!parts.length) parts.push("定義有更新");
  return parts.join("；");
}

export default function SchemaEditor() {
  const { id } = useParams<{ id: string }>();
  const [schema, setSchema] = useState<Schema | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [draft, setDraft] = useState<Version | null>(null);
  const [def, setDef] = useState<FormDefinition | null>(null);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [chat, setChat] = useState<ChatMsg[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const [proposed, setProposed] = useState<FormDefinition | null>(null);
  const [proposedTitle, setProposedTitle] = useState<string | null>(null);
  const [changeSummary, setChangeSummary] = useState("");

  const load = async () => {
    if (!id) return;
    setError("");
    try {
      const data = await api.getSchema(id);
      setSchema(data.schema);
      setVersions(data.versions);
      let d =
        data.versions.find((v) => v.status === "draft") ||
        data.versions.find((v) => v.status === "preview") ||
        null;
      if (!d) {
        d = await api.createVersion(id);
        const refreshed = await api.getSchema(id);
        setVersions(refreshed.versions);
      }
      setDraft(d);
      setDef(structuredClone(d.definition));
    } catch (e: unknown) {
      setError(String((e as Error).message || e));
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const publishedHistory = useMemo(
    () => versions.filter((v) => v.status === "published"),
    [versions]
  );

  const fieldOptions = useMemo(
    () =>
      (def?.steps || [])
        .filter((s) => s.type !== "info")
        .map((s) => ({ id: s.id, title: s.title })),
    [def]
  );

  const updateStep = (index: number, step: Step) => {
    if (!def) return;
    const steps = [...def.steps];
    steps[index] = step;
    setDef({ ...def, steps });
  };

  const deleteStep = (index: number) => {
    if (!def) return;
    setDef({ ...def, steps: def.steps.filter((_, i) => i !== index) });
  };

  const moveStep = (index: number, dir: -1 | 1) => {
    if (!def) return;
    const j = index + dir;
    if (j < 0 || j >= def.steps.length) return;
    const steps = [...def.steps];
    [steps[index], steps[j]] = [steps[j], steps[index]];
    setDef({ ...def, steps });
  };

  const save = async () => {
    if (!id || !draft || !def) return;
    setBusy(true);
    setError("");
    setMsg("");
    try {
      const v = await api.patchVersion(id, draft.id, def);
      setDraft(v);
      setMsg("已儲存草稿");
      await load();
    } catch (e: unknown) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const doPreview = async () => {
    if (!id || !draft || !def) return;
    setBusy(true);
    setError("");
    try {
      await api.patchVersion(id, draft.id, def);
      const v = await api.preview(id, draft.id);
      setDraft(v);
      setDef(structuredClone(v.definition));
      const url = `http://localhost:5175/preview/${v.preview_token}`;
      setMsg(`預覽已就緒：${url}`);
      await load();
    } catch (e: unknown) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const doPublish = async () => {
    if (!id || !draft || !def) return;
    if (!confirm("確定部署上線？發布後此版本不可再編輯。")) return;
    setBusy(true);
    setError("");
    try {
      let vid = draft.id;
      if (draft.status === "draft" || draft.status === "preview") {
        await api.patchVersion(id, draft.id, def);
        const v = await api.publish(id, vid);
        setMsg(`已上線！公開網址：http://localhost:5175/f/${schema?.slug}`);
        await api.createVersion(id);
        await load();
      }
    } catch (e: unknown) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const doRollback = async (vid: string) => {
    if (!id) return;
    if (!confirm("確定回滾？將以該版本內容重新發布為新版本。")) return;
    setBusy(true);
    setError("");
    try {
      const v = await api.rollback(id, vid);
      setMsg(`已回滾並發布為 v${v.version}。公開網址：http://localhost:5175/f/${schema?.slug}`);
      await load();
    } catch (e: unknown) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const sendChat = async () => {
    if (!id || !chatInput.trim()) return;
    const userMsg: ChatMsg = { role: "user", content: chatInput.trim() };
    const next = [...chat, userMsg];
    setChat(next);
    setChatInput("");
    setChatBusy(true);
    setError("");
    try {
      const res = await api.aiChat(id, next);
      setChat([...next, { role: "assistant", content: res.reply }]);
      if (res.proposed_definition) {
        setProposed(res.proposed_definition);
        setProposedTitle(res.proposed_schema_title || null);
        setChangeSummary(
          summarizeChanges(def, res.proposed_definition, res.proposed_schema_title)
        );
      } else {
        setProposed(null);
        setProposedTitle(null);
        setChangeSummary("");
      }
    } catch (e: unknown) {
      setError(String((e as Error).message || e));
    } finally {
      setChatBusy(false);
    }
  };

  const applyProposed = async () => {
    if (!id || !proposed) return;
    setBusy(true);
    setError("");
    try {
      await api.aiApply(id, proposed, proposedTitle);
      setMsg("已套用 AI 建議到草稿");
      setProposed(null);
      setProposedTitle(null);
      setChangeSummary("");
      await load();
    } catch (e: unknown) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  if (!schema || !def || !draft) {
    return (
      <div>
        <Link to="/">← 返回</Link>
        {error ? <div className="error">{error}</div> : <p className="muted">載入中…</p>}
      </div>
    );
  }

  return (
    <div>
      <Link to="/">← 返回列表</Link>
      <h1 style={{ marginTop: 12 }}>{schema.title}</h1>
      <p className="muted">
        slug: <code>{schema.slug}</code> · 編輯中：v{draft.version}{" "}
        <span className={`badge ${draft.status}`}>{draft.status}</span>
        {schema.active_version != null && (
          <> · 線上：v{schema.active_version}</>
        )}
      </p>

      <div className="toolbar">
        <button className="btn primary" disabled={busy} onClick={save}>
          儲存
        </button>
        <button className="btn" disabled={busy} onClick={doPreview}>
          預覽
        </button>
        <button className="btn success" disabled={busy} onClick={doPublish}>
          部署上線
        </button>
      </div>

      {msg && <div className="notice">{msg}</div>}
      {error && <div className="error">{error}</div>}

      <div className="editor-layout">
        <div className="editor-main">
          {publishedHistory.length > 0 && (
            <div className="card">
              <h3>歷史版本（回滾）</h3>
              <div className="stack">
                {publishedHistory.map((v) => (
                  <div className="row" key={v.id} style={{ justifyContent: "space-between" }}>
                    <span>
                      v{v.version}{" "}
                      {schema.active_version === v.version && (
                        <span className="badge published">目前線上</span>
                      )}
                    </span>
                    <button
                      className="btn"
                      disabled={busy || schema.active_version === v.version}
                      onClick={() => doRollback(v.id)}
                    >
                      回滾
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="row" style={{ justifyContent: "space-between", margin: "16px 0" }}>
            <h2>題目卡片</h2>
            <button
              className="btn primary"
              onClick={() => setDef({ ...def, steps: [...def.steps, emptyStep()] })}
            >
              ＋ 新增題目
            </button>
          </div>

          {def.steps.length === 0 && <p className="muted">尚無題目，請新增</p>}
          {def.steps.map((step, i) => (
            <StepCard
              key={step.id}
              step={step}
              index={i}
              total={def.steps.length}
              fieldOptions={fieldOptions.filter((f) => f.id !== step.id)}
              onChange={(s) => updateStep(i, s)}
              onDelete={() => deleteStep(i)}
              onMove={(dir) => moveStep(i, dir)}
            />
          ))}
        </div>

        <aside className="ai-panel card">
          <h3>AI 對話</h3>
          <p className="muted" style={{ marginBottom: 8 }}>
            可用中文指令調整草稿，例如「加一題滿意度」、「刪掉就讀學校」、「改標題春季問卷」。
            未設定 OPENAI_API_KEY 時使用內建 MOCK。
          </p>
          <div className="ai-messages">
            {chat.length === 0 && (
              <p className="muted">尚無對話，輸入指令開始。</p>
            )}
            {chat.map((m, i) => (
              <div key={i} className={`ai-bubble ${m.role}`}>
                <div className="ai-role">{m.role === "user" ? "你" : "AI"}</div>
                <div>{m.content}</div>
              </div>
            ))}
          </div>
          {proposed && (
            <div className="ai-propose">
              <div className="muted" style={{ marginBottom: 8 }}>
                變更摘要：{changeSummary || "有建議定義"}
              </div>
              <button className="btn success" disabled={busy} onClick={applyProposed}>
                套用到草稿
              </button>
            </div>
          )}
          <div className="ai-input row" style={{ marginTop: 10 }}>
            <input
              value={chatInput}
              placeholder="輸入中文指令…"
              disabled={chatBusy}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendChat();
                }
              }}
            />
            <button className="btn primary" disabled={chatBusy || !chatInput.trim()} onClick={sendChat}>
              送出
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
