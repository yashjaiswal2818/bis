import React, { useState } from 'react';
import { Search, Sparkles, AlertCircle, Info, Loader2 } from 'lucide-react';
import StandardCard from './StandardCard';

const SAMPLE_QUERIES = [
  {
    label: '🏗️ 43 Grade Cement',
    query: 'Procurement of 43 Grade Ordinary Portland Cement for reinforced cement concrete structural bridge works.',
  },
  {
    label: '🧱 Concrete Aggregates',
    query: 'Coarse and fine aggregates from natural sources for use in structural concrete works.',
  },
  {
    label: '⚡ 1100V PVC Cables',
    query: 'PVC insulated electric cables for working voltages up to and including 1100 V for building electrification.',
  },
  {
    label: '💧 Precast Concrete Pipes',
    query: 'Precast concrete pipes with and without reinforcement for water supply drainage and sewerage culverts.',
  },
  {
    label: '🛡️ Structural Steel TMT',
    query: 'High strength deformed steel bars and wires for concrete reinforcement (TMT Grade Fe 500D).',
  },
  {
    label: '🇮🇳 सीमेंट मानक (Hindi)',
    query: 'भवन निर्माण के लिए 33 ग्रेड पोर्टलैंड सीमेंट और फ्लाई ऐश सीमेंट आवश्यकताएँ',
  },
];

export default function SpecSearch({ onOpenGeMClause, onSearch, searchResults, isSearching, searchError }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSelectChip = (q) => {
    setQuery(q);
    onSearch(q);
  };

  return (
    <div className="spec-search-container">
      {/* Officer Helper Advice Banner */}
      <div className="officer-banner">
        <Info size={20} className="officer-banner-icon" />
        <div className="officer-banner-text">
          <h3>GFR 2017 Rule 144 & GeM Compliance Note</h3>
          <p>
            General Financial Rules mandate that technical specifications in public procurement tenders must be based on national standards (BIS) where available, without being restrictive to proprietary brands. Enter any tender item or scope below to retrieve the exact standard and mandatory Quality Control Orders (QCOs).
          </p>
        </div>
      </div>

      {/* Main Search Panel */}
      <div className="search-card">
        <div className="search-label-group">
          <label htmlFor="tender-query" className="search-title">
            <Search size={16} color="#60a5fa" />
            <span>Tender Item Description, Technical Specification, or Keyword:</span>
          </label>
          <span className="gfr-hint">Supports English, Technical Specs & Hindi</span>
        </div>

        <form onSubmit={handleSubmit} className="search-input-wrapper">
          <textarea
            id="tender-query"
            className="search-textarea"
            placeholder="e.g. Supply of 43 Grade Ordinary Portland Cement for RCC construction, or flame retardant low smoke cables..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
          />
          <button type="submit" className="btn-search" disabled={isSearching || !query.trim()}>
            {isSearching ? (
              <>
                <Loader2 size={16} className="spin-icon" />
                <span>Auditing...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Recommend Standards</span>
              </>
            )}
          </button>
        </form>

        {/* Quick Sample Chips */}
        <div className="quick-categories">
          <span className="quick-label">Frequently Procured Government Items (Quick Fill):</span>
          <div className="chips-wrap">
            {SAMPLE_QUERIES.map((item, idx) => (
              <button
                key={idx}
                type="button"
                className="chip-btn"
                onClick={() => handleSelectChip(item.query)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {searchError && (
        <div style={{ background: 'var(--alert-red-soft)', border: '1px solid var(--alert-red-border)', borderRadius: 'var(--radius-md)', padding: '1rem', color: '#f87171', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <AlertCircle size={18} />
          <span>{searchError}</span>
        </div>
      )}

      {/* Search Results */}
      {searchResults && (
        <section className="results-section">
          <div className="results-meta-header">
            <div className="results-count">
              Recommended Indian Standards ({searchResults.hits?.length || 0})
            </div>
            <div className="results-badges">
              <span className="badge badge-neutral">
                Search Latency: {searchResults.latency_seconds}s
              </span>
              <span className="badge badge-blue">
                Verified BIS Whitelist Guard
              </span>
            </div>
          </div>

          {searchResults.hits?.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', color: 'var(--text-secondary)' }}>
              <p>No matching Indian Standards found for this description. Try adjusting your technical keywords.</p>
            </div>
          ) : (
            searchResults.hits.map((hit) => (
              <StandardCard
                key={hit.is_code}
                hit={hit}
                onOpenGeMClause={onOpenGeMClause}
              />
            ))
          )}
        </section>
      )}
    </div>
  );
}
