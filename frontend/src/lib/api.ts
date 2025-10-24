const API_BASE = `${window.location.origin}/api`;

export async function login(username: string, password: string) {
  const r = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{ access_token: string; token_type: string }>
}

export function authHeaders() {
  const t = localStorage.getItem('qv_token') || '';
  return { 'Authorization': `Bearer ${t}` } as HeadersInit;
}

export async function listCollections() {
  const r = await fetch(`${API_BASE}/collections`, { headers: authHeaders() });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function createCollection(data: { name: string; vectors_size: number; distance: 'Cosine'|'Dot'|'Euclid' }) {
  const r = await fetch(`${API_BASE}/collections`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data)
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function searchVector(data: { collection: string; vector: number[]; limit?: number; with_payload?: boolean }) {
  const r = await fetch(`${API_BASE}/vectors/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data)
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
