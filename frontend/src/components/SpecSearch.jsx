import React, { useState, useEffect } from 'react';
import { Search, AlertCircle, ArrowRight, ChevronRight, ExternalLink, FileSearch, ClipboardList, ShieldCheck, History } from 'lucide-react';
import { getRegistryStats } from '../api/client';
import StandardCard from './StandardCard';
import LoadingSteps from './LoadingSteps';
import { useLanguage } from '../i18n';

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

const CHIP_SETS = { product: PRODUCT_CHIPS, spec: SPEC_CHIPS, multilingual: MULTILINGUAL_CHIPS, natural: NATURAL_CHIPS };

const MODE_LABELS = [
  { key: 'product', labelKey: 'mode_product' },
  { key: 'spec', labelKey: 'mode_spec' },
  { key: 'multilingual', labelKey: 'mode_multilingual' },
  { key: 'natural', labelKey: 'mode_natural' },
];

const PLACEHOLDER_KEYS = {
  product: 'placeholder_product',
  spec: 'placeholder_spec',
  multilingual: 'placeholder_multilingual',
  natural: 'placeholder_natural',
};

const CAPABILITIES = [
  { id: 'find', icon: FileSearch, titleKey: 'cap1_title', descKey: 'cap1_desc' },
  { id: 'audit', icon: ClipboardList, titleKey: 'cap2_title', descKey: 'cap2_desc' },
  { id: 'certify', icon: ShieldCheck, titleKey: 'cap3_title', descKey: 'cap3_desc' },
  { id: 'edition', icon: History, titleKey: 'cap4_title', descKey: 'cap4_desc' },
];

