import React, { useState } from 'react';
import { Play, Download, CheckCircle, Terminal, Award, Activity, Loader2 } from 'lucide-react';
import { judgeSearch } from '../api/client';

const BENCHMARK_QUERIES = [
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

export default function BenchmarkSandbox() {
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState('');
  const [metrics, setMetrics] = useState(null);
  const [teamResults, setTeamResults] = useState(null);

  const runBenchmark = async () => {
    setIsRunning(true);
    setLogs('> Initializing offline benchmark evaluation against public benchmark queries...\n');
    setMetrics(null);
    setTeamResults(null);

    const norm = (s) => s.replace(/\s+/g, '').toLowerCase();
    let hitsAt3 = 0;
    let reciprocalRanks = [];
    let totalLatency = 0;
    const results = [];

    try {
      for (let i = 0; i < BENCHMARK_QUERIES.length; i++) {
        const q = BENCHMARK_QUERIES[i];
        setLogs((prev) => prev + `> [${i + 1}/${BENCHMARK_QUERIES.length}] Evaluating ${q.id}: "${q.query.slice(0, 45)}..." `);

        const res = await judgeSearch(q.query, 5);
        totalLatency += res.latency_seconds;
        const retrieved = res.retrieved_standards || [];

        results.push({
          id: q.id,
          query: q.query,
          expected_standards: [q.expected],
          retrieved_standards: retrieved,
          latency_seconds: res.latency_seconds,
        });

        // Hit@3
        const top3Norm = retrieved.slice(0, 3).map(norm);
        const expNorm = norm(q.expected);
        const isHit = top3Norm.includes(expNorm);
        if (isHit) hitsAt3++;

        // MRR@5
        const top5Norm = retrieved.slice(0, 5).map(norm);
        const rankIdx = top5Norm.indexOf(expNorm);
        const rr = rankIdx >= 0 ? 1.0 / (rankIdx + 1) : 0.0;
        reciprocalRanks.push(rr);

        setLogs((prev) => prev + `-> Match rank: ${rankIdx >= 0 ? `#${rankIdx + 1}` : 'MISS'} (${res.latency_seconds}s)\n`);
      }

      const hitRate = (hitsAt3 / BENCHMARK_QUERIES.length) * 100;
      const mrr = reciprocalRanks.reduce((a, b) => a + b, 0) / BENCHMARK_QUERIES.length;
      const avgLat = totalLatency / BENCHMARK_QUERIES.length;

      setMetrics({
        hitRate: hitRate.toFixed(1),
        mrr: mrr.toFixed(3),
        avgLatency: avgLat.toFixed(2),
      });

      setTeamResults(results);

      setLogs((prev) => prev + `\n========================================\n` +
        `EVALUATION COMPLETE:\n` +
        `Hit Rate @ 3: ${hitRate.toFixed(1)}% (Target: >80%)\n` +
        `MRR @ 5:      ${mrr.toFixed(3)} (Target: >0.70)\n` +
        `Avg Latency:  ${avgLat.toFixed(3)}s (Target: <5.0s)\n` +
        `========================================\n`
      );
    } catch (err) {
      setLogs((prev) => prev + `\n[ERROR] Evaluation interrupted: ${err.message}\n`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleDownloadResults = () => {
    if (!teamResults) return;
    const blob = new Blob([JSON.stringify(teamResults, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'team_results.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="benchmark-container">
      {/* Overview Banner */}
      <div className="officer-banner">
        <Activity size={20} className="officer-banner-icon" />
        <div className="officer-banner-text">
          <h3>Information Retrieval & Evaluation Benchmark</h3>
          <p>
            Evaluates the offline hybrid retrieval pipeline (BM25 lexical search + BGE-M3 1024-d dense vector index + Cross-Encoder reranking) against curated government procurement benchmark queries.
          </p>
        </div>
      </div>

      {/* Action Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <button
          className="btn-primary-search"
          onClick={runBenchmark}
          disabled={isRunning}
        >
          {isRunning ? (
            <>
              <Loader2 size={16} className="spin-icon" />
              <span>Running Benchmark ({BENCHMARK_QUERIES.length} Queries)...</span>
            </>
          ) : (
            <>
              <Play size={16} />
              <span>Execute Evaluation Suite</span>
            </>
          )}
        </button>

        {teamResults && (
          <button className="btn-action-outline" onClick={handleDownloadResults}>
            <Download size={15} />
            <span>Download team_results.json</span>
          </button>
        )}
      </div>

      {/* Metrics Dashboard */}
      {metrics && (
        <div className="benchmark-metrics-grid">
          <div className="metric-card">
            <div className="metric-label">Hit Rate @ 3</div>
            <div className="metric-value" style={{ color: '#059669' }}>
              {metrics.hitRate}%
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Target: &gt;80.0%</span>
          </div>

          <div className="metric-card">
            <div className="metric-label">MRR @ 5</div>
            <div className="metric-value" style={{ color: 'var(--primary-blue)' }}>
              {metrics.mrr}
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Mean Reciprocal Rank</span>
          </div>

          <div className="metric-card">
            <div className="metric-label">Avg Search Latency</div>
            <div className="metric-value" style={{ color: 'var(--primary-navy)' }}>
              {metrics.avgLatency}s
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Hardware-Adaptive Target: &lt;5s</span>
          </div>
        </div>
      )}

      {/* Terminal Log Console */}
      <div className="terminal-box" aria-label="Evaluation Console Output">
        {logs || '> Standby. Click "Execute Evaluation Suite" to run public test queries...'}
      </div>
    </div>
  );
}
