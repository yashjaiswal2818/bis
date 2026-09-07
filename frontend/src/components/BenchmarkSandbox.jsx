import React, { useState } from 'react';
import { Play, Download, CheckCircle, Terminal, Award, Activity } from 'lucide-react';
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
    setLogs('> Initializing offline benchmark evaluation against public test set...\n');
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
    a.click();
  };

  return (
    <div className="benchmark-sandbox-container">
      <div className="officer-banner">
        <Award size={20} className="officer-banner-icon" />
        <div className="officer-banner-text">
          <h3>Recommendation Accuracy & Latency Benchmarks</h3>
          <p>
            Verify the offline retrieval accuracy, reciprocal rank scores, and CPU latency ladder across the standardized test dataset. This guarantees retrieval precision before deploying tender specifications.
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <button
          className="btn-search"
          style={{ height: '42px', padding: '0 1.25rem' }}
          onClick={runBenchmark}
          disabled={isRunning}
        >
          <Play size={15} />
          <span>{isRunning ? 'Running Benchmark...' : 'Run Benchmark (public_test_set.json)'}</span>
        </button>

        {teamResults && (
          <button className="btn-action-primary" onClick={handleDownloadResults}>
            <Download size={15} />
            <span>Download team_results.json</span>
          </button>
        )}
      </div>

      {/* Metrics Grid */}
      {metrics && (
        <div className="benchmark-metrics-grid">
          <div className="metric-card">
            <span className="metric-title">Hit Rate @ 3</span>
            <span className="metric-value" style={{ color: '#34d399' }}>{metrics.hitRate}%</span>
            <span className="metric-target">Target: &gt; 80% (Accurate Match)</span>
          </div>

          <div className="metric-card">
            <span className="metric-title">Mean Reciprocal Rank (MRR@5)</span>
            <span className="metric-value" style={{ color: '#60a5fa' }}>{metrics.mrr}</span>
            <span className="metric-target">Target: &gt; 0.70 (Top Rank Precision)</span>
          </div>

          <div className="metric-card">
            <span className="metric-title">Average Latency per Query</span>
            <span className="metric-value" style={{ color: '#fbbf24' }}>{metrics.avgLatency}s</span>
            <span className="metric-target">Target: &lt; 2.0s (Hardware Adaptive)</span>
          </div>
        </div>
      )}

      {/* Terminal Logs */}
      {logs && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <Terminal size={14} />
            <span>Evaluation Execution Log:</span>
          </div>
          <pre className="terminal-log">{logs}</pre>
        </div>
      )}
    </div>
  );
}
