import React, { useState } from 'react';
import { X, Copy, Check, FileText, AlertTriangle, ShieldCheck, ShieldAlert, BookOpen, ExternalLink, Award, CheckCircle2, Zap } from 'lucide-react';

export default function StandardDetailsModal({ isOpen, onClose, standard, onOpenGeMClause, displayLanguage: propLang }) {
  const [copied, setCopied] = useState(false);
  const [activeSection, setActiveSection] = useState('overview');
  const [showOriginalEnglish, setShowOriginalEnglish] = useState(false);

  const displayLanguage = propLang || (() => {
    try {
      return localStorage.getItem('is_display_language') || 'en';
    } catch {
      return 'en';
    }
  })();

  if (!isOpen || !standard) return null;

  const isLocalized = displayLanguage !== 'en' && !showOriginalEnglish && standard.translations && standard.translations[displayLanguage];
  const activeTranslation = isLocalized ? standard.translations[displayLanguage] : null;

  const displayTitle = activeTranslation?.title || standard.title;
  const displayScope = activeTranslation?.scope || standard.scope;
  const displayRationale = activeTranslation?.rationale || standard.rationale || standard.scope;

  const REGIONAL_LANG_TOGGLES = {
    mr: 'मराठीत पहा',
    hi: 'हिन्दी में देखें',
    ta: 'தமிழில் காண்க',
    te: 'తెలుగులో చూడండి',
    bn: 'বাংলায় দেখুন',
    gu: 'ગુજરાતીમાં જુઓ',
    kn: 'ಕನ್ನಡದಲ್ಲಿ ನೋಡಿ',
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(standard.is_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isSuperseded = standard.status !== 'ACTIVE';
  const isMandatoryQCO = standard.qco_rules && standard.qco_rules.length > 0 && standard.qco_rules[0].is_mandatory;
  const qco = isMandatoryQCO ? standard.qco_rules[0] : null;

  const isHallmarking = qco && (qco.scheme_type?.includes('Scheme-IV') || qco.scheme_type?.includes('Hallmark'));
  const isCRS = qco && (qco.scheme_type?.includes('Scheme-II') || qco.scheme_type?.includes('CRS'));

  // Group Allied Standards by Category (Feature 3)
  const alliedList = standard.allied_standards || [];
  const normTests = alliedList.filter((a) => a.relation_type === 'NORM_TEST');
  const safetyNorms = alliedList.filter((a) => a.relation_type === 'SAFETY');
  const installNorms = alliedList.filter((a) => a.relation_type === 'INSTALLATION');
  const termNorms = alliedList.filter((a) => a.relation_type === 'TERMINOLOGY');
  const relatedProds = alliedList.filter(
    (a) => !['NORM_TEST', 'SAFETY', 'INSTALLATION', 'TERMINOLOGY'].includes(a.relation_type)
  );

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <span className="badge badge-blue">Indian Standard</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--primary-navy)' }}>
              {standard.is_code}
            </span>
            {displayLanguage !== 'en' && standard.translations?.[displayLanguage] && (
              <button
                type="button"
                className="btn-card-lang-toggle"
                onClick={() => setShowOriginalEnglish(!showOriginalEnglish)}
                style={{ marginLeft: '0.5rem' }}
              >
                <span>🌐</span>
                <span>
                  {showOriginalEnglish
                    ? (REGIONAL_LANG_TOGGLES[displayLanguage] || 'Regional View')
                    : 'Official English'}
                </span>
              </button>
            )}
            {standard.status === 'ACTIVE' ? (
              <span className="badge badge-emerald">
                <CheckCircle2 size={12} />
                ACTIVE {standard.reaffirmation_year ? `(Reaffirmed ${standard.reaffirmation_year})` : ''}
              </span>
            ) : (
              <span className="badge badge-amber">
                <AlertTriangle size={12} />
                SUPERSEDED {standard.superseded_by ? `(by ${standard.superseded_by})` : ''}
              </span>
            )}
            {/* No verified amendment source exists in the registry snapshot; never show a count. */}
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close standard details">
            <X size={18} />
          </button>
        </div>

        {/* Older / Superseded Standard Notice (Feature 4) */}
        {isSuperseded && (
          <div style={{
            background: '#fffbeb',
            borderBottom: '1px solid #fde68a',
            padding: '0.75rem 1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            fontSize: '0.82rem',
            color: '#92400e'
          }}>
            <AlertTriangle size={16} flexShrink={0} />
            <div>
              <strong>Advisory:</strong> This is a historical or superseded standard in the national archive.
              {standard.superseded_by ? (
                <span> It has been formally superseded by <strong>{standard.superseded_by}</strong>. Public procurement tenders must cite the updated standard <strong>{standard.superseded_by}</strong>.</span>
              ) : (
                <span> Please verify whether an updated revision or amendment has been gazetted.</span>
              )}
            </div>
          </div>
        )}

        {/* Navigation Sub-Tabs */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid var(--border-color)',
          background: '#ffffff',
          padding: '0 1.5rem',
          flexWrap: 'wrap'
        }}>
          {[
            { id: 'overview', label: 'Overview & Edition' },
            { id: 'rationale', label: '🧠 Semantic Scope Match' },
            { id: 'qco', label: 'Mandatory Certification Status' },
            { id: 'allied', label: `Allied Standards (${alliedList.length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id)}
              style={{
                padding: '0.75rem 1rem',
                fontSize: '0.85rem',
                fontWeight: activeSection === tab.id ? 600 : 500,
                color: activeSection === tab.id ? 'var(--primary-blue)' : 'var(--text-secondary)',
                borderBottom: activeSection === tab.id ? '2px solid var(--primary-blue)' : '2px solid transparent',
                background: 'transparent',
                borderTop: 'none',
                borderLeft: 'none',
                borderRight: 'none',
                cursor: 'pointer',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {activeSection === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '0.4rem' }}>
                  {displayTitle}
                </h3>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                  {standard.schedule_category && (
                    <span className="badge badge-category">Division: {standard.schedule_category}</span>
                  )}
                  <span className="badge badge-emerald">
                    Published Edition: {standard.is_code}
                  </span>
                  {standard.reaffirmation_year && (
                    <span className="badge badge-blue">Reaffirmed Year: {standard.reaffirmation_year}</span>
                  )}
                  <span className="badge badge-neutral">Amendment status not recorded</span>
                </div>
              </div>

              <div>
                <div className="modal-section-title">Standard Scope & Technical Coverage</div>
                <div className="modal-text-box">
                  {displayScope || 'Covers materials, physical requirements, manufacturing methods, testing procedures, sampling guidelines and compliance criteria under Bureau of Indian Standards.'}
                </div>
              </div>

              {standard.is_government_schedule_match && (
                <div className="schedule-banner">
                  <div>
                    <strong>🏛️ CPWD / GeM Schedule Verified:</strong>{' '}
                    <span>{standard.schedule_item_title || 'Government Procurement Schedule Match'}</span>
                  </div>
                  {standard.matched_grade && (
                    <span className="badge badge-emerald">Grade: {standard.matched_grade}</span>
                  )}
                </div>
              )}
            </div>
          )}

          {activeSection === 'rationale' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <div className="modal-section-title">Semantic Neural Match Rationale</div>
                <div className="modal-text-box" style={{ background: '#eff6ff', borderColor: '#bfdbfe', color: '#1e3a8a' }}>
                  {displayRationale}
                </div>
              </div>

              <div>
                <div className="modal-section-title">GFR 2017 Rule 144 Conformance</div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  Under Rule 144 of the General Financial Rules (2017), government entities must base technical specifications on national standards (BIS). Citing <strong>{standard.is_code}</strong> ensures non-restrictive competitive bidding while legally securing certified quality.
                </p>
              </div>
            </div>
          )}

          {activeSection === 'qco' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {isMandatoryQCO && qco ? (
                <div className={`qco-box ${isHallmarking ? 'qco-box-gold' : ''}`}>
                  <div className="qco-box-header">
                    {isHallmarking ? <Award size={18} /> : isCRS ? <Zap size={18} /> : <ShieldAlert size={18} />}
                    <span>
                      {isHallmarking
                        ? 'MANDATORY BIS HALLMARKING (Scheme-IV with 6-digit HUID)'
                        : isCRS
                        ? 'MANDATORY COMPULSORY REGISTRATION SCHEME (Scheme-II CRS)'
                        : 'MANDATORY BIS PRODUCT CERTIFICATION (Scheme-I ISI Mark)'}
                    </span>
                  </div>
                  <div className="qco-box-content" style={{ marginBottom: '0.75rem' }}>
                    {qco.compliance_warning || 'This standard is notified under a mandatory Quality Control Order (QCO) issued under Section 16 of the BIS Act, 2016. Supply of uncertified goods is prohibited by law.'}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.6rem', fontSize: '0.82rem', color: isHallmarking ? '#78350f' : '#854d0e', background: 'rgba(255,255,255,0.7)', padding: '0.6rem', borderRadius: 'var(--radius-sm)' }}>
                    <div><strong>Scheme:</strong> {qco.scheme_type || 'Scheme-I (ISI Mark)'}</div>
                    {qco.ministry && <div><strong>Ministry:</strong> {qco.ministry}</div>}
                    {qco.order_name && <div><strong>Order:</strong> {qco.order_name}</div>}
                  </div>
                </div>
              ) : (
                <div style={{ background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '1.25rem', textAlign: 'center' }}>
                  <ShieldCheck size={32} color="#10b981" style={{ margin: '0 auto 0.5rem' }} />
                  <h4 style={{ fontSize: '0.98rem', fontWeight: 600, color: 'var(--primary-navy)', marginBottom: '0.25rem' }}>
                    Voluntary BIS Conformance (GFR 2017 Rule 144)
                  </h4>
                  <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                    No mandatory Quality Control Order (QCO) is currently enforced for this specific standard. Conformity may be required in tender specifications to guarantee standardized engineering performance.
                  </p>
                </div>
              )}
            </div>
          )}

          {activeSection === 'allied' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="modal-section-title">
                Allied & Normative Reference Standards ({alliedList.length})
              </div>

              {alliedList.length === 0 ? (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  This is a self-contained standard specification without separate normative references.
                </p>
              ) : (
                <>
                  {/* Category 1: Test Methods */}
                  {normTests.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span>🧪</span> Normative Test Methods & Sampling Procedures ({normTests.length})
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                        {normTests.map((a, idx) => (
                          <div key={idx} style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 'var(--radius-sm)', padding: '0.6rem 0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <strong style={{ fontFamily: 'var(--font-mono)', color: '#166534', fontSize: '0.88rem' }}>{a.target_is_code}</strong>
                              <span style={{ fontSize: '0.8rem', color: '#14532d', marginLeft: '0.5rem' }}>{a.title || 'Normative Test Standard'}</span>
                            </div>
                            <span className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>Test Method</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Category 2: Safety Standards */}
                  {safetyNorms.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span>🛡️</span> Safety & Protection Standards ({safetyNorms.length})
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                        {safetyNorms.map((a, idx) => (
                          <div key={idx} style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 'var(--radius-sm)', padding: '0.6rem 0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <strong style={{ fontFamily: 'var(--font-mono)', color: '#991b1b', fontSize: '0.88rem' }}>{a.target_is_code}</strong>
                              <span style={{ fontSize: '0.8rem', color: '#7f1d1d', marginLeft: '0.5rem' }}>{a.title || 'Safety & Protection Standard'}</span>
                            </div>
                            <span className="badge badge-amber" style={{ fontSize: '0.7rem' }}>Safety Standard</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Category 3: Installation Standards */}
                  {installNorms.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span>🛠️</span> Installation & Workmanship Standards ({installNorms.length})
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                        {installNorms.map((a, idx) => (
                          <div key={idx} style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 'var(--radius-sm)', padding: '0.6rem 0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <strong style={{ fontFamily: 'var(--font-mono)', color: '#1e40af', fontSize: '0.88rem' }}>{a.target_is_code}</strong>
                              <span style={{ fontSize: '0.8rem', color: '#1e3a8a', marginLeft: '0.5rem' }}>{a.title || 'Installation Code of Practice'}</span>
                            </div>
                            <span className="badge badge-blue" style={{ fontSize: '0.7rem' }}>Installation</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Category 4: Terminology Standards */}
                  {termNorms.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span>📖</span> Terminology & Nomenclature Standards ({termNorms.length})
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                        {termNorms.map((a, idx) => (
                          <div key={idx} style={{ background: '#f5f3ff', border: '1px solid #ddd6fe', borderRadius: 'var(--radius-sm)', padding: '0.6rem 0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <strong style={{ fontFamily: 'var(--font-mono)', color: '#5b21b6', fontSize: '0.88rem' }}>{a.target_is_code}</strong>
                              <span style={{ fontSize: '0.8rem', color: '#4c1d95', marginLeft: '0.5rem' }}>{a.title || 'Glossary of Terms'}</span>
                            </div>
                            <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>Terminology</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Category 5: Related Products */}
                  {relatedProds.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span>🔗</span> Related Product & Raw Material Standards ({relatedProds.length})
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                        {relatedProds.map((a, idx) => (
                          <div key={idx} style={{ background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '0.6rem 0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary-navy)', fontSize: '0.88rem' }}>{a.target_is_code}</strong>
                              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>{a.title || 'Related Specification'}</span>
                            </div>
                            <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>Related Product</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <button className="btn-action-outline" onClick={handleCopyCode}>
            {copied ? <Check size={14} color="#059669" /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy IS Code'}</span>
          </button>

          <div style={{ display: 'flex', gap: '0.6rem' }}>
            <button
              className="btn-action-primary"
              onClick={() => {
                onClose();
                onOpenGeMClause(standard.is_code);
              }}
            >
              <FileText size={14} />
              <span>Draft GeM Clause</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
