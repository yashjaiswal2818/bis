const API_BASE = "http://127.0.0.1:8000";

// --- Tab Switching ---
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    btn.classList.add("active");
    const target = btn.getAttribute("data-tab");
    document.getElementById(target).classList.add("active");
  });
});

// --- Health Check ---
async function checkBackendHealth() {
  const statusElem = document.getElementById("backend-status");
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      statusElem.textContent = "Backend: Online (Port 8000)";
      statusElem.parentElement.querySelector(".status-dot").classList.add("online");
    } else {
      statusElem.textContent = "Backend: Offline";
      statusElem.parentElement.querySelector(".status-dot").classList.remove("online");
    }
  } catch (err) {
    statusElem.textContent = "Backend: Not Connected";
    statusElem.parentElement.querySelector(".status-dot").classList.remove("online");
  }
}
setInterval(checkBackendHealth, 5000);
checkBackendHealth();

// --- Quick Chips ---
document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const q = chip.getAttribute("data-query");
    document.getElementById("query-input").value = q;
    performSearch(q);
  });
});

// --- Search Execution ---
document.getElementById("search-btn").addEventListener("click", () => {
  const q = document.getElementById("query-input").value.trim();
  if (q) performSearch(q);
});

document.getElementById("query-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    const q = e.target.value.trim();
    if (q) performSearch(q);
  }
});

async function performSearch(query) {
  const btn = document.getElementById("search-btn");
  const container = document.getElementById("results-container");
  const list = document.getElementById("results-list");
  const latencyTag = document.getElementById("latency-tag");

  btn.textContent = "Searching...";
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, top_k: 5 }),
    });

    if (!res.ok) throw new Error("Search failed");
    const data = await res.json();

    container.style.display = "block";
    latencyTag.textContent = `Latency: ${data.latency_seconds}s`;
    list.innerHTML = "";

    data.hits.forEach(hit => {
      const card = document.createElement("div");
      card.className = "result-card";

      // Badges
      const confClass = hit.confidence === "HIGH" ? "badge-high" : "badge-medium";
      const statusClass = hit.status === "ACTIVE" ? "badge-active" : "badge-superseded";
      let statusBadge = `<span class="badge ${statusClass}">${hit.status}</span>`;
      if (hit.status === "SUPERSEDED" && hit.superseded_by) {
        statusBadge += `<span class="badge badge-superseded">Superseded by ${hit.superseded_by}</span>`;
      }

      // QCO Alert Callout
      let qcoHtml = "";
      if (hit.qco_rules && hit.qco_rules.length > 0 && hit.qco_rules[0].is_mandatory) {
        const qco = hit.qco_rules[0];
        qcoHtml = `
          <div class="qco-callout">
            <strong>⚠️ MANDATORY QCO ALERT (${qco.scheme_type}):</strong> ${qco.compliance_warning}
          </div>
        `;
      }

      // Allied Standards
      let alliedHtml = "";
      if (hit.allied_standards && hit.allied_standards.length > 0) {
        const topAllied = hit.allied_standards.slice(0, 4);
        const chips = topAllied.map(a => `<span class="allied-chip" title="${a.label}: ${a.title}">${a.target_is_code} (${a.relation_type})</span>`).join("");
        alliedHtml = `
          <div class="allied-section">
            <div class="allied-tags">
              <span style="font-size:0.75rem; color:var(--text-muted); font-weight:600;">ALLIED:</span>
              ${chips}
            </div>
            <button class="btn btn-outline gem-btn" data-code="${hit.is_code}">📋 GeM Tender Clause</button>
          </div>
        `;
      } else {
        alliedHtml = `
          <div class="allied-section" style="justify-content: flex-end;">
            <button class="btn btn-outline gem-btn" data-code="${hit.is_code}">📋 GeM Tender Clause</button>
          </div>
        `;
      }

      card.innerHTML = `
        <div class="card-top">
          <div>
            <div class="is-code-title">#${hit.rank} ${hit.is_code}</div>
            <div class="standard-name">${hit.title}</div>
          </div>
          <div class="badges-group">
            <span class="badge ${confClass}">Score: ${Math.round(hit.rerank_score * 100)}% (${hit.confidence})</span>
            ${statusBadge}
          </div>
        </div>
        ${qcoHtml}
        <div class="scope-text">${hit.scope || "Specification requirements for Indian standard conformance."}</div>
        <div class="rationale-box">
          <span class="rationale-label">AI RATIONALE:</span> ${hit.rationale}
        </div>
        ${alliedHtml}
      `;

      list.appendChild(card);
    });

    // Attach modal listener
    document.querySelectorAll(".gem-btn").forEach(b => {
      b.addEventListener("click", () => openGeMModal(b.getAttribute("data-code")));
    });

  } catch (err) {
    alert("Error executing search: " + err.message);
  } finally {
    btn.textContent = "Recommend Standards";
    btn.disabled = false;
  }
}

