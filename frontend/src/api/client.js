/**
 * API Client for BIS Indian Standards Recommendation Backend
 */

const API_BASE = 'http://127.0.0.1:8000';

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return await res.json();
  } catch (err) {
    return { status: 'offline', error: err.message };
  }
}

export async function getRegistryStats() {
  const res = await fetch(`${API_BASE}/api/registry-stats`);
  if (!res.ok) throw new Error(`Registry stats failed with status ${res.status}`);
  return await res.json();
}

export async function searchStandards(query, topK = 5, useCloudLLM = false) {
  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: query.trim(),
      top_k: topK,
      use_cloud_llm: useCloudLLM,
    }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Search failed with status ${res.status}`);
  }
  return await res.json();
}

export async function getStandardDetails(isCode) {
  const res = await fetch(`${API_BASE}/standards/${encodeURIComponent(isCode)}`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to fetch details for ${isCode}`);
  }
  return await res.json();
}

export async function generateGeMClause(isCode) {
  const res = await fetch(`${API_BASE}/gem-clause`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_code: isCode }),
  });
  if (!res.ok) {
    throw new Error(`Failed to generate GeM clause for ${isCode}`);
  }
  return await res.json();
}

export async function auditTenderFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/tender-audit`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    throw new Error(`Tender audit failed with status ${res.status}`);
  }
  return await res.json();
}

export async function judgeSearch(query, topK = 5) {
  const res = await fetch(`${API_BASE}/judge_search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: query.trim(), top_k: topK }),
  });
  if (!res.ok) {
    throw new Error(`Evaluation call failed for query`);
  }
  return await res.json();
}

export async function exportPdfReport(auditResult, filename) {
  const res = await fetch(`${API_BASE}/api/reports/export/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ audit_result: auditResult, filename: filename }),
  });
  if (!res.ok) {
    throw new Error(`PDF Export failed with status ${res.status}`);
  }
  return await res.blob();
}
