import React, { useState, useEffect } from 'react';
import { Search, Sparkles, AlertCircle, Info, FileQuestion, HelpCircle, History, ArrowRight, CheckCircle2, ChevronRight, X } from 'lucide-react';
import StandardCard from './StandardCard';
import LoadingSteps from './LoadingSteps';

const PRODUCT_CHIPS = [
  { icon: '⚡', label: 'PVC Power Cables (1.1 kV)', query: 'PVC insulated electric cables for working voltages up to and including 1100 V' },
  { icon: '🏷️', label: '22k Gold Jewellery & Artefacts', query: '22 Karat gold and gold alloys, jewellery and artefacts hallmarking' },
  { icon: '🔩', label: 'Structural Steel TMT (Fe 500D)', query: 'High strength deformed steel bars and wires for concrete reinforcement (TMT Grade Fe 500D)' },
  { icon: '💧', label: 'Drinking Water Quality', query: 'Drinking water quality specifications, physical, chemical and bacteriological parameters' },
  { icon: '🧱', label: 'Portland Pozzolana Cement', query: 'Portland pozzolana cement flyash based for structural civil construction' },
  { icon: '🚨', label: 'Fire Detection & Alarm System', query: 'Automatic fire detection and alarm systems, smoke detectors and fire alarm control panels' },
];

const SPEC_CHIPS = [
  { icon: '📑', label: 'CPWD RCC Structural Work', query: 'Reinforced cement concrete structural building construction M25 grade with nominal aggregate 20mm, slump 100mm, machine vibrated' },
  { icon: '📑', label: 'MES LT Distribution Panel', query: 'Replacement of Defective 415Volt LT Main Distribution Panel & 415 V LT Main Distribution Board, Street Light Incoming Cables, Main Incoming Power Cables and circuit Wirings' },
  { icon: '📑', label: 'DoCA Precious Articles', query: 'Supply of 22 Karat gold medals for annual merit awards conforming to national hallmarking standards with 6-digit HUID' },
  { icon: '📑', label: 'MeitY Lithium Storage Cells', query: 'Secondary sealed lithium cells and batteries for portable equipment under compulsory registration scheme' },
];

const MULTILINGUAL_CHIPS = [
  { icon: '⚡', label: '🇮🇳 हिन्दी: पीवीसी तार (1100V)', query: 'पीवीसी इंसुलेटेड बिजली के तार 1100 वोल्ट' },
  { icon: '🏷️', label: '🇮🇳 हिन्दी: 22K सोना हॉलमार्किंग', query: '22 कैरेट सोने के आभूषण हॉलमार्किंग' },
  { icon: '💧', label: '🇮🇳 हिन्दी: पीने का पानी परीक्षण', query: 'पीने का साफ पानी गुणवत्ता परीक्षण' },
  { icon: '🧱', label: '🇮🇳 हिन्दी: पोर्टलैंड सीमेंट (PPC)', query: 'पोर्टलैंड पोजोलाना सीमेंट flyash based' },
  { icon: '🔌', label: '🌐 Hinglish: bijli ke taar', query: 'bijli ke taar 1100V building wiring ke liye' },
  { icon: '✨', label: '🌐 Hinglish: sone ke gehne 22k', query: 'sone ke gehne 22k hallmarking huid ke sath' },
];

const NATURAL_CHIPS = [
  { icon: '💬', label: 'Building Fire Safety in Schools', query: 'Which BIS standard should we follow for fire safety in school and hospital buildings?' },
  { icon: '💬', label: 'Drinking Water Testing Norms', query: 'What are the official test methods for drinking water physical and chemical parameters?' },
  { icon: '💬', label: '22k Gold HUID Requirement', query: 'We want to procure 22 carat gold medals with mandatory 6-digit HUID hallmarking for merit awards' },
  { icon: '💬', label: 'Solar Rooftop Grid Connection', query: 'Which Indian standard is applicable for rooftop solar grid-tied photovoltaic inverters?' },
];

