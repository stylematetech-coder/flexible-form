import type { Schema, Version } from "../types";

export interface DeployBarProps {
  schema: Schema;
  draft: Version;
  publishedHistory: Version[];
  busy: boolean;
  msg: string;
  error: string;
  onSave: () => void;
  onPreview: () => void;
  onPublish: () => void;
  onRollback: (vid: string) => void;
}

export default function DeployBar({
  schema,
  draft,
  publishedHistory,
  busy,
  msg,
  error,
  onSave,
  onPreview,
  onPublish,
  onRollback,
}: DeployBarProps) {
  return (
    <>
      <div className="toolbar">
        <button className="btn primary" disabled={busy} onClick={onSave}>
          儲存
        </button>
        <button className="btn" disabled={busy} onClick={onPreview}>
          預覽
        </button>
        <button className="btn success" disabled={busy} onClick={onPublish}>
          部署上線
        </button>
      </div>

      {msg && <div className="notice">{msg}</div>}
      {error && <div className="error">{error}</div>}

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
                  onClick={() => onRollback(v.id)}
                >
                  回滾
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
