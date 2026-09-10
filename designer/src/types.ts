export type StepType = "single" | "multi" | "text" | "textarea" | "number" | "info";
export type ShowIfOp = "eq" | "neq" | "includes" | "notIncludes";

export interface Option {
  value: string;
  label: string;
}

export interface ShowIf {
  field: string;
  op: ShowIfOp;
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

export interface Schema {
  id: string;
  slug: string;
  title: string;
  status: string;
  active_version: number | null;
  owner_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Version {
  id: string;
  schema_id: string;
  version: number;
  status: "draft" | "preview" | "published";
  definition: FormDefinition;
  created_at: string;
  published_at: string | null;
  preview_token: string | null;
}
