import React, { useState } from 'react';
import { ShieldAlert, CheckCircle2, AlertTriangle, FileText, Copy, Check, Info, Award, Zap, ShieldCheck } from 'lucide-react';

export default function StandardCard({ hit, onOpenGeMClause, onViewDetails, displayLanguage = 'en', onSearch }) {
  const [copiedCode, setCopiedCode] = useState(false);
  const [showOriginalEnglish, setShowOriginalEnglish] = useState(false);

  const isLocalized = displayLanguage !== 'en' && !showOriginalEnglish && hit.translations && hit.translations[displayLanguage];
  const activeTranslation = isLocalized ? hit.translations[displayLanguage] : null;

  const displayTitle = activeTranslation?.title || hit.title;
  const displayRationale = activeTranslation?.rationale || hit.rationale || hit.scope;
  const displayScope = activeTranslation?.scope || hit.scope;
  const displayCertLabel = activeTranslation?.certification_label;

  const isMandatoryQCO = hit.qco_rules && hit.qco_rules.length > 0 && hit.qco_rules[0].is_mandatory;
  const qcoDetails = isMandatoryQCO ? hit.qco_rules[0] : null;

  const handleCopyCode = () => {
    navigator.clipboard.writeText(hit.is_code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const REGIONAL_LANG_TOGGLES = {
    mr: 'मराठीत पहा',
    hi: 'हिन्दी में देखें',
    ta: 'தமிழில் காண்க',
    te: 'తెలుగులో చూడండి',
    bn: 'বাংলায় দেখুন',
    gu: 'ગુજરાતીમાં જુઓ',
    kn: 'ಕನ್ನಡದಲ್ಲಿ ನೋಡಿ',
  };

  const REGIONAL_MATCH_LABELS = {
    mr: 'उच्च सुसंगतता (High Match)',
    hi: 'उच्च सुसंगतता (High Match)',
    ta: 'உயர் பொருத்தம் (High Match)',
    te: 'అధిక అనుకూలత (High Match)',
    bn: 'উচ্চ সামঞ্জস্য (High Match)',
    gu: 'ઉચ્ચ સુસંગતતા (High Match)',
    kn: 'ಹೆಚ್ಚಿನ ಹೊಂದಾಣಿಕೆ (High Match)',
  };

  const REGIONAL_SEMANTIC_HEADINGS = {
    mr: 'अर्थबोध आणि कार्यक्षेत्र सुसंगतता (Semantic Match)',
    hi: 'अर्थबोध एवं कार्यक्षेत्र सुसंगतता (Semantic Match)',
    ta: 'பொருள் புரிதல் மற்றும் நோக்கம் பொருத்தம் (Semantic Match)',
    te: 'అర్థ వివరణ మరియు పరిధి అనుకూలత (Semantic Match)',
    bn: 'অর্থবোধ ও ক্ষেত্র সামঞ্জস্য (Semantic Match)',
    gu: 'અર્થબોધ અને કાર્યક્ષેત્ર સુસંગતતા (Semantic Match)',
    kn: 'ಅರ್ಥ ವಿವರಣೆ ಮತ್ತು ವ್ಯಾಪ್ತಿ ಹೊಂದಾಣಿಕೆ (Semantic Match)',
  };

  const getRelevanceLabel = () => {
    if (isLocalized && REGIONAL_MATCH_LABELS[displayLanguage]) {
      return REGIONAL_MATCH_LABELS[displayLanguage];
    }
    if (hit.confidence === 'HIGH') return 'High Semantic Match';
    if (hit.confidence === 'MEDIUM') return 'Moderate Semantic Match';
    return 'Related Parameter Match';
  };

  const renderRelevanceMeter = () => {
    let bars = 1;
    let color = '#9ca3af'; // gray-400
    let label = 'Related to your search';
    
    if (hit.confidence === 'HIGH') {
      bars = 3;
      color = '#10b981'; // emerald-500
      label = 'High relevance';
    } else if (hit.confidence === 'MEDIUM') {
      bars = 2;
      color = '#f59e0b'; // amber-500
      label = 'Moderate relevance';
    }

    if (isLocalized && REGIONAL_MATCH_LABELS[displayLanguage]) {
      return REGIONAL_MATCH_LABELS[displayLanguage];
      label = REGIONAL_MATCH_LABELS[displayLanguage];
    }
    if (hit.confidence === 'HIGH') return 'High Semantic Match';
    if (hit.confidence === 'MEDIUM') return 'Moderate Semantic Match';
    return 'Related Parameter Match';

    return (
      <div style={{ display: 'flex', alignItems: 'center', background: '#f8fafc', padding: '4px 8px', borderRadius: '12px', border: '1px solid #e2e8f0' }} title={`Confidence: ${hit.confidence}`}>
        <div style={{ display: 'flex', gap: '2px', alignItems: 'flex-end', height: '12px' }}>
          <div style={{ width: '4px', height: '6px', backgroundColor: bars >= 1 ? color : '#e5e7eb', borderRadius: '1px' }} />
          <div style={{ width: '4px', height: '9px', backgroundColor: bars >= 2 ? color : '#e5e7eb', borderRadius: '1px' }} />
          <div style={{ width: '4px', height: '12px', backgroundColor: bars >= 3 ? color : '#e5e7eb', borderRadius: '1px' }} />
        </div>
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginLeft: '6px' }}>
          {label}
        </span>
      </div>
    );
  };

  const isActive = hit.status === 'ACTIVE';
  const isHallmarking = qcoDetails && (qcoDetails.scheme_type?.includes('Scheme-IV') || qcoDetails.scheme_type?.includes('Hallmark'));
  const isCRS = qcoDetails && (qcoDetails.scheme_type?.includes('Scheme-II') || qcoDetails.scheme_type?.includes('CRS'));

  // Group Allied Standards by Category (Feature 3)
  const alliedList = hit.allied_standards || [];
  const normTests = alliedList.filter((a) => a.relation_type === 'NORM_TEST');
  const safetyNorms = alliedList.filter((a) => a.relation_type === 'SAFETY');
  const installNorms = alliedList.filter((a) => a.relation_type === 'INSTALLATION');
  const termNorms = alliedList.filter((a) => a.relation_type === 'TERMINOLOGY');
  const relatedProds = alliedList.filter(
    (a) => !['NORM_TEST', 'SAFETY', 'INSTALLATION', 'TERMINOLOGY'].includes(a.relation_type)
  );

  return (
    <article className={`standard-card ${isActive ? 'active-standard' : 'superseded-standard'}`}>
      {/* Top Row: Code Pill + Semantic Badge + Version Badges (Features 2 & 4) */}
      <div className="card-top-row">
        <div className="is-code-title-wrap">
          <span className="is-code-pill">{hit.is_code}</span>
          <span className={`badge ${hit.confidence === 'HIGH' ? 'badge-emerald' : 'badge-amber'}`}>
            🧠 {getRelevanceLabel()}
          </span>
          {renderRelevanceMeter()}
          {hit.schedule_category && (
            <span className="badge badge-category">{hit.schedule_category}</span>
          )}
        </div>

        <div className="header-badges-wrap">
          {displayLanguage !== 'en' && hit.translations?.[displayLanguage] && (
            <button
              type="button"
              className="btn-card-lang-toggle"
              onClick={() => setShowOriginalEnglish(!showOriginalEnglish)}
              title="Toggle between localized regional text and official English"
            >
              <span>🌐</span>
              <span>
                {showOriginalEnglish
                  ? (REGIONAL_LANG_TOGGLES[displayLanguage] || 'Regional View')
                  : 'Official English'}
              </span>
            </button>
          )}

          {(() => {
            const ec = hit.edition_context;
            if (!ec) {
              return isActive ? (
                <span className="badge badge-neutral" title="Present in the registry snapshot."><span>In registry</span></span>
              ) : null;
            }
            if (ec.state === 'later_edition_exists') {
              return (
                <button 
                  className="badge badge-amber" 
                  title="Derived from editions present in the registry snapshot. Not a BIS currency determination — confirm at standardsbis.bsbedge.com."
                  onClick={(e) => { e.stopPropagation(); if (onSearch) onSearch(ec.later_edition_available); }}
                  style={{ cursor: 'pointer', border: 'none', background: '#fef3c7', color: '#92400e' }}
                >
                  <span>Later edition in registry: {ec.later_edition_available}</span>
                  <span>Later edition in registry: <span style={{ fontFamily: 'var(--font-mono)' }}>{ec.later_edition_available}</span></span>
                </button>
              );
            }
            if (ec.state === 'restructured_edition_exists') {
              return (
                <button 
                  className="badge badge-amber" 
                  title="Derived from editions present in the registry snapshot. Not a BIS currency determination — confirm at standardsbis.bsbedge.com."
                  onClick={(e) => { e.stopPropagation(); if (onSearch) onSearch(ec.later_edition_available); }}
                  style={{ cursor: 'pointer', border: 'none', background: '#fef3c7', color: '#92400e' }}
                >
                  <span>Restructured as: <span style={{ fontFamily: 'var(--font-mono)' }}>{ec.later_edition_available}</span></span>
                </button>
              );
            }
            if (ec.state === 'latest_in_registry') {
              return (
                <span className="badge badge-neutral" title="Derived from editions present in the registry snapshot. Not a BIS currency determination — confirm at standardsbis.bsbedge.com.">
                  <span>Latest edition in registry</span>
                </span>
              );
            }
            return (
              <span className="badge badge-neutral" title="Derived from editions present in the registry snapshot. Not a BIS currency determination — confirm at standardsbis.bsbedge.com.">
                <span>Edition not recorded</span>
              </span>
            );
          })()}

          {!isActive && (
            <span className="badge badge-amber" title="Recorded as superseded in the registry snapshot">
              <AlertTriangle size={12} />
              <span>Superseded {hit.superseded_by ? `(by ${hit.superseded_by})` : ''}</span>
              <span>Superseded {hit.superseded_by ? <>(by <span style={{ fontFamily: 'var(--font-mono)' }}>{hit.superseded_by}</span>)</> : ''}</span>
            </span>
          )}

          {/* Amendment counts are not sourced from any BIS amendment document; never show a number. */}
          <span className="badge badge-neutral" title="The registry snapshot carries no verified amendment source. Check the BIS portal for gazetted amendments.">
            <span>Amendment status not recorded</span>
          </span>
        </div>
      </div>

      {/* Standard Title */}
      <h3 className="standard-full-title">{displayTitle}</h3>

      {/* Superseded Warning Banner (Feature 4) */}
      {!isActive && (
        <div className="superseded-alert-box">
          <AlertTriangle size={15} flexShrink={0} />
          <div>
            <strong>Historical / Superseded Standard:</strong> This standard has been superseded by{' '}
            <strong>{hit.superseded_by || 'an updated standard'}</strong>. Public tenders should cite the latest active version.
          </div>
        </div>
      )}

      {/* Government Schedule Match */}
      {hit.is_government_schedule_match && (
        <div className="schedule-banner">
          <div>
            <strong>🏛️ CPWD / GeM Schedule Verified:</strong>{' '}
            <span>{hit.schedule_item_title || 'Matches Public Procurement Specification'}</span>
          </div>
          {hit.matched_grade && (
            <span className="badge badge-emerald">Grade: {hit.matched_grade}</span>
          )}
        </div>
      )}

      {/* Mandatory Certification Requirement (Feature 5) */}
      {isMandatoryQCO && qcoDetails ? (
        <div className={`qco-ribbon ${isHallmarking ? 'qco-ribbon-gold' : isCRS ? 'qco-ribbon-blue' : ''}`}>
          {isHallmarking ? <Award size={15} flexShrink={0} /> : isCRS ? <Zap size={15} flexShrink={0} /> : <ShieldAlert size={15} flexShrink={0} />}
          <span>
            <strong>
              {displayCertLabel || (
                isHallmarking
                  ? 'MANDATORY BIS HALLMARKING (Scheme-IV with 6-digit HUID):'
                  : isCRS
                  ? 'MANDATORY COMPULSORY REGISTRATION SCHEME (Scheme-II CRS):'
                  : 'MANDATORY BIS PRODUCT CERTIFICATION (Scheme-I ISI Mark):'
              )}
            </strong>{' '}
            {qcoDetails.compliance_warning || `Mandatory certification under ${qcoDetails.scheme_type || 'Scheme-I (ISI Mark)'} per BIS Act, 2016.`}
          </span>
        </div>
      ) : (
        <div className="voluntary-conformance-tag">
          <ShieldCheck size={14} color="#10b981" />
          <span>
            <strong>
              {displayCertLabel || 'Voluntary BIS Conformance:'}
            </strong>{' '}
            {!isLocalized ? 'No mandatory QCO notified. Quality compliance verifiable via manufacturer test certificates (GFR 2017 Rule 144 compliant).' : ''}
          </span>
        </div>
      )}

      {/* Semantic Understanding & Technical Justification (Feature 2) */}
      <div className="why-relevant-box">
        <div className="why-relevant-title">
          <span>
            🧠 {isLocalized && REGIONAL_SEMANTIC_HEADINGS[displayLanguage]
              ? REGIONAL_SEMANTIC_HEADINGS[displayLanguage]
              : 'Semantic Understanding & Scope Match'}
          </span>
        </div>
        <div className="why-relevant-text">
          {displayRationale}
        </div>
      </div>

      {/* Allied Standards Categorization Group (Feature 3) */}
      <div className="card-footer-bar">
        <div className="allied-categories-container">
          {alliedList.length === 0 ? (
            <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
              Self-contained specification (no separate normative references required)
            </div>
          ) : (
            <>
              {normTests.length > 0 && (
                <div className="allied-cat-row">
                  <span className="allied-cat-label">🧪 Test Methods:</span>
                  {normTests.slice(0, 3).map((a, i) => (
                    <span
                      key={i}
                      className="allied-tag allied-tag-test allied-clickable-tag"
                      title={`Normative Test Method: ${a.title || a.label}`}
                      onClick={() => onViewDetails(hit)}
                    >
                      {a.target_is_code}
                    </span>
                  ))}
                  {normTests.length > 3 && (
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>+{normTests.length - 3} more</span>
                  )}
                </div>
              )}

              {safetyNorms.length > 0 && (
                <div className="allied-cat-row">
                  <span className="allied-cat-label">🛡️ Safety Norms:</span>
                  {safetyNorms.slice(0, 3).map((a, i) => (
                    <span
                      key={i}
                      className="allied-tag allied-tag-safety allied-clickable-tag"
                      title={`Safety Standard: ${a.title || a.label}`}
                      onClick={() => onViewDetails(hit)}
                    >
                      {a.target_is_code}
                    </span>
                  ))}
                </div>
              )}

              {installNorms.length > 0 && (
                <div className="allied-cat-row">
                  <span className="allied-cat-label">🛠️ Installation:</span>
                  {installNorms.slice(0, 3).map((a, i) => (
                    <span
                      key={i}
                      className="allied-tag allied-tag-install allied-clickable-tag"
                      title={`Installation & Workmanship: ${a.title || a.label}`}
                      onClick={() => onViewDetails(hit)}
                    >
                      {a.target_is_code}
                    </span>
                  ))}
                </div>
              )}

              {termNorms.length > 0 && (
                <div className="allied-cat-row">
                  <span className="allied-cat-label">📖 Terminology:</span>
                  {termNorms.slice(0, 2).map((a, i) => (
                    <span
                      key={i}
                      className="allied-tag allied-tag-terms allied-clickable-tag"
                      title={`Terminology Standard: ${a.title || a.label}`}
                      onClick={() => onViewDetails(hit)}
                    >
                      {a.target_is_code}
                    </span>
                  ))}
                </div>
              )}

              {relatedProds.length > 0 && (
                <div className="allied-cat-row">
                  <span className="allied-cat-label">🔗 Related Standards:</span>
                  {relatedProds.slice(0, 3).map((a, i) => (
                    <span
                      key={i}
                      className="allied-tag allied-clickable-tag"
                      title={`Related Product Standard: ${a.title || a.label}`}
                      onClick={() => onViewDetails(hit)}
                    >
                      {a.target_is_code}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Action Buttons */}
        <div className="card-actions" style={{ marginTop: '0.6rem', alignSelf: 'flex-end' }}>
          <button
            className="btn-action-outline"
            onClick={handleCopyCode}
            title="Copy standard code to clipboard"
          >
            {copiedCode ? <Check size={13} color="#059669" /> : <Copy size={13} />}
            <span>{copiedCode ? 'Copied' : 'Copy Code'}</span>
          </button>

          <button
            className="btn-action-outline"
            onClick={() => onViewDetails(hit)}
            title="View full standard scope, amendments, and allied standards tree"
          >
            <Info size={13} />
            <span>View Details</span>
          </button>

          <button
            className="btn-action-primary"
            onClick={() => onOpenGeMClause(hit.is_code)}
            title="Generate ready-to-paste GeM specification clause"
          >
            <FileText size={13} />
            <span>GeM Clause</span>
          </button>
        </div>
      </div>
    </article>
  );
}
