import StepCard from "./StepCard";
import type { FormDefinition, Step } from "../types";

function uid() {
  return `s_${Math.random().toString(36).slice(2, 10)}`;
}

export const emptyStep = (): Step => ({
  id: uid(),
  type: "text",
  title: "新問題",
  required: false,
  options: [],
  showIf: null,
});

export interface StepsEditorProps {
  def: FormDefinition;
  onChange: (def: FormDefinition) => void;
}

export default function StepsEditor({ def, onChange }: StepsEditorProps) {
  const fieldOptions = (def.steps || [])
    .filter((s) => s.type !== "info")
    .map((s) => ({ id: s.id, title: s.title }));

  const updateStep = (index: number, step: Step) => {
    const steps = [...def.steps];
    steps[index] = step;
    onChange({ ...def, steps });
  };

  const deleteStep = (index: number) => {
    onChange({ ...def, steps: def.steps.filter((_, i) => i !== index) });
  };

  const moveStep = (index: number, dir: -1 | 1) => {
    const j = index + dir;
    if (j < 0 || j >= def.steps.length) return;
    const steps = [...def.steps];
    [steps[index], steps[j]] = [steps[j], steps[index]];
    onChange({ ...def, steps });
  };

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between", margin: "16px 0" }}>
        <h2>題目卡片</h2>
        <button
          className="btn primary"
          onClick={() => onChange({ ...def, steps: [...def.steps, emptyStep()] })}
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
    </>
  );
}
