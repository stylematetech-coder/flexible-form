import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import AiChatPanel, { type ChatMsg } from "../components/AiChatPanel";
import DeployBar from "../components/DeployBar";
import StepsEditor from "../components/StepsEditor";
import type { FormDefinition, Schema, Version } from "../types";

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

      <DeployBar
        schema={schema}
        draft={draft}
        publishedHistory={publishedHistory}
        busy={busy}
        msg={msg}
        error={error}
        onSave={save}
        onPreview={doPreview}
        onPublish={doPublish}
        onRollback={doRollback}
      />

      <div className="editor-layout">
        <div className="editor-main">
          <StepsEditor def={def} onChange={setDef} />
        </div>

        <AiChatPanel
          chat={chat}
          chatInput={chatInput}
          chatBusy={chatBusy}
          busy={busy}
          proposed={proposed}
          changeSummary={changeSummary}
          onChatInputChange={setChatInput}
          onSend={sendChat}
          onApply={applyProposed}
        />
      </div>
    </div>
  );
}
