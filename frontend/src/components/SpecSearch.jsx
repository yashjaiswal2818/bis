import React, { useState, useEffect } from 'react';
import { Search, AlertCircle, ArrowRight, ChevronRight, ExternalLink } from 'lucide-react';
import { getRegistryStats } from '../api/client';
import StandardCard from './StandardCard';
import LoadingSteps from './LoadingSteps';

const PRODUCT_CHIPS = [
  { label: 'PVC Cables 1100V', query: 'PVC insulated electric cables for working voltages up to and including 1100 V' },
  { label: '22K Gold Hallmarking', query: '22 Karat gold and gold alloys, jewellery and artefacts hallmarking' },
  { label: 'TMT Fe 500D', query: 'High strength deformed steel bars and wires for concrete reinforcement (TMT Grade Fe 500D)' },
  { label: 'Drinking Water', query: 'Drinking water quality specifications, physical, chemical and bacteriological parameters' },
  { label: 'Portland Cement PPC', query: 'Portland pozzolana cement flyash based for structural civil construction' },
];

const SPEC_CHIPS = [
  { label: 'CPWD RCC Work', query: 'Reinforced cement concrete structural building construction M25 grade with nominal aggregate 20mm, slump 100mm, machine vibrated' },
  { label: 'MES LT Panel', query: 'Replacement of Defective 415Volt LT Main Distribution Panel & 415 V LT Main Distribution Board, Street Light Incoming Cables, Main Incoming Power Cables and circuit Wirings' },
  { label: 'DoCA Gold Medals', query: 'Supply of 22 Karat gold medals for annual merit awards conforming to national hallmarking standards with 6-digit HUID' },
];

const MULTILINGUAL_CHIPS = [
  { label: 'हिन्दी: पीवीसी तार (1100V)', query: 'पीवीसी इंसुलेटेड बिजली के तार 1100 वोल्ट' },
  { label: 'हिन्दी: 22K सोना', query: '22 कैरेट सोने के आभूषण हॉलमार्किंग' },
  { label: 'हिन्दी: पीने का पानी', query: 'पीने का साफ पानी गुणवत्ता परीक्षण' },
  { label: 'Hinglish: bijli ke taar', query: 'bijli ke taar 1100V building wiring ke liye' },
];

const NATURAL_CHIPS = [
  { label: 'Fire Safety in Schools', query: 'Which BIS standard should we follow for fire safety in school and hospital buildings?' },
  { label: 'Drinking Water Tests', query: 'What are the official test methods for drinking water physical and chemical parameters?' },
  { label: 'Solar Rooftop Grid', query: 'Which Indian standard is applicable for rooftop solar grid-tied photovoltaic inverters?' },
];

const CHIP_SETS = {
  product: PRODUCT_CHIPS,
  spec: SPEC_CHIPS,
  multilingual: MULTILINGUAL_CHIPS,
  natural: NATURAL_CHIPS,
};

const MODE_LABELS = [
  { key: 'product',      label: 'Product Description' },
  { key: 'spec',         label: 'Technical Specification' },
  { key: 'multilingual', label: 'हिन्दी / Hinglish' },
  { key: 'natural',      label: 'Natural Language' },
];

const PLACEHOLDERS = {
  product: 'Describe a product, material, or equipment…',
  spec: 'Paste a tender clause, BoQ line item, or technical specification…',
  multilingual: 'अपनी भाषा में खोजें — हिन्दी या Hinglish…',
  natural: 'Ask a question about standards, testing, or compliance…',
};

