const STORAGE_KEY = "ff_owner_token";
const DEFAULT_TOKEN = "dev-token";

/** Resolve owner token: localStorage → ?token= query → default dev-token. */
export function getOwnerToken(): string {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && stored.trim()) return stored.trim();
  } catch {
    /* ignore */
  }
  try {
    const q = new URLSearchParams(window.location.search).get("token");
    if (q && q.trim()) {
      setOwnerToken(q.trim());
      return q.trim();
    }
  } catch {
    /* ignore */
  }
  return DEFAULT_TOKEN;
}

export function setOwnerToken(token: string): void {
  const t = (token || "").trim() || DEFAULT_TOKEN;
  try {
    localStorage.setItem(STORAGE_KEY, t);
  } catch {
    /* ignore */
  }
}

export { STORAGE_KEY, DEFAULT_TOKEN };