// --- GeM Modal ---
const modal = document.getElementById("gem-modal");
const closeBtn = document.getElementById("modal-close-btn");
const copyBtn = document.getElementById("copy-clause-btn");

closeBtn.addEventListener("click", () => modal.style.display = "none");
modal.addEventListener("click", (e) => {
  if (e.target === modal) modal.style.display = "none";
});

async function openGeMModal(isCode) {
  modal.style.display = "flex";
  const textarea = document.getElementById("gem-clause-text");
  textarea.value = "Generating official GeM tender clause for " + isCode + " ...";

  try {
    const res = await fetch(`${API_BASE}/gem-clause`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_code: isCode }),
    });
    if (!res.ok) throw new Error("Failed to generate clause");
    const data = await res.json();
    textarea.value = data.full_tender_specification_text;
  } catch (err) {
    textarea.value = "Error generating specification clause: " + err.message;
  }
}

copyBtn.addEventListener("click", () => {
  const textarea = document.getElementById("gem-clause-text");
  textarea.select();
  navigator.clipboard.writeText(textarea.value);
  copyBtn.textContent = "✅ Copied to Clipboard!";
  setTimeout(() => copyBtn.textContent = "📋 Copy to Clipboard", 2000);
});

// --- Tender Dropzone ---
const dropzone = document.getElementById("tender-dropzone");
const fileInput = document.getElementById("tender-file-input");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.style.borderColor = "var(--accent-blue)";
});
dropzone.addEventListener("dragleave", () => {
  dropzone.style.borderColor = "var(--border-color)";
});
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.style.borderColor = "var(--border-color)";
  if (e.dataTransfer.files.length) {
    uploadTender(e.dataTransfer.files[0]);
  }
});
fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) uploadTender(e.target.files[0]);
});