export default function SpecSearch({ onOpenGeMClause, onViewDetails, onSearch, searchResults, isSearching, searchError, onSwitchToTender }) {
  const { t } = useLanguage();
  const [query, setQuery] = useState('');
  const [inputMode, setInputMode] = useState('product');
  const [stats, setStats] = useState(null);
  const [recentSearches, setRecentSearches] = useState([]);

  useEffect(() => {
    let alive = true;
    getRegistryStats().then((d) => { if (alive) setStats(d); }).catch(() => {});
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    try {
      const saved = sessionStorage.getItem('is_recent_searches_v3');
      if (saved) setRecentSearches(JSON.parse(saved));
    } catch {}
  }, []);

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

  const handleSubmit = (e) => { e?.preventDefault(); if (query.trim()) onSearch(query.trim()); };
  const handleSelectChip = (q) => { setQuery(q); onSearch(q); };
  const handleClear = () => { setQuery(''); onSearch(null); };

  const hits = searchResults?.hits || [];
  const mostRelevantHits = hits.filter((h) => h.confidence === 'HIGH' || h.rank <= 2);
  const relatedHits = hits.filter((h) => !mostRelevantHits.includes(h));
  const activeChips = CHIP_SETS[inputMode] || PRODUCT_CHIPS;

  if (!searchResults && !isSearching) {
    return (
      <div className="portal-landing">
        <section className="hero">
          <div className="hero-grid-bg" aria-hidden="true" />
          <img src="/bis-logo.png" alt="" aria-hidden="true" className="hero-watermark-seal" width="340" />
          <div className="hero-inner">
            <div className="hero-content">
              <h1>{t('hero_title_pre')}<span className="accent">{t('hero_title_accent')}</span><br />{t('hero_title_post')}</h1>
              <p className="hero-sub">
                {t('hero_sub')}
              </p>

              <div className="mode-bar">
                {MODE_LABELS.map((m) => (
                  <button key={m.key} className={`mode-btn ${inputMode === m.key ? 'active' : ''}`} onClick={() => setInputMode(m.key)}>{t(m.labelKey)}</button>
                ))}
              </div>

              <form onSubmit={handleSubmit} className="search-pill">
                <Search size={20} className="pill-icon" />
                <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t(PLACEHOLDER_KEYS[inputMode])} />
                <button type="submit" disabled={!query.trim() || isSearching}>{t('common_search')}</button>
              </form>

              <div className="chip-row">
                <span className="chip-label">{t('chip_try')}</span>
                {activeChips.map((c) => (
                  <button key={c.label} className="chip" onClick={() => handleSelectChip(c.query)}>{c.label}</button>
                ))}
              </div>

              <button className="tender-cta" onClick={onSwitchToTender}>{t('cta_audit_tender')} <ArrowRight size={16} /></button>
            </div>

            <aside className="trust-card">
              <div className="trust-seal-header">
                <img src="/bis-logo.png" alt="Bureau of Indian Standards" width="52" height="43" />
                <div className="trust-seal-header-text">
                  <h3>{t('trust_title')}</h3>
                  <span className="trust-seal-sub">{t('trust_sub')}</span>
                </div>
              </div>
              {stats ? (
                <dl className="trust-dl">
                  <div><dt>{t('trust_standards_indexed')}</dt><dd>{stats.total_standards?.toLocaleString('en-IN')}</dd></div>
                  <div><dt>{t('trust_qco_notified')}</dt><dd>{stats.qco_notified_count?.toLocaleString('en-IN')}</dd></div>
                  <div><dt>{t('trust_cert_schemes')}</dt><dd>{stats.scheme_count}</dd></div>
                  {stats.edition_link_count != null && <div><dt>{t('trust_edition_links')}</dt><dd>{stats.edition_link_count?.toLocaleString('en-IN')}</dd></div>}
                </dl>
              ) : (
                <div className="trust-skeleton"><div /><div /><div /><div /></div>
              )}
              {stats?.data_provenance && (
                <p className="trust-prov">{t('trust_source', { source: stats.data_provenance.source })}<br />{t('trust_snapshot', { date: stats.data_provenance.snapshot_date })}</p>
              )}
            </aside>
          </div>
        </section>

        <section className="cap-section">
          <div className="cap-inner">
            <h2>{t('cap_heading')}</h2>
            <div className="cap-grid">
              {CAPABILITIES.map((c) => {
                const action = c.id === 'audit' ? onSwitchToTender
                  : c.id === 'certify' ? () => handleSelectChip('Packaged drinking water')
                  : c.id === 'edition' ? () => handleSelectChip('33 Grade Ordinary Portland Cement')
                  : () => document.querySelector('.search-pill input')?.focus();
                return (
                  <button key={c.id} className="cap-card" onClick={action}>
                    <c.icon size={22} className="cap-icon" />
                    <strong>{t(c.titleKey)}</strong>
                    <span>{t(c.descKey)}</span>
                    <ChevronRight size={16} className="cap-arrow" />
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        <section className="data-section">
          <div className="data-inner">
            <div className="data-panel data-wide">
              <h3>{t('recent_searches')}</h3>
              {recentSearches.length > 0 ? (
                <table className="recent-tbl">
                  <thead><tr><th>{t('tbl_query')}</th><th>{t('tbl_top_result')}</th><th>{t('tbl_confidence')}</th><th>{t('tbl_time')}</th></tr></thead>
                  <tbody>
                    {recentSearches.map((r, i) => (
                      <tr key={i} onClick={() => handleSelectChip(r.query)}>
                        <td className="rt-q">{r.query}</td>
                        <td className="rt-c mono">{r.top_code}</td>
                        <td><span className={`conf-pill conf-${(r.confidence || '').toLowerCase()}`}>{r.confidence}</span></td>
                        <td className="rt-t">{r.time}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="empty-msg">{t('recent_empty')}</p>
              )}
            </div>

            <div className="data-panel data-narrow">
              <h3>{t('qco_watch_title')}</h3>
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
                <p className="empty-msg">{t('common_loading')}</p>
              )}
            </div>
          </div>
        </section>

        <section className="ext-section">
          <div className="ext-inner">
            <h3>{t('ext_resources')}</h3>
            <div className="ext-row">
              {[
                { name: 'bis.gov.in', href: 'https://bis.gov.in' },
                { name: 'standardsbis.bsbedge.com', href: 'https://standardsbis.bsbedge.com' },
                { name: 'manakonline.in', href: 'https://manakonline.in' },
                { name: 'BIS CARE', href: 'https://www.bis.gov.in/bis-care-app/' },
              ].map((l) => (
                <a key={l.name} href={l.href} target="_blank" rel="noreferrer">{l.name} <ExternalLink size={13} /></a>
              ))}
            </div>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="results-page">
      <div className="results-search-bar">
        <form onSubmit={handleSubmit} className="results-form">
          <Search size={18} className="rsb-icon" />
          <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t('placeholder_results_search')} />
          <button type="submit" className="rsb-search" disabled={isSearching || !query.trim()}>{t('common_search')}</button>
          <button type="button" className="rsb-clear" onClick={handleClear}>{t('back')}</button>
        </form>
      </div>

      {isSearching && <LoadingSteps query={query} />}

      {searchError && (
        <div className="error-banner"><AlertCircle size={16} /><span>{searchError}</span></div>
      )}

      {!isSearching && searchResults && (
        <section className="results-body">
          {hits.length === 0 ? (
            <div className="empty-state-box">
              <h3 className="empty-state-title">{t('no_match_title')}</h3>
              <p className="empty-state-desc">{t('no_match_desc')}</p>
            </div>
          ) : (
            <>
              {mostRelevantHits.length > 0 && (
                <div className="ranking-tier-group">
                  <div className="ranking-tier-header">
                    <span className="ranking-tier-title">{t('most_relevant')}</span>
                    <span className="ranking-tier-count">{mostRelevantHits.length}</span>
                  </div>
                  {mostRelevantHits.map((hit) => (
                    <StandardCard key={hit.is_code} hit={hit} onOpenGeMClause={onOpenGeMClause} onViewDetails={onViewDetails} onSearch={onSearch} />
                  ))}
                </div>
              )}
              {relatedHits.length > 0 && (
                <div className="ranking-tier-group related-tier">
                  <div className="ranking-tier-header">
                    <span className="ranking-tier-title">{t('related_allied')}</span>
                    <span className="ranking-tier-count">{relatedHits.length}</span>
                  </div>
                  {relatedHits.map((hit) => (
                    <StandardCard key={hit.is_code} hit={hit} onOpenGeMClause={onOpenGeMClause} onViewDetails={onViewDetails} onSearch={onSearch} />
                  ))}
                </div>
              )}
            </>
          )}

          <p className="edition-disclosure">
            {t('edition_disclosure_pre')}
            <a href="https://standardsbis.bsbedge.com" target="_blank" rel="noreferrer">standardsbis.bsbedge.com</a>
            {t('edition_disclosure_post')}
          </p>
        </section>
      )}
    </div>
  );
}
