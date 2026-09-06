import type { Step } from "./types";

export function isVisible(step: Step, answers: Record<string, unknown>): boolean {
  if (!step.showIf) return true;
  const { field, op, value } = step.showIf;
  const raw = answers[field];
  switch (op) {
    case "eq":
      return raw === value;
    case "neq":
      return raw !== value;
    case "includes":
      return Array.isArray(raw) && raw.includes(value);
    case "notIncludes":
      return !Array.isArray(raw) || !raw.includes(value);
    default:
      return true;
  }
}
