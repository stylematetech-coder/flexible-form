import type { PublicForm, ResponseDoc } from "../types";

const BASE = "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export const api = {
  getBySlug: (slug: string) => req<PublicForm>(`/public/forms/${slug}`),
  getByPreview: (token: string) => req<PublicForm>(`/public/preview/${token}`),
  createResponse: (
    slug: string,
    body: { identity: { name: string; phone: string }; answers?: Record<string, unknown> }
  ) =>
    req<ResponseDoc>(`/public/forms/${slug}/responses`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchResponse: (
    id: string,
    body: {
      identity?: { name: string; phone: string };
      answers?: Record<string, unknown>;
    }
  ) =>
    req<ResponseDoc>(`/public/responses/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  submit: (id: string) =>
    req<ResponseDoc>(`/public/responses/${id}/submit`, { method: "POST" }),
};
