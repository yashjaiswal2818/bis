import React, { useState, useEffect } from 'react';
import { X, Copy, Check, FileText, AlertTriangle, ShieldCheck, ShieldAlert, Globe2, Award, CheckCircle2, Zap, FlaskConical, Wrench, BookOpen, Link2, Landmark } from 'lucide-react';
import Seal from './Seal';
import { useLanguage } from '../i18n';

export default function StandardDetailsModal({ isOpen, onClose, standard, onOpenGeMClause }) {
  const { lang: displayLanguage, t } = useLanguage();
  const [copied, setCopied] = useState(false);
  const [activeSection, setActiveSection] = useState('overview');
  const [showOriginalEnglish, setShowOriginalEnglish] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  if (!isOpen || !standard) return null;

  const isLocalized = displayLanguage !== 'en' && !showOriginalEnglish && standard.translations && standard.translations[displayLanguage];
  const activeTranslation = isLocalized ? standard.translations[displayLanguage] : null;

  const displayTitle = activeTranslation?.title || standard.title;
  const displayScope = activeTranslation?.scope || standard.scope;
  const displayRationale = activeTranslation?.rationale || standard.rationale || standard.scope;

  const REGIONAL_LANG_TOGGLES = {
    mr: 'मराठीत पहा', hi: 'हिन्दी में देखें', ta: 'தமிழில் காண்க', te: 'తెలుగులో చూడండి',
    bn: 'বাংলায় দেখুন', gu: 'ગુજરાતીમાં જુઓ', kn: 'ಕನ್ನಡದಲ್ಲಿ ನೋಡಿ',
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

  const alliedList = standard.allied_standards || [];
  const normTests = alliedList.filter((a) => a.relation_type === 'NORM_TEST');
  const safetyNorms = alliedList.filter((a) => a.relation_type === 'SAFETY');
  const installNorms = alliedList.filter((a) => a.relation_type === 'INSTALLATION');
  const termNorms = alliedList.filter((a) => a.relation_type === 'TERMINOLOGY');
  const relatedProds = alliedList.filter((a) => !['NORM_TEST', 'SAFETY', 'INSTALLATION', 'TERMINOLOGY'].includes(a.relation_type));

  const alliedGroups = [
    { list: normTests, label: t('allied_test_full'), icon: FlaskConical, cls: 'allied-tag-test', chip: 'badge-emerald', tag: t('tag_test') },
    { list: safetyNorms, label: t('allied_safety_full'), icon: ShieldAlert, cls: 'allied-tag-safety', chip: 'badge-amber', tag: t('tag_safety') },
    { list: installNorms, label: t('allied_install_full'), icon: Wrench, cls: 'allied-tag-install', chip: 'badge-blue', tag: t('tag_install') },
    { list: termNorms, label: t('allied_terms_full'), icon: BookOpen, cls: 'allied-tag-terms', chip: 'badge-category', tag: t('tag_terms') },
    { list: relatedProds, label: t('allied_related_full'), icon: Link2, cls: '', chip: 'badge-neutral', tag: t('tag_related') },
  ];

  const TABS = [
    { id: 'overview', label: t('tab_overview') },
    { id: 'rationale', label: t('tab_rationale') },
    { id: 'qco', label: t('tab_qco') },
    { id: 'allied', label: t('tab_allied', { n: alliedList.length }) },
  ];

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <Seal tier={isSuperseded ? 'low' : 'high'} size={42} />
            <span className="mono" style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ink)' }}>{standard.is_code}</span>
            {displayLanguage !== 'en' && standard.translations?.[displayLanguage] && (
              <button type="button" className="btn-card-lang-toggle" onClick={() => setShowOriginalEnglish(!showOriginalEnglish)}>
                <Globe2 size={12} />
                <span>{showOriginalEnglish ? (REGIONAL_LANG_TOGGLES[displayLanguage] || 'Regional view') : t('official_english')}</span>
              </button>
            )}
            {standard.status === 'ACTIVE' ? (
              <span className="badge badge-emerald"><CheckCircle2 size={12} />{t('active_status')} {standard.reaffirmation_year ? t('reaffirmed_paren', { year: standard.reaffirmation_year }) : ''}</span>
            ) : (
              <span className="badge badge-amber"><AlertTriangle size={12} />{t('superseded_status')} {standard.superseded_by ? <>{t('by_paren_pre')}<span className="mono">{standard.superseded_by}</span>{t('by_paren_post')}</> : ''}</span>
            )}
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label={t('close_details')}><X size={18} /></button>
        </div>

        {isSuperseded && (
          <div className="modal-advisory">
            <AlertTriangle size={16} />
            <div>
              <strong>{t('advisory_label')}</strong> {t('advisory_verify')}{' '}
              {standard.superseded_by ? (
                t('advisory_superseded_by', { by: standard.superseded_by })
              ) : (
                t('advisory_no_successor')
              )}
            </div>
          </div>
        )}

        <div className="modal-tabs">
          {TABS.map((tab) => (
            <button key={tab.id} className={`modal-tab ${activeSection === tab.id ? 'active' : ''}`} onClick={() => setActiveSection(tab.id)}>
              {tab.label}
            </button>
          ))}
        </div>

        <div className="modal-body">
          {activeSection === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <h3 className="standard-full-title">{displayTitle}</h3>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                  {standard.schedule_category && <span className="badge badge-category">{t('division_label', { cat: standard.schedule_category })}</span>}
                  <span className="badge badge-emerald">{t('published_edition')} <span className="mono">{standard.is_code}</span></span>
                  {standard.reaffirmation_year && <span className="badge badge-blue">{t('reaffirmed_year', { year: standard.reaffirmation_year })}</span>}
                  <span className="badge badge-neutral">{t('amendment_not_recorded')}</span>
                </div>
              </div>

              <div>
                <div className="modal-section-title">{t('scope_heading')}</div>
                <div className="modal-text-box">
                  {displayScope || t('scope_fallback')}
                </div>
              </div>

              {standard.is_government_schedule_match && (
                <div className="schedule-banner">
                  <div><Landmark size={14} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '0.35rem' }} />
                    <strong>{t('schedule_verified')}</strong> <span>{standard.schedule_item_title || t('schedule_fallback_modal')}</span>
                  </div>
                  {standard.matched_grade && <span className="badge badge-emerald">{t('grade_label', { grade: standard.matched_grade })}</span>}
                </div>
              )}
            </div>
          )}

          {activeSection === 'rationale' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <div className="modal-section-title">{t('rationale_heading')}</div>
                <div className="modal-text-box" style={{ background: 'var(--seal-tint)', borderColor: 'var(--seal-tint-2)' }}>{displayRationale}</div>
              </div>
              <div>
                <div className="modal-section-title">{t('gfr_heading')}</div>
                <p style={{ fontSize: '0.85rem', color: 'var(--ink-secondary)', lineHeight: 1.6 }}>
                  {t('gfr_text_pre')}<strong className="mono">{standard.is_code}</strong>{t('gfr_text_post')}
                </p>
              </div>
            </div>
          )}

          {activeSection === 'qco' && (
            isMandatoryQCO && qco ? (
              <div className={`qco-box ${isHallmarking ? 'qco-box-gold' : ''}`}>
                <div className="qco-box-header">
                  {isHallmarking ? <Award size={18} /> : isCRS ? <Zap size={18} /> : <ShieldAlert size={18} />}
                  <span>{isHallmarking ? t('qco_hallmark_label_modal') : isCRS ? t('qco_crs_label_modal') : t('qco_isi_label_modal')}</span>
                </div>
                <div className="qco-box-content" style={{ marginBottom: '0.75rem' }}>
                  {qco.compliance_warning || t('qco_compliance_fallback_modal')}
                </div>
                <div className="qco-meta-grid">
                  <div><strong>{t('scheme_label')}</strong> {qco.scheme_type || 'Scheme-I (ISI Mark)'}</div>
                  {qco.ministry && <div><strong>{t('ministry_label')}</strong> {qco.ministry}</div>}
                  {qco.order_name && <div><strong>{t('order_label')}</strong> {qco.order_name}</div>}
                </div>
              </div>
            ) : (
              <div className="qco-voluntary-box">
                <ShieldCheck size={30} color="#1E6B4F" style={{ margin: '0 auto 0.6rem' }} />
                <h4 style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--ink)', marginBottom: '0.3rem' }}>{t('voluntary_modal_heading')}</h4>
                <p style={{ fontSize: '0.84rem', color: 'var(--ink-secondary)' }}>
                  {t('voluntary_modal_text')}
                </p>
              </div>
            )
          )}

          {activeSection === 'allied' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.4rem' }}>
              <div className="modal-section-title">{t('allied_heading', { n: alliedList.length })}</div>
              {alliedList.length === 0 ? (
                <p style={{ fontSize: '0.85rem', color: 'var(--ink-muted)' }}>{t('allied_none')}</p>
              ) : (
                alliedGroups.filter((g) => g.list.length > 0).map((g) => (
                  <div key={g.label}>
                    <h4 className="allied-group-title"><g.icon size={15} />{g.label} ({g.list.length})</h4>
                    <div className="allied-detail-list">
                      {g.list.map((a, idx) => (
                        <div key={idx} className="allied-detail-row">
                          <div>
                            <span className="allied-detail-code mono">{a.target_is_code}</span>
                            <span className="allied-detail-title">{a.title || t('is_spec_fallback')}</span>
                          </div>
                          <span className={`badge ${g.chip}`} style={{ fontSize: '0.7rem' }}>{g.tag}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-action-outline" onClick={handleCopyCode}>
            {copied ? <Check size={14} /> : <Copy size={14} />}<span>{copied ? t('common_copied') : t('copy_is_code')}</span>
          </button>
          <button className="btn-action-primary" onClick={() => { onClose(); onOpenGeMClause(standard.is_code); }}>
            <FileText size={14} /><span>{t('draft_gem_clause')}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