export default function SpecSearch({
  onOpenGeMClause,
  onViewDetails,
  onSearch,
  searchResults,
  isSearching,
  searchError,
  onSwitchToTender,
  displayLanguage,
}) {
  const [query, setQuery] = useState('');
  const [inputMode, setInputMode] = useState('product');
  const [stats, setStats] = useState(null);
  const [recentSearches, setRecentSearches] = useState([]);

  // Load stats once
  useEffect(() => {
    let alive = true;
    getRegistryStats()
      .then((d) => { if (alive) setStats(d); })
      .catch(() => {});
    return () => { alive = false; };
  }, []);

  // Load recent searches from session
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem('is_recent_searches_v3');
      if (saved) setRecentSearches(JSON.parse(saved));
    } catch {}
  }, []);

  // Track real searches into recent-searches table
  useEffect(() => {
    if (searchResults && searchResults.query) {
      const hit = searchResults.hits?.[0];
      const entry = {
        query: searchResults.query,
        top_code: hit ? hit.is_code : '—',
        confidence: hit ? (hit.confidence || hit.relevance_band || 'LOW') : '—',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setRecentSearches((prev) => {
        const deduped = prev.filter((r) => r.query.toLowerCase() !== entry.query.toLowerCase());
        const updated = [entry, ...deduped].slice(0, 5);
        try { sessionStorage.setItem('is_recent_searches_v3', JSON.stringify(updated)); } catch {}
        return updated;
      });
    }
  }, [searchResults]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (query.trim()) onSearch(query.trim());
  };

  const handleSelectChip = (q) => {
    setQuery(q);
    onSearch(q);
  };

  const handleClear = () => {
    setQuery('');
    onSearch(null);
  };

  const hits = searchResults?.hits || [];
  const mostRelevantHits = hits.filter((h) => h.confidence === 'HIGH' || h.rank <= 2);
  const relatedHits = hits.filter((h) => !mostRelevantHits.includes(h));
  const activeChips = CHIP_SETS[inputMode] || PRODUCT_CHIPS;

  /* ------------------------------------------------------------------ */
  /*  LANDING PAGE (no results, not searching)                          */
  /* ------------------------------------------------------------------ */
  if (!searchResults && !isSearching) {
    return (
      <div className="portal-landing">
        {/* ── Hero ── */}
        <section className="hero">
          <div className="hero-grid-bg" aria-hidden="true" />
          <div className="hero-inner">
            <div className="hero-content">
              <h1>
                Find the right{' '}
                <span className="accent">Indian Standard</span>
                <br />for every procurement line item
              </h1>
              <p className="hero-sub">
                Semantic search across 33,500+ BIS standards with automatic
                Quality Control Order verification, edition mapping, and
                allied-standard discovery.
              </p>

              {/* Mode selector */}
              <div className="mode-bar">
                {MODE_LABELS.map((m) => (
                  <button
                    key={m.key}
                    className={`mode-btn ${inputMode === m.key ? 'active' : ''}`}
                    onClick={() => setInputMode(m.key)}
                  >{m.label}</button>
                ))}
              </div>

              {/* Search pill */}
              <form onSubmit={handleSubmit} className="search-pill">
                <Search size={20} className="pill-icon" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={PLACEHOLDERS[inputMode]}
                />
                <button type="submit" disabled={!query.trim() || isSearching}>
                  Search
                </button>
              </form>

              {/* Try chips */}
              <div className="chip-row">
                <span className="chip-label">Try:</span>
                {activeChips.map((c) => (
                  <button key={c.label} className="chip" onClick={() => handleSelectChip(c.query)}>
                    {c.label}
                  </button>
                ))}
              </div>

              <button className="tender-cta" onClick={onSwitchToTender}>
                Audit a tender document <ArrowRight size={16} />
              </button>
            </div>

            {/* Trust card */}
            <aside className="trust-card">
              <h3>Live Registry</h3>
              {stats ? (
                <dl className="trust-dl">
                  <div><dt>Standards indexed</dt><dd>{stats.total_standards?.toLocaleString('en-IN')}</dd></div>
                  <div><dt>QCO-notified products</dt><dd>{stats.qco_notified_count?.toLocaleString('en-IN')}</dd></div>
                  <div><dt>Certification schemes</dt><dd>{stats.scheme_count}</dd></div>
                  {stats.edition_link_count != null && (
                    <div><dt>Edition links</dt><dd>{stats.edition_link_count?.toLocaleString('en-IN')}</dd></div>
                  )}
                </dl>
              ) : (
                <div className="trust-skeleton">
                  <div /><div /><div /><div />
                </div>
              )}
              {stats?.data_provenance && (
                <p className="trust-prov">
                  Source: {stats.data_provenance.source}<br />
                  Snapshot: {stats.data_provenance.snapshot_date}
                </p>
              )}
            </aside>
          </div>
        </section>

        {/* ── Capabilities ── */}
        <section className="cap-section">
          <div className="cap-inner">
            <h2>What can this engine do?</h2>
            <div className="cap-grid">
              {[
                { icon: '🔍', title: 'Find applicable standards', desc: 'Search by product name, technical specification, or natural-language question.', action: () => document.querySelector('.search-pill input')?.focus() },
                { icon: '📑', title: 'Audit a tender or BoQ', desc: 'Upload a PDF or CSV and verify every line item for standard compliance.', action: onSwitchToTender },
                { icon: '🛡️', title: 'Check mandatory certification', desc: 'Verify ISI, CRS, and Hallmarking QCO enforcement for any product.', action: () => handleSelectChip('Packaged drinking water') },
                { icon: '🕒', title: 'Check edition currency', desc: 'Amber badges flag superseded editions and link to the current version.', action: () => handleSelectChip('33 Grade Ordinary Portland Cement') },
              ].map((c) => (
                <button key={c.title} className="cap-card" onClick={c.action}>
                  <span className="cap-emoji">{c.icon}</span>
                  <strong>{c.title}</strong>
                  <span>{c.desc}</span>
                  <ChevronRight size={16} className="cap-arrow" />
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* ── Data section ── */}
        <section className="data-section">
          <div className="data-inner">
            {/* Recent searches */}
            <div className="data-panel data-wide">
              <h3>Recent searches</h3>
              {recentSearches.length > 0 ? (
                <table className="recent-tbl">
                  <thead>
                    <tr><th>Query</th><th>Top result</th><th>Confidence</th><th>Time</th></tr>
                  </thead>
                  <tbody>
                    {recentSearches.map((r, i) => (
                      <tr key={i} onClick={() => handleSelectChip(r.query)}>
                        <td className="rt-q">{r.query}</td>
                        <td className="rt-c">{r.top_code}</td>
                        <td><span className={`conf-pill conf-${(r.confidence || '').toLowerCase()}`}>{r.confidence}</span></td>
                        <td className="rt-t">{r.time}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="empty-msg">Your searches will appear here</p>
              )}
            </div>

            {/* QCO watch */}
            <div className="data-panel data-narrow">
              <h3>Mandatory certification watch</h3>
              {stats?.qco_samples ? (
                <ul className="qco-ul">
                  {stats.qco_samples.map((row) => (
                    <li key={row.is_code}>
                      <button className="qco-row" onClick={() => handleSelectChip(row.is_code)} title={row.order_name}>
                        <span className="qco-code">{row.is_code}</span>
                        <span className="qco-title">{row.title}</span>
                        <span className={`qco-badge qco-badge-${row.scheme.toLowerCase()}`}>{row.scheme}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty-msg">Loading…</p>
              )}
            </div>
          </div>
        </section>

        {/* ── External resources ── */}
        <section className="ext-section">
          <div className="ext-inner">
            <h3>External resources</h3>
            <div className="ext-row">
              {[
                { name: 'bis.gov.in', href: 'https://bis.gov.in' },
                { name: 'standardsbis.bsbedge.com', href: 'https://standardsbis.bsbedge.com' },
                { name: 'manakonline.in', href: 'https://manakonline.in' },
                { name: 'BIS CARE', href: 'https://www.bis.gov.in/bis-care-app/' },
              ].map((l) => (
                <a key={l.name} href={l.href} target="_blank" rel="noreferrer">
                  {l.name} <ExternalLink size={13} />
                </a>
              ))}
            </div>
          </div>
        </section>
      </div>
    );
  }

  /* ------------------------------------------------------------------ */
  /*  RESULTS VIEW (searching or has results)                           */
  /* ------------------------------------------------------------------ */
  return (
    <div className="results-page">
      {/* Compact search bar */}
      <div className="results-search-bar">
        <form onSubmit={handleSubmit} className="results-form">
          <Search size={18} className="rsb-icon" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search Indian Standards…"
          />
          <button type="submit" className="rsb-search" disabled={isSearching || !query.trim()}>
            Search
          </button>
          <button type="button" className="rsb-clear" onClick={handleClear}>
            ← Back
          </button>
        </form>
      </div>

      {isSearching && <LoadingSteps />}

      {searchError && (
        <div className="error-banner">
          <AlertCircle size={16} />
          <span>{searchError}</span>
        </div>
      )}

      {!isSearching && searchResults && (
        <section className="results-body">
          {hits.length === 0 ? (
            <div className="empty-state-box">
              <h3 className="empty-state-title">No matching Indian Standard found</h3>
              <p className="empty-state-desc">
                Try describing the product, material, or technical requirement in more detail.
              </p>
            </div>
          ) : (
            <>
              {mostRelevantHits.length > 0 && (
                <div className="ranking-tier-group">
                  <div className="ranking-tier-header">
                    <span className="ranking-tier-title">Most Relevant Standards</span>
                    <span className="ranking-tier-count">{mostRelevantHits.length}</span>
                  </div>
                  {mostRelevantHits.map((hit) => (
                    <StandardCard
                      key={hit.is_code}
                      hit={hit}
                      onOpenGeMClause={onOpenGeMClause}
                      onViewDetails={onViewDetails}
                      displayLanguage={displayLanguage}
                      onSearch={onSearch}
                    />
                  ))}
                </div>
              )}
              {relatedHits.length > 0 && (
                <div className="ranking-tier-group related-tier">
                  <div className="ranking-tier-header">
                    <span className="ranking-tier-title">Related &amp; Allied Standards</span>
                    <span className="ranking-tier-count">{relatedHits.length}</span>
                  </div>
                  {relatedHits.map((hit) => (
                    <StandardCard
                      key={hit.is_code}
                      hit={hit}
                      onOpenGeMClause={onOpenGeMClause}
                      onViewDetails={onViewDetails}
                      displayLanguage={displayLanguage}
                      onSearch={onSearch}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          <p className="edition-disclosure">
            Edition as recorded in registry snapshot. Verify current edition at{' '}
            <a href="https://standardsbis.bsbedge.com" target="_blank" rel="noreferrer">standardsbis.bsbedge.com</a>{' '}
            before use in tender documents.
          </p>
        </section>
      )}
    </div>
  );
}
