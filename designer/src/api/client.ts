import type { FormDefinition, Schema, Version } from "../types";
import { getOwnerToken } from "./owner";

const BASE = "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getOwnerToken();
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export const api = {
  listSchemas: () => req<Schema[]>("/schemas"),
  createSchema: (title: string, slug: string) =>
    req<Schema>("/schemas", {
      method: "POST",
      body: JSON.stringify({ title, slug }),
    }),
  getSchema: (id: string) =>
    req<{ schema: Schema; versions: Version[] }>(`/schemas/${id}`),
  createVersion: (schemaId: string) =>
    req<Version>(`/schemas/${schemaId}/versions`, { method: "POST", body: "{}" }),
  patchVersion: (schemaId: string, vid: string, definition: FormDefinition) =>
    req<Version>(`/schemas/${schemaId}/versions/${vid}`, {
      method: "PATCH",
      body: JSON.stringify({ definition }),
    }),
  preview: (schemaId: string, vid: string) =>
    req<Version>(`/schemas/${schemaId}/versions/${vid}/preview`, { method: "POST" }),
  publish: (schemaId: string, vid: string) =>
    req<Version>(`/schemas/${schemaId}/versions/${vid}/publish`, { method: "POST" }),
  rollback: (schemaId: string, vid: string) =>
    req<Version>(`/schemas/${schemaId}/versions/${vid}/rollback`, { method: "POST" }),
  aiChat: (
    schemaId: string,
    messages: { role: string; content: string }[]
  ) =>
    req<{
      reply: string;
      proposed_definition: FormDefinition | null;
      proposed_schema_title?: string | null;
    }>(`/schemas/${schemaId}/ai/chat`, {
      method: "POST",
      body: JSON.stringify({ messages }),
    }),
  aiApply: (
    schemaId: string,
    definition: FormDefinition,
    schema_title?: string | null
  ) =>
    req<Version>(`/schemas/${schemaId}/ai/apply`, {
      method: "POST",
      body: JSON.stringify({
        definition,
        ...(schema_title ? { schema_title } : {}),
      }),
    }),
};
