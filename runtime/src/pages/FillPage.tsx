import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { isVisible } from "../showIf";
import type { PublicForm, Step } from "../types";

type Mode = "public" | "preview";

export default function FillPage({ mode }: { mode: Mode }) {
  const { slug, token } = useParams<{ slug?: string; token?: string }>();
  const nav = useNavigate();
  const [form, setForm] = useState<PublicForm | null>(null);
  const [phase, setPhase] = useState<"identity" | "steps">("identity");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [stepIndex, setStepIndex] = useState(0);
  const [responseId, setResponseId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setError("");
    const load =
      mode === "public" && slug
        ? api.getBySlug(slug)
        : mode === "preview" && token
          ? api.getByPreview(token)
          : Promise.reject(new Error("缺少參數"));
    load
      .then(setForm)
      .catch((e) => setError(String(e.message || e)));
  }, [mode, slug, token]);

  const visibleSteps = useMemo(() => {
    if (!form) return [] as Step[];
    return form.definition.steps.filter((s) => isVisible(s, answers));
  }, [form, answers]);

  const current = visibleSteps[stepIndex];

  const startFill = async () => {
    if (!form) return;
    setError("");
    const req = form.definition.settings.require_identity || [];
    if (req.includes("name") && !name.trim()) {
      setError("請填寫姓名");
      return;
    }
    if (req.includes("phone") && !phone.trim()) {
      setError("請填寫電話");
      return;
    }
    setBusy(true);
    try {
      if (mode === "public" && slug) {
        const r = await api.createResponse(slug, {
          identity: { name: name.trim(), phone: phone.trim() },
          answers: {},
        });
        setResponseId(r.id);
      }
      // preview mode: local-only, no persistence required for demo
      setPhase("steps");
      setStepIndex(0);
    } catch (e: unknown) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const setAnswer = (stepId: string, value: unknown) => {
    setAnswers((prev) => ({ ...prev, [stepId]: value }));
  };

  const persist = async (nextAnswers: Record<string, unknown>) => {
    if (!responseId) return;
    await api.patchResponse(responseId, { answers: nextAnswers });
  };

  const validateCurrent = (): boolean => {
    if (!current || current.type === "info") return true;
    if (!current.required) return true;
    const v = answers[current.id];
    if (v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0)) {
      setError("此題為必填");
      return false;
    }
    return true;
  };

  const next = async () => {
    setError("");
    if (!validateCurrent()) return;
    setBusy(true);
    try {
      await persist(answers);
      // recompute visible after answer
      if (stepIndex >= visibleSteps.length - 1) {
        await finish();
      } else {
        setStepIndex((i) => i + 1);
      }
    } catch (e: unknown) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const back = () => {
    setError("");
    setStepIndex((i) => Math.max(0, i - 1));
  };

  const finish = async () => {
    if (responseId) {
      await api.patchResponse(responseId, { answers });
      await api.submit(responseId);
    }
    nav("/done");
  };

  if (error && !form) {
    return (
      <>
        <header className="topbar">問卷</header>
        <main className="main">
          <div className="card error">{error}</div>
        </main>
      </>
    );
  }

  if (!form) {
    return (
      <>
        <header className="topbar">問卷</header>
        <main className="main">
          <p className="muted">載入中…</p>
        </main>
      </>
    );
  }

  const progress =
    phase === "identity"
      ? 5
      : visibleSteps.length
        ? Math.round(((stepIndex + 1) / visibleSteps.length) * 100)
        : 100;

  return (
    <>
      <header className="topbar">
        {form.title}
        {form.mode === "preview" && <span className="badge">預覽</span>}
      </header>
      <main className="main">
        <div className="progress">
          <span style={{ width: `${progress}%` }} />
        </div>
        <div className="card stack">
          {phase === "identity" && (
            <>
              <h2>請先填寫基本資料</h2>
              <label>姓名</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="您的姓名"
              />
              <label>電話</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="手機號碼"
              />
              {error && <div className="error">{error}</div>}
              <button className="btn primary" disabled={busy} onClick={startFill}>
                開始填寫
              </button>
            </>
          )}

          {phase === "steps" && current && (
            <>
              <div className="muted">
                {stepIndex + 1} / {visibleSteps.length}
              </div>
              {current.type === "info" ? (
                <div className="info-block">
                  <h2>{current.title}</h2>
                </div>
              ) : (
                <>
                  <h2>
                    {current.title}
                    {current.required && <span style={{ color: "#e03131" }}> *</span>}
                  </h2>
                  <StepInput step={current} value={answers[current.id]} onChange={setAnswer} />
                </>
              )}
              {error && <div className="error">{error}</div>}
              <div className="row" style={{ justifyContent: "space-between" }}>
                <button className="btn" disabled={stepIndex === 0 || busy} onClick={back}>
                  上一題
                </button>
                <button className="btn primary" disabled={busy} onClick={next}>
                  {stepIndex >= visibleSteps.length - 1 ? "提交" : "下一題"}
                </button>
              </div>
            </>
          )}

          {phase === "steps" && !current && (
            <>
              <p>沒有可顯示的題目</p>
              <button className="btn primary" onClick={() => finish()}>
                提交
              </button>
            </>
          )}
        </div>
      </main>
    </>
  );
}

function StepInput({
  step,
  value,
  onChange,
}: {
  step: Step;
  value: unknown;
  onChange: (id: string, v: unknown) => void;
}) {
  if (step.type === "single") {
    return (
      <div className="stack">
        {step.options.map((o) => (
          <label className="option" key={o.value}>
            <input
              type="radio"
              name={step.id}
              checked={value === o.value}
              onChange={() => onChange(step.id, o.value)}
            />
            {o.label}
          </label>
        ))}
      </div>
    );
  }
  if (step.type === "multi") {
    const arr = Array.isArray(value) ? (value as string[]) : [];
    const toggle = (v: string) => {
      if (arr.includes(v)) onChange(step.id, arr.filter((x) => x !== v));
      else onChange(step.id, [...arr, v]);
    };
    return (
      <div className="stack">
        {step.options.map((o) => (
          <label className="option" key={o.value}>
            <input
              type="checkbox"
              checked={arr.includes(o.value)}
              onChange={() => toggle(o.value)}
            />
            {o.label}
          </label>
        ))}
      </div>
    );
  }
  if (step.type === "textarea") {
    return (
      <textarea
        rows={4}
        value={String(value ?? "")}
        onChange={(e) => onChange(step.id, e.target.value)}
      />
    );
  }
  if (step.type === "number") {
    return (
      <input
        type="number"
        value={value === undefined || value === null ? "" : String(value)}
        onChange={(e) =>
          onChange(step.id, e.target.value === "" ? "" : Number(e.target.value))
        }
      />
    );
  }
  return (
    <input
      type="text"
      value={String(value ?? "")}
      onChange={(e) => onChange(step.id, e.target.value)}
    />
  );
}
