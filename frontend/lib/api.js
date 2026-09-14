export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    cache: "no-store",
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    const err = new Error(data?.detail ? JSON.stringify(data.detail) : res.statusText);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}
