import type { Step, StepType, ShowIfOp } from "../types";

const TYPE_LABELS: Record<StepType, string> = {
  single: "單選",
  multi: "複選",
  text: "短文字",
  textarea: "長文字",
  number: "數字",
  info: "說明",
};

interface Props {
  step: Step;
  index: number;
  total: number;
  fieldOptions: { id: string; title: string }[];
  onChange: (step: Step) => void;
  onDelete: () => void;
  onMove: (dir: -1 | 1) => void;
}

export default function StepCard({
  step,
  index,
  total,
  fieldOptions,
  onChange,
  onDelete,
  onMove,
}: Props) {
  const needsOptions = step.type === "single" || step.type === "multi";

  const set = (patch: Partial<Step>) => onChange({ ...step, ...patch });

  const updateOption = (i: number, key: "value" | "label", val: string) => {
    const options = step.options.map((o, idx) =>
      idx === i ? { ...o, [key]: val } : o
    );
    set({ options });
  };

  const addOption = () => {
    const n = step.options.length + 1;
    set({ options: [...step.options, { value: `opt_${n}`, label: `選項 ${n}` }] });
  };

  const removeOption = (i: number) => {
    set({ options: step.options.filter((_, idx) => idx !== i) });
  };

  return (
    <div className="card step-card stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <span className="handle">
          步驟 {index + 1} · {TYPE_LABELS[step.type]}
        </span>
        <div className="row">
          <button className="btn" disabled={index === 0} onClick={() => onMove(-1)}>
            ↑
          </button>
          <button className="btn" disabled={index === total - 1} onClick={() => onMove(1)}>
            ↓
          </button>
          <button className="btn danger" onClick={onDelete}>
            刪除
          </button>
        </div>
      </div>

      <label>題型</label>
      <select
        value={step.type}
        onChange={(e) => {
          const type = e.target.value as StepType;
          set({
            type,
            options:
              type === "single" || type === "multi"
                ? step.options.length
                  ? step.options
                  : [
                      { value: "a", label: "選項 A" },
                      { value: "b", label: "選項 B" },
                    ]
                : [],
          });
        }}
      >
        {(Object.keys(TYPE_LABELS) as StepType[]).map((t) => (
          <option key={t} value={t}>
            {TYPE_LABELS[t]}
          </option>
        ))}
      </select>

      <label>題目 / 內容</label>
      <input value={step.title} onChange={(e) => set({ title: e.target.value })} />

      {step.type !== "info" && (
        <label className="row">
          <input
            type="checkbox"
            checked={step.required}
            onChange={(e) => set({ required: e.target.checked })}
            style={{ width: "auto" }}
          />
          必填
        </label>
      )}

      {needsOptions && (
        <div className="stack">
          <label>選項</label>
          {step.options.map((o, i) => (
            <div className="row" key={i}>
              <input
                style={{ flex: 1 }}
                value={o.label}
                placeholder="顯示文字"
                onChange={(e) => updateOption(i, "label", e.target.value)}
              />
              <input
                style={{ flex: 1 }}
                value={o.value}
                placeholder="值"
                onChange={(e) => updateOption(i, "value", e.target.value)}
              />
              <button className="btn" onClick={() => removeOption(i)}>
                ×
              </button>
            </div>
          ))}
          <button className="btn" onClick={addOption}>
            ＋ 新增選項
          </button>
        </div>
      )}

      <div className="stack">
        <label>條件顯示（showIf）</label>
        <select
          value={step.showIf ? "on" : "off"}
          onChange={(e) => {
            if (e.target.value === "off") set({ showIf: null });
            else
              set({
                showIf: {
                  field: fieldOptions[0]?.id || "",
                  op: "eq",
                  value: "",
                },
              });
          }}
        >
          <option value="off">永遠顯示</option>
          <option value="on">依條件顯示</option>
        </select>
        {step.showIf && (
          <div className="row">
            <select
              style={{ flex: 2 }}
              value={step.showIf.field}
              onChange={(e) =>
                set({ showIf: { ...step.showIf!, field: e.target.value } })
              }
            >
              {fieldOptions.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.title || f.id}
                </option>
              ))}
            </select>
            <select
              style={{ flex: 1 }}
              value={step.showIf.op}
              onChange={(e) =>
                set({
                  showIf: { ...step.showIf!, op: e.target.value as ShowIfOp },
                })
              }
            >
              <option value="eq">等於</option>
              <option value="neq">不等於</option>
              <option value="includes">包含</option>
              <option value="notIncludes">不包含</option>
            </select>
            <input
              style={{ flex: 1 }}
              value={String(step.showIf.value)}
              placeholder="值"
              onChange={(e) =>
                set({ showIf: { ...step.showIf!, value: e.target.value } })
              }
            />
          </div>
        )}
      </div>
    </div>
  );
}
