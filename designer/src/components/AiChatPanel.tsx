import type { FormDefinition } from "../types";

export type ChatMsg = { role: "user" | "assistant"; content: string };

export interface AiChatPanelProps {
  chat: ChatMsg[];
  chatInput: string;
  chatBusy: boolean;
  busy: boolean;
  proposed: FormDefinition | null;
  changeSummary: string;
  onChatInputChange: (value: string) => void;
  onSend: () => void;
  onApply: () => void;
}

export default function AiChatPanel({
  chat,
  chatInput,
  chatBusy,
  busy,
  proposed,
  changeSummary,
  onChatInputChange,
  onSend,
  onApply,
}: AiChatPanelProps) {
  return (
    <aside className="ai-panel card">
      <h3>AI 對話</h3>
      <p className="muted" style={{ marginBottom: 8 }}>
        可用中文指令調整草稿，例如「加一題滿意度」、「刪掉就讀學校」、「改標題春季問卷」。
        也可從零口述：「幫我做一份顧客滿意度問卷」。未設定 OPENAI_API_KEY 時使用內建 MOCK。
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
          <button className="btn success" disabled={busy} onClick={onApply}>
            套用到草稿
          </button>
        </div>
      )}
      <div className="ai-input row" style={{ marginTop: 10 }}>
        <input
          value={chatInput}
          placeholder="輸入中文指令…"
          disabled={chatBusy}
          onChange={(e) => onChatInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
        />
        <button className="btn primary" disabled={chatBusy || !chatInput.trim()} onClick={onSend}>
          送出
        </button>
      </div>
    </aside>
  );
}