const CONVERSATIONAL_PATTERNS = [
  /^(?:hi|hello|hey|who are you|how are you|tell me a joke|test)\b/i,
  /^(?:what is your name|greetings)\b/i,
];

export default function SpecSearch({
  onOpenGeMClause,
  onViewDetails,
  onSearch,
  searchResults,
  isSearching,
  searchError,
  onSwitchToTender,
}) {
  const [query, setQuery] = useState('');
  const [inputMode, setInputMode] = useState('product'); // 'product' | 'spec'
  const [recentSearches, setRecentSearches] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [activeComponentFilter, setActiveComponentFilter] = useState('ALL');
  const [displayLanguage, setDisplayLanguage] = useState(() => {
    try {
      return localStorage.getItem('is_display_language') || 'en';
    } catch {
      return 'en';
    }
  });

  const handleLanguageChange = (lang) => {
    setDisplayLanguage(lang);
    try {
      localStorage.setItem('is_display_language', lang);
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    try {
      const saved = localStorage.getItem('is_recent_searches');
      if (saved) {
        setRecentSearches(JSON.parse(saved));
      }
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const saveToHistory = (q) => {
    const trimmed = q.trim();
    if (!trimmed || trimmed.length < 3) return;
    setRecentSearches((prev) => {
      const filtered = prev.filter((item) => item.toLowerCase() !== trimmed.toLowerCase());
      const updated = [trimmed, ...filtered].slice(0, 8);
      try {
        localStorage.setItem('is_recent_searches', JSON.stringify(updated));
      } catch {
        // Ignore
      }
      return updated;
    });
  };

  const handleClearHistory = () => {
    setRecentSearches([]);
    localStorage.removeItem('is_recent_searches');
    setShowHistory(false);
  };

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (query.trim()) {
      saveToHistory(query);
      setActiveComponentFilter('ALL');
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
    saveToHistory(q);
    setActiveComponentFilter('ALL');
    onSearch(q);
  };

  const isConversationalQuery = (text) => {
    const trimmed = text.trim();
    if (trimmed.length < 2) return false;
    const lower = trimmed.toLowerCase();
    // Never block queries with technical, standards, materials, or multilingual keywords
    if (
      lower.includes('standard') ||
      lower.includes('is ') ||
      lower.includes('code') ||
      lower.includes('bis') ||
      lower.includes('norm') ||
      lower.includes('fire') ||
      lower.includes('water') ||
      lower.includes('cement') ||
      lower.includes('cable') ||
      lower.includes('wire') ||
      lower.includes('gold') ||
      lower.includes('steel') ||
      lower.includes('safety') ||
      lower.includes('test') ||
      lower.includes('taar') ||
      lower.includes('bijli') ||
      lower.includes('sone') ||
      lower.includes('paani') ||
      lower.includes('gehne') ||
      lower.includes('loha') ||
      /[\u0900-\u097F]/.test(lower)
    ) {
      return false;
    }
    return CONVERSATIONAL_PATTERNS.some((pat) => pat.test(trimmed));
  };

  const hasInvalidInput = query.trim() && isConversationalQuery(query);

  const hits = searchResults?.hits || [];
  const queryLower = (searchResults?.query || '').toLowerCase();

  const detectedComponents = [];
  if (queryLower.includes('panel') || queryLower.includes('board') || queryLower.includes('switchgear')) {
    detectedComponents.push({ id: 'PANEL', label: 'LT Panel & Distribution Boards', keywords: ['panel', 'switchgear', 'board', 'breaker', 'distribution'] });
  }
  if (queryLower.includes('cable') || queryLower.includes('wire') || queryLower.includes('wiring')) {
    detectedComponents.push({ id: 'CABLE', label: 'Cables & Conductors', keywords: ['cable', 'wire', 'conductor', 'pvc', 'xlpe'] });
  }
  if (queryLower.includes('earthing') || queryLower.includes('earth')) {
    detectedComponents.push({ id: 'EARTHING', label: 'Earthing & Protection', keywords: ['earthing', 'earth', 'grounding'] });
  }
  if (queryLower.includes('pipe') || queryLower.includes('sewerage') || queryLower.includes('drainage')) {
    detectedComponents.push({ id: 'PIPE', label: 'Pipes & Drainage', keywords: ['pipe', 'drainage', 'culvert', 'sewerage'] });
  }
  if (queryLower.includes('cement') || queryLower.includes('concrete') || queryLower.includes('aggregate') || queryLower.includes('steel')) {
    detectedComponents.push({ id: 'CIVIL', label: 'Civil & Structural Materials', keywords: ['cement', 'concrete', 'aggregate', 'steel', 'tmt', 'bars'] });
  }

  const filteredHits = hits.filter((hit) => {
    if (activeComponentFilter === 'ALL') return true;
    const comp = detectedComponents.find((c) => c.id === activeComponentFilter);
    if (!comp) return true;
    const text = `${hit.is_code} ${hit.title} ${hit.scope || ''} ${hit.schedule_category || ''}`.toLowerCase();
    return comp.keywords.some((kw) => text.includes(kw));
  });

  const mostRelevantHits = filteredHits.filter((h) => h.confidence === 'HIGH' || h.rank <= 2);
  const relatedHits = filteredHits.filter((h) => !mostRelevantHits.includes(h));

  return (
    <div className="spec-search-container">
      {/* Clean Hero Header */}
      <section className="hero-section">
        <div className="hero-pill">
          <Sparkles size={12} color="#d97706" />
          <span>Bureau of Indian Standards • National Procurement Directory</span>
        </div>
        <h1 className="hero-title">Find the Right Indian Standards</h1>
        <p className="hero-subtitle">
          Search by product, material, specification, or upload a tender document.
        </p>
      </section>

      {/* Main Search Console */}
      <div className="search-card">
        <div className="search-header-row">
          <label htmlFor="tender-query" className="search-input-label">
            <Search size={16} color="#1e5bb8" />
            <span>Search Indian Standards</span>
          </label>
          <span className="search-hint">हिन्दी • Hinglish • English</span>
        </div>

        {/* Input Mode Selector (Feature 1: Product descriptions vs Technical specifications vs Multilingual vs Natural Language vs Tender documents) */}
        <div className="input-mode-tabs">
          <div className="input-mode-group" aria-label="Search input mode">
          <button
            type="button"
            aria-pressed={inputMode === 'product'}
            className={`input-mode-tab ${inputMode === 'product' ? 'active' : ''}`}
            onClick={() => setInputMode('product')}
          >
            <span>🏷️</span>
            <span>Product Description</span>
          </button>
          <button
            type="button"
            aria-pressed={inputMode === 'spec'}
            className={`input-mode-tab ${inputMode === 'spec' ? 'active' : ''}`}
            onClick={() => setInputMode('spec')}
          >
            <span>📑</span>
            <span>Technical Specification</span>
          </button>
          <button
            type="button"
            aria-pressed={inputMode === 'multilingual'}
            className={`input-mode-tab ${inputMode === 'multilingual' ? 'active' : ''}`}
            onClick={() => setInputMode('multilingual')}
          >
            <span>🇮🇳</span>
            <span>हिन्दी / Hinglish</span>
          </button>
          <button
            type="button"
            aria-pressed={inputMode === 'natural'}
            className={`input-mode-tab ${inputMode === 'natural' ? 'active' : ''}`}
            onClick={() => setInputMode('natural')}
          >
            <span>💬</span>
            <span>Natural Language Query</span>
          </button>
          </div>
          <button
            type="button"
            className="tender-switch-link"
            onClick={onSwitchToTender}
            title="Upload Tender PDF, CSV, or BoQ schedule for automatic clause audit"
          >
            <span>📂</span>
            <span>Tender document</span>
            <ArrowRight size={13} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="search-box-container">
          <div className="search-textarea-wrap">
            <textarea
              id="tender-query"
              className="search-textarea"
              placeholder={
                inputMode === 'product'
                  ? "Enter product name or commodity description (e.g., 'PVC insulated electric cables for working voltages up to 1100 V')..."
                  : inputMode === 'spec'
                  ? "Paste technical specification clause, bill of quantities (BoQ) item, or engineering parameters (e.g., 'Reinforced cement concrete structural building construction M25 grade with nominal aggregate 20mm, slump 100mm, machine vibrated')..."
                  : inputMode === 'multilingual'
                  ? "अपनी भाषा में खोजें (जैसे 'पीवीसी इंसुलेटेड बिजली के तार 1100 वोल्ट', '22 कैरेट सोने के आभूषण हॉलमार्किंग', या 'bijli ke taar 1100V building wiring')..."
                  : "Ask any conversational question (e.g., 'Which BIS standard should we follow for fire safety in school and hospital buildings?' or 'What are the official test methods for drinking water parameters?')..."
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={2}
            />

            <div className="search-controls-bar">
              <div className="search-actions-left">
                {recentSearches.length > 0 && (
                  <button
                    type="button"
                    className="history-toggle-btn"
                    onClick={() => setShowHistory(!showHistory)}
                    title="View recent procurement searches"
                  >
                    <History size={14} />
                    <span>Recent ({recentSearches.length})</span>
                  </button>
                )}
                <span className="search-char-count">{query.length} chars</span>
              </div>

              <div className="search-shortcut-hint">
                <span>Press <strong>Enter ↵</strong> to search</span>
              </div>

              <button
                type="submit"
                className="btn-primary-search"
                disabled={isSearching || !query.trim()}
              >
                <Search size={16} />
                <span>Search Indian Standards</span>
              </button>
            </div>
          </div>
        </form>

        {/* Recent Searches Panel */}
        {showHistory && recentSearches.length > 0 && (
          <div className="recent-searches-panel">
            <div className="recent-header">
              <span>Recent Procurement Searches</span>
              <button className="recent-clear-btn" onClick={handleClearHistory}>
                Clear All
              </button>
            </div>
            <div className="recent-list">
              {recentSearches.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="recent-item-btn"
                  onClick={() => handleSelectChip(item)}
                >
                  {item.length > 45 ? item.slice(0, 45) + '...' : item}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Example Query Chips based on Selected Mode */}
        <div className="example-chips-section">
          <span className="example-chips-label">Try:</span>
          <div className="chips-wrap">
            {(inputMode === 'product'
              ? PRODUCT_CHIPS
              : inputMode === 'spec'
              ? SPEC_CHIPS
              : inputMode === 'multilingual'
              ? MULTILINGUAL_CHIPS
              : NATURAL_CHIPS
            ).map((item, idx) => (
              <button
                key={idx}
                type="button"
                className="chip-btn"
                onClick={() => handleSelectChip(item.query)}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Invalid Query Alert (Requirement 11) */}
      {hasInvalidInput && (
        <div style={{
          background: '#fffbeb',
          border: '1.5px solid #fde68a',
          borderRadius: 'var(--radius-lg)',
          padding: '1.1rem 1.35rem',
          color: '#92400e',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.75rem',
          marginBottom: '1.5rem',
          boxShadow: 'var(--shadow-xs)'
        }}>
          <AlertCircle size={20} style={{ flexShrink: 0, marginTop: '0.1rem' }} />
          <div>
            <strong style={{ display: 'block', fontSize: '0.92rem', marginBottom: '0.2rem' }}>
              This doesn't appear to be a standards-related requirement.
            </strong>
            <span style={{ fontSize: '0.86rem', color: '#78350f' }}>
              Try entering a product, material, equipment, construction activity, testing requirement, or procurement specification (e.g. <em>"PVC insulated power cables"</em> or <em>"415 V LT distribution panel"</em>).
            </span>
          </div>
        </div>
      )}

      {/* Search Error Alert */}
      {searchError && (
        <div style={{
          background: '#fef2f2',
          border: '1.5px solid #fecaca',
          borderRadius: 'var(--radius-lg)',
          padding: '1.1rem 1.35rem',
          color: '#991b1b',
          display: 'flex',
          alignItems: 'center',
          gap: '0.65rem',
          marginBottom: '1.5rem',
          boxShadow: 'var(--shadow-xs)'
        }}>
          <AlertCircle size={20} />
          <span>{searchError}</span>
        </div>
      )}

      {/* Multi-Step Loading Experience (Requirement 12) */}
      {isSearching && <LoadingSteps query={query} />}

      {/* Search Results Display */}
      {!isSearching && searchResults && (
        <section className="results-section">
          {/* Results Meta Bar */}
          <div className="results-meta-bar">
            <div className="results-count-title">
              Recommended Indian Standards ({hits.length})
            </div>
            <div className="results-meta-tags">
              <span className="badge badge-neutral">
                Search Latency: {searchResults.latency_seconds}s
              </span>
              <span className="badge badge-emerald">
                <CheckCircle2 size={12} />
                <span>Verified 33k+ BIS Whitelist Guard</span>
              </span>
            </div>
          </div>

          {/* Multilingual Result Language Switcher (Govt Procurement Multi-Language Bar) */}
          <div className="result-language-switcher-bar">
            <div className="result-lang-label">
              <span>🌐</span>
              <span>Result Language / निकालाची भाषा:</span>
            </div>
            <div className="result-lang-buttons">
              <button
                type="button"
                className={`btn-lang-choice ${displayLanguage === 'en' ? 'active' : ''}`}
                onClick={() => handleLanguageChange('en')}
                title="Official English as gazetted by BIS"
              >
                <span>🇬🇧 English</span>
              </button>
              <button
                type="button"
                className={`btn-lang-choice ${displayLanguage === 'mr' ? 'active' : ''}`}
                onClick={() => handleLanguageChange('mr')}
                title="मराठीत निकाल पहा (View results in Marathi)"
              >
                <span>🇮🇳 मराठी</span>
              </button>
              <button
                type="button"
                className={`btn-lang-choice ${displayLanguage === 'hi' ? 'active' : ''}`}
                onClick={() => handleLanguageChange('hi')}
                title="हिन्दी में परिणाम देखें (View results in Hindi)"
              >
                <span>🇮🇳 हिन्दी</span>
              </button>
              <button
                type="button"
                className={`btn-lang-choice ${displayLanguage === 'ta' ? 'active' : ''}`}
                onClick={() => handleLanguageChange('ta')}
                title="தமிழில் முடிவுகளைக் காண்க (View results in Tamil)"
              >
                <span>🇮🇳 தமிழ்</span>
              </button>
              <button
                type="button"
                className={`btn-lang-choice ${displayLanguage === 'te' ? 'active' : ''}`}
                onClick={() => handleLanguageChange('te')}
                title="తెలుగులో ఫలితాలను చూడండి (View results in Telugu)"
              >
                <span>🇮🇳 తెలుగు</span>
              </button>
              <button
                type="button"
                className={`btn-lang-choice ${displayLanguage === 'bn' ? 'active' : ''}`}
                onClick={() => handleLanguageChange('bn')}
                title="বাংলায় ফলাফল দেখুন (View results in Bengali)"
              >
                <span>🇮🇳 বাংলা</span>
              </button>
              <button
                type="button"
                className={`btn-lang-choice ${displayLanguage === 'gu' ? 'active' : ''}`}
                onClick={() => handleLanguageChange('gu')}
                title="ગુજરાતીમાં પરિણામો જુઓ (View results in Gujarati)"
              >
                <span>🇮🇳 ગુજરાતી</span>
              </button>
              <button
                type="button"
                className={`btn-lang-choice ${displayLanguage === 'kn' ? 'active' : ''}`}
                onClick={() => handleLanguageChange('kn')}
                title="ಕನ್ನಡದಲ್ಲಿ ಫಲಿತಾಂಶಗಳನ್ನು ವೀಕ್ಷಿಸಿ (View results in Kannada)"
              >
                <span>🇮🇳 ಕನ್ನಡ</span>
              </button>
            </div>
          </div>

          {/* Semantic Neural Understanding Badge (Feature 2) */}
          <div className="semantic-understanding-bar">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <span style={{ fontSize: '1.25rem' }}>🧠</span>
              <div>
                <div style={{ fontSize: '0.86rem', fontWeight: 700, color: 'var(--primary-navy)' }}>
                  Semantic Understanding & Neural Ranking
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  Matches derived from multi-dimensional engineering scope and parametric concepts (BGE-M3 1024-dim dense cross-encoder), not simple keyword matching.
                </div>
              </div>
            </div>
            <span className="badge badge-blue">Dense Embeddings + Neural Reranker</span>
          </div>

          {/* Complex Query Component Filter (Requirement 9) */}
          {detectedComponents.length > 1 && (
            <div className="component-filter-bar">
              <span className="component-filter-label">Filter Component:</span>
              <button
                className={`component-pill-btn ${activeComponentFilter === 'ALL' ? 'active' : ''}`}
                onClick={() => setActiveComponentFilter('ALL')}
              >
                All Standards ({hits.length})
              </button>
              {detectedComponents.map((comp) => (
                <button
                  key={comp.id}
                  className={`component-pill-btn ${activeComponentFilter === comp.id ? 'active' : ''}`}
                  onClick={() => setActiveComponentFilter(comp.id)}
                >
                  {comp.label}
                </button>
              ))}
            </div>
          )}

          {/* Empty State (Requirement 10) */}
          {hits.length === 0 ? (
            <div className="empty-state-box">
              <div className="empty-state-icon">
                <FileQuestion size={26} />
              </div>
              <h3 className="empty-state-title">No closely matching Indian Standard found</h3>
              <p className="empty-state-desc">
                The search query did not yield any high-confidence match in the official 33,553 Bureau of Indian Standards catalog.
                Try describing the product, material, equipment, process or technical requirement in more detail.
              </p>

              <div className="empty-tips-card">
                <div className="empty-tips-title">Search Tips for Procurement Officers:</div>
                <ul className="empty-tips-list">
                  <li><strong>Standard Number:</strong> Enter the direct code if known (e.g. <code>IS 694</code>, <code>IS 456</code>, <code>IS 1786</code>).</li>
                  <li><strong>Technical Parameters:</strong> Include voltage, grade, or material type (e.g. <em>"415 V LT switchgear"</em>, <em>"43 Grade OPC"</em>).</li>
                  <li><strong>Avoid Brand Names:</strong> Citing generic specifications rather than proprietary vendor brand names.</li>
                </ul>
              </div>
            </div>
          ) : (
            <>
              {/* Ranking Tier 1: Most Relevant (Requirement 6) */}
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
                    />
                  ))}
                </div>
              )}

              {/* Ranking Tier 2: Related Standards (Requirement 6) */}
              {relatedHits.length > 0 && (
                <div className="ranking-tier-group" style={{ marginTop: '1.25rem' }}>
                  <div className="ranking-tier-header">
                    <span className="ranking-tier-title">Related & Allied Standards</span>
                    <span className="ranking-tier-count">{relatedHits.length}</span>
                  </div>
                  {relatedHits.map((hit) => (
                    <StandardCard
                      key={hit.is_code}
                      hit={hit}
                      onOpenGeMClause={onOpenGeMClause}
                      onViewDetails={onViewDetails}
                      displayLanguage={displayLanguage}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </section>
      )}
    </div>
  );
}
