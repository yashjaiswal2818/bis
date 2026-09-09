import React, { useState } from 'react';
import { Search, Sparkles, AlertCircle, Info, Loader2, FileQuestion, HelpCircle } from 'lucide-react';
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
    label: '👑 Gold Hallmarking (DoCA)',
    query: 'Mandatory gold jewellery purity marking and 6-digit HUID hallmarking requirements.',
  },
  {
    label: '🔋 Lithium Battery (CRS)',
    query: 'Safety requirements for secondary lithium cells and batteries under compulsory registration scheme.',
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
            <div className="empty-results-card" style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-lg)',
              padding: '2.5rem 2rem',
              textAlign: 'center',
              marginTop: '1rem',
            }}>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                background: 'rgba(245, 158, 11, 0.12)',
                color: '#f59e0b',
                marginBottom: '1rem'
              }}>
                <FileQuestion size={28} />
              </div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                No Matching Indian Standards Found
              </h3>
              <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto 1.5rem auto', fontSize: '0.95rem', lineHeight: '1.6' }}>
                The search query did not yield any high-confidence match in the official 33,553 Bureau of Indian Standards catalog. Zero spurious standards are returned to guarantee 100% compliance with GFR Rule 144.
              </p>

              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem',
                maxWidth: '650px',
                margin: '0 auto',
                textAlign: 'left'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#60a5fa', fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.75rem' }}>
                  <HelpCircle size={16} />
                  <span>Search Recommendations & Assistance:</span>
                </div>
                <ul style={{ listStyleType: 'disc', paddingLeft: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.875rem', lineHeight: '1.7' }}>
                  <li><strong>Standard Code Format:</strong> Use verified standard numbers (e.g., <code style={{ color: '#93c5fd' }}>IS 269</code>, <code style={{ color: '#93c5fd' }}>IS 383</code>, <code style={{ color: '#93c5fd' }}>IS 458</code>, <code style={{ color: '#93c5fd' }}>IS 1786</code>). Unverified standard codes are safely rejected.</li>
                  <li><strong>Engineering Specifications:</strong> Include material grades or test parameters (e.g., <em>"43 grade Ordinary Portland Cement"</em>, <em>"PVC insulated cables up to 1100V"</em>).</li>
                  <li><strong>Bilingual Support:</strong> Technical tender queries in Hindi (e.g., <em>"भवन निर्माण के लिए पोर्टलैंड सीमेंट"</em>) are natively indexed.</li>
                  <li><strong>Quick Fill:</strong> Select any of the frequently procured government items in the quick-fill chips above.</li>
                </ul>
              </div>
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