async function uploadTender(file) {
  const summary = document.getElementById("tender-audit-summary");
  const clausesList = document.getElementById("tender-clauses-list");
  const container = document.getElementById("tender-results");

  container.style.display = "block";
  summary.innerHTML = `<p style="color:var(--text-secondary);">Auditing ${file.name}...</p>`;
  clausesList.innerHTML = "";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE}/tender-audit`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error("Audit failed");
    const data = await res.json();

    summary.innerHTML = `
      <div style="background:var(--bg-surface-elevated); padding:1rem; border-radius:var(--radius-md); margin-bottom:1rem; border:1px solid var(--border-color);">
        <strong>File:</strong> ${file.name} | <strong>Type:</strong> ${data.type.toUpperCase()}
        ${data.warning ? `<p style="color:var(--warning-amber); margin-top:0.4rem;">${data.warning}</p>` : ""}
      </div>
    `;

    const items = data.items_audited || data.clauses_analyzed || [];
    items.forEach(item => {
      const card = document.createElement("div");
      card.className = "result-card";
      const recs = item.recommended_standards.map(r => `<span class="badge badge-active">${r.is_code} (${r.title})</span>`).join(" ");

      card.innerHTML = `
        <div style="font-size:0.9rem; font-weight:600; margin-bottom:0.5rem;">
          Item: "${item.item_description || item.clause_text}"
        </div>
        <div><strong>Applicable Standards:</strong> ${recs}</div>
      `;
      clausesList.appendChild(card);
    });

  } catch (err) {
    summary.innerHTML = `<p style="color:var(--danger-red);">Upload failed: ${err.message}</p>`;
  }
}

// --- Judge Sandbox Execution ---
document.getElementById("run-eval-btn").addEventListener("click", runJudgeBenchmark);

async function runJudgeBenchmark() {
  const runBtn = document.getElementById("run-eval-btn");
  const grid = document.getElementById("metrics-grid");
  const logBox = document.getElementById("sandbox-log");

  runBtn.textContent = "⏳ Running Benchmark (10 Queries)...";
  runBtn.disabled = true;
  grid.style.display = "grid";
  logBox.style.display = "block";
  logBox.innerHTML = "> Loading benchmark queries from public_test_set.json ...\n";

  try {
    // Benchmark queries from public_test_set.json
    const queries = [
      { id: "PUB-01", query: "We are a small enterprise manufacturing 33 Grade Ordinary Portland Cement. Which BIS standard covers the chemical and physical requirements?", expected: "IS 269: 1989" },
      { id: "PUB-02", query: "I need to comply with the regulations for coarse and fine aggregates derived from natural sources intended for use in structural concrete.", expected: "IS 383: 1970" },
      { id: "PUB-03", query: "What is the official specification for manufacturing precast concrete pipes, both with and without reinforcement, for water mains?", expected: "IS 458: 2003" },
      { id: "PUB-04", query: "Our company is shifting to manufacturing hollow and solid lightweight concrete masonry blocks. What standard outlines dimensional tolerances and strength?", expected: "IS 2185 (Part 2): 1983" },
      { id: "PUB-05", query: "Requirements for low-heat portland cement intended for massive concrete structures like dams where hydration heat must be minimized.", expected: "IS 12600: 1989" },
      { id: "PUB-06", query: "Specifications for high-alumina cement intended for refractory applications and resistance to chemical attack.", expected: "IS 6452: 1989" },
      { id: "PUB-07", query: "Manufacturing requirements for portland pozzolana cement based on calcined clay for general construction work.", expected: "IS 1489 (Part 2): 1991" },
      { id: "PUB-08", query: "Standard requirements for manufacturing autoclave cellular concrete blocks for structural masonry and partition walls.", expected: "IS 2185 (Part 3): 1984" },
      { id: "PUB-09", query: "Physical and chemical properties required for supersulphated cement used in marine structures subject to chemical attack.", expected: "IS 6909: 1990" },
      { id: "PUB-10", query: "Specifications for hydrophobic portland cement intended for long-term storage in high-humidity tropical conditions.", expected: "IS 8043: 1991" }
    ];

    let hitsAt3 = 0;
    let reciprocalRanks = [];
    let totalLatency = 0;
    const teamResults = [];

    const norm = s => s.replace(/\s+/g, "").toLowerCase();

    for (let i = 0; i < queries.length; i++) {
      const q = queries[i];
      logBox.innerHTML += `> [${i + 1}/${queries.length}] Evaluating ${q.id} ... `;

      const res = await fetch(`${API_BASE}/judge_search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q.query, top_k: 5 }),
      });

      if (!res.ok) throw new Error("Evaluation failed at " + q.id);
      const data = await res.json();

      totalLatency += data.latency_seconds;
      const retrieved = data.retrieved_standards;

      teamResults.push({
        id: q.id,
        query: q.query,
        expected_standards: [q.expected],
        retrieved_standards: retrieved,
        latency_seconds: data.latency_seconds,
      });

      // Compute Hit@3
      const top3Norm = retrieved.slice(0, 3).map(norm);
      const expNorm = norm(q.expected);
      const hit = top3Norm.includes(expNorm);
      if (hit) hitsAt3++;

      // Compute MRR@5
      const top5Norm = retrieved.slice(0, 5).map(norm);
      const rankIdx = top5Norm.indexOf(expNorm);
      const rr = rankIdx >= 0 ? 1.0 / (rankIdx + 1) : 0.0;
      reciprocalRanks.push(rr);

      logBox.innerHTML += `Match rank: ${rankIdx >= 0 ? rankIdx + 1 : "MISS"} (${data.latency_seconds}s)\n`;
      logBox.scrollTop = logBox.scrollHeight;
    }

    const hitRate = (hitsAt3 / queries.length) * 100;
    const mrr = reciprocalRanks.reduce((a, b) => a + b, 0) / queries.length;
    const avgLat = totalLatency / queries.length;

    document.getElementById("hit-value").textContent = `${hitRate.toFixed(1)}%`;
    document.getElementById("mrr-value").textContent = mrr.toFixed(3);
    document.getElementById("lat-value").textContent = `${avgLat.toFixed(2)}s`;

    logBox.innerHTML += `\n========================================\n`;
    logBox.innerHTML += `EVALUATION COMPLETE:\n`;
    logBox.innerHTML += `Hit Rate @ 3: ${hitRate.toFixed(1)}% (Target: >80%)\n`;
    logBox.innerHTML += `MRR @ 5:      ${mrr.toFixed(3)} (Target: >0.70)\n`;
    logBox.innerHTML += `Avg Latency:  ${avgLat.toFixed(3)}s (Target: <5.0s)\n`;
    logBox.innerHTML += `========================================\n`;

    // Enable download
    const dlBtn = document.getElementById("download-results-btn");
    dlBtn.style.display = "inline-block";
    dlBtn.onclick = () => {
      const blob = new Blob([JSON.stringify(teamResults, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "team_results.json";
      a.click();
    };

  } catch (err) {
    logBox.innerHTML += `\nError during evaluation: ${err.message}\n`;
  } finally {
    runBtn.textContent = "🚀 Run Benchmark (public_test_set.json)";
    runBtn.disabled = false;
  }
}
