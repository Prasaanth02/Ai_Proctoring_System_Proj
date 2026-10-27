const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function generateBRD(file) {
  const form = new FormData();
  form.append('file', file);

  const res = await fetch(`${API_BASE}/generate-brd`, {
    method: 'POST',
    body: form,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || `Server error ${res.status}`);
  }

  return data; // { brd: string, filename: string }
}
