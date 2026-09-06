export type StepType = "single" | "multi" | "text" | "textarea" | "number" | "info";

export interface Option {
  value: string;
  label: string;
}

export interface ShowIf {
  field: string;
  op: "eq" | "neq" | "includes" | "notIncludes";
  value: string;
}

export interface Step {
  id: string;
  type: StepType;
  title: string;
  required: boolean;
  options: Option[];
  showIf: ShowIf | null;
}

export interface FormDefinition {
  version: string;
  locale: string;
  settings: {
    require_identity: string[];
    one_response_per: string | null;
  };
  steps: Step[];
}

export interface PublicForm {
  schema_id: string;
  slug: string;
  title: string;
  version: number;
  definition: FormDefinition;
  mode: "public" | "preview";
}

export interface ResponseDoc {
  id: string;
  schema_id: string;
  version: number;
  status: "in_progress" | "submitted";
  identity: { name: string; phone: string };
  answers: Record<string, unknown>;
  created_at: string;
  submitted_at: string | null;
}
