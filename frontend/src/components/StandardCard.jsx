import React, { useState } from 'react';
import { ShieldAlert, AlertTriangle, FileText, Copy, Check, Info, Award, Zap, ShieldCheck, Globe2, Landmark, FlaskConical, Wrench, BookOpen, Link2, Brain } from 'lucide-react';
import Seal from './Seal';
import { useLanguage } from '../i18n';

export default function StandardCard({ hit, onOpenGeMClause, onViewDetails, onSearch }) {
  const { lang: displayLanguage, t } = useLanguage();
  const [copiedCode, setCopiedCode] = useState(false);
  const [showOriginalEnglish, setShowOriginalEnglish] = useState(false);

  const isLocalized = displayLanguage !== 'en' && !showOriginalEnglish && hit.translations && hit.translations[displayLanguage];
  const activeTranslation = isLocalized ? hit.translations[displayLanguage] : null;

  const displayTitle = activeTranslation?.title || hit.title;
  const displayRationale = activeTranslation?.rationale || hit.rationale || hit.scope;
  const displayCertLabel = activeTranslation?.certification_label;

  const isMandatoryQCO = hit.qco_rules && hit.qco_rules.length > 0 && hit.qco_rules[0].is_mandatory;
  const qcoDetails = isMandatoryQCO ? hit.qco_rules[0] : null;

  const handleCopyCode = () => {
    navigator.clipboard.writeText(hit.is_code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const REGIONAL_LANG_TOGGLES = {
    mr: 'मराठीत पहा', hi: 'हिन्दी में देखें', ta: 'தமிழில் காண்க', te: 'తెలుగులో చూడండి',
    bn: 'বাংলায় দেখুন', gu: 'ગુજરાતીમાં જુઓ', kn: 'ಕನ್ನಡದಲ್ಲಿ ನೋಡಿ',
  };
  const REGIONAL_MATCH_LABELS = {
    mr: 'उच्च सुसंगतता', hi: 'उच्च सुसंगतता', ta: 'உயர் பொருத்தம்', te: 'అధిక అనుకూలత',
    bn: 'উচ্চ সামঞ্জস্য', gu: 'ઉચ્ચ સુસંગતતા', kn: 'ಹೆಚ್ಚಿನ ಹೊಂದಾಣಿಕೆ',
  };
  const REGIONAL_SEMANTIC_HEADINGS = {
    mr: 'अर्थबोध आणि व्याप्ती सुसंगतता', hi: 'अर्थबोध एवं कार्यक्षेत्र सुसंगतता', ta: 'பொருள் புரிதல் மற்றும் நோக்கம்',
    te: 'అర్థ వివరణ మరియు పరిధి', bn: 'অর্থবোধ ও ক্ষেত্র সামঞ্জস্য', gu: 'અર્થબોધ અને કાર્યક્ષેત્ર', kn: 'ಅರ್ಥ ವಿವರಣೆ',
  };

  const tier = hit.confidence === 'HIGH' ? 'high' : hit.confidence === 'MEDIUM' ? 'medium' : 'low';

  const getRelevanceLabel = () => {
    if (isLocalized && REGIONAL_MATCH_LABELS[displayLanguage]) return REGIONAL_MATCH_LABELS[displayLanguage];
    if (hit.confidence === 'HIGH') return t('match_high');
    if (hit.confidence === 'MEDIUM') return t('match_medium');
    return t('match_related');
  };

  const isActive = hit.status === 'ACTIVE';
  const isHallmarking = qcoDetails && (qcoDetails.scheme_type?.includes('Scheme-IV') || qcoDetails.scheme_type?.includes('Hallmark'));
  const isCRS = qcoDetails && (qcoDetails.scheme_type?.includes('Scheme-II') || qcoDetails.scheme_type?.includes('CRS'));

  const alliedList = hit.allied_standards || [];
  const normTests = alliedList.filter((a) => a.relation_type === 'NORM_TEST');
  const safetyNorms = alliedList.filter((a) => a.relation_type === 'SAFETY');
  const installNorms = alliedList.filter((a) => a.relation_type === 'INSTALLATION');
  const termNorms = alliedList.filter((a) => a.relation_type === 'TERMINOLOGY');
  const relatedProds = alliedList.filter((a) => !['NORM_TEST', 'SAFETY', 'INSTALLATION', 'TERMINOLOGY'].includes(a.relation_type));

  const renderEditionBadge = () => {
    const ec = hit.edition_context;
    const provenanceTitle = t('edition_provenance_title');
    if (!ec) {
      return isActive ? <span className="badge badge-neutral" title={t('badge_in_registry_title')}>{t('badge_in_registry')}</span> : null;
    }
    if (ec.state === 'later_edition_exists' || ec.state === 'restructured_edition_exists') {
      const label = ec.state === 'later_edition_exists' ? t('later_edition') : t('restructured_as');
      return (
        <button
          className="badge"
          title={provenanceTitle}
          onClick={(e) => { e.stopPropagation(); if (onSearch) onSearch(ec.later_edition_available); }}
        >
          <span>{label}: <span className="mono">{ec.later_edition_available}</span></span>
        </button>
      );
    }
    if (ec.state === 'latest_in_registry') {
      return <span className="badge badge-neutral" title={provenanceTitle}>{t('latest_in_registry')}</span>;
    }
    return <span className="badge badge-neutral" title={provenanceTitle}>{t('edition_not_recorded')}</span>;
  };

  const alliedGroups = [
    { list: normTests, label: t('allied_test'), icon: FlaskConical, cls: 'allied-tag-test' },
    { list: safetyNorms, label: t('allied_safety'), icon: ShieldAlert, cls: 'allied-tag-safety' },
    { list: installNorms, label: t('allied_install'), icon: Wrench, cls: 'allied-tag-install' },
    { list: termNorms, label: t('allied_terms'), icon: BookOpen, cls: 'allied-tag-terms' },
    { list: relatedProds, label: t('allied_related'), icon: Link2, cls: '' },
  ];

  return (
    <article className={`standard-card ${isActive ? 'active-standard' : 'superseded-standard'}`}>
      <div className="card-medallion-strip">
        <div className="is-code-title-wrap">
          <div className="card-seal-badge">
            <Seal tier={tier} size={46} title={`Confidence: ${hit.confidence}`} />
            <div>
              <div className="is-code-pill">{hit.is_code}</div>
              <div className={`relevance-label tier-${tier}`}>{getRelevanceLabel()}</div>
            </div>
          </div>
          {hit.schedule_category && <span className="badge badge-category">{hit.schedule_category}</span>}
        </div>

        <div className="header-badges-wrap">
          {displayLanguage !== 'en' && hit.translations?.[displayLanguage] && (
            <button type="button" className="btn-card-lang-toggle" onClick={() => setShowOriginalEnglish(!showOriginalEnglish)}
              title={t('lang_toggle_title')}>
              <Globe2 size={12} className="lang-glyph" />
              <span>{showOriginalEnglish ? (REGIONAL_LANG_TOGGLES[displayLanguage] || 'Regional view') : t('official_english')}</span>
            </button>
          )}
          {renderEditionBadge()}
          {!isActive && (
            <span className="badge badge-amber" title={t('superseded_title')}>
              <AlertTriangle size={12} />
              <span>{t('superseded')} {hit.superseded_by ? <>{t('by_paren_pre')}<span className="mono">{hit.superseded_by}</span>{t('by_paren_post')}</> : ''}</span>
            </span>
          )}
          <span className="badge badge-neutral" title={t('amendment_not_recorded_title')}>
            {t('amendment_not_recorded')}
          </span>
        </div>
      </div>

      <div className="card-body">
        <h3 className="standard-full-title">{displayTitle}</h3>

        {!isActive && (
          <div className="superseded-alert-box">
            <AlertTriangle size={15} />
            <div>
              <strong>{t('card_historical_label')}</strong> {t('card_historical_text', { by: hit.superseded_by || t('card_historical_fallback') })}
            </div>
          </div>
        )}

        {hit.is_government_schedule_match && (
          <div className="schedule-banner">
            <div><Landmark size={14} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '0.35rem' }} />
              <strong>{t('schedule_verified')}</strong> <span>{hit.schedule_item_title || t('schedule_fallback')}</span>
            </div>
            {hit.matched_grade && <span className="badge badge-emerald">{t('grade_label', { grade: hit.matched_grade })}</span>}
          </div>
        )}

        {isMandatoryQCO && qcoDetails ? (
          <div className={`qco-ribbon ${isHallmarking ? 'qco-ribbon-gold' : isCRS ? 'qco-ribbon-blue' : ''}`}>
            {isHallmarking ? <Award size={15} /> : isCRS ? <Zap size={15} /> : <ShieldAlert size={15} />}
            <span>
              <strong>
                {displayCertLabel || (isHallmarking ? t('qco_hallmark_label') : isCRS ? t('qco_crs_label') : t('qco_isi_label'))}
              </strong>{' '}
              {qcoDetails.compliance_warning || t('qco_compliance_fallback', { scheme: qcoDetails.scheme_type || 'Scheme-I (ISI Mark)' })}
            </span>
          </div>
        ) : (
          <div className="voluntary-conformance-tag">
            <ShieldCheck size={14} />
            <span>
              <strong>{displayCertLabel || t('voluntary_label')}</strong>{' '}
              {!isLocalized ? t('voluntary_text') : ''}
            </span>
          </div>
        )}

        <div className="why-relevant-box">
          <div className="why-relevant-title">
            <Brain size={13} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '0.3rem' }} />
            {isLocalized && REGIONAL_SEMANTIC_HEADINGS[displayLanguage] ? REGIONAL_SEMANTIC_HEADINGS[displayLanguage] : t('semantic_heading')}
          </div>
          <div className="why-relevant-text">{displayRationale}</div>
        </div>

        <div className="card-footer-bar">
          <div className="allied-categories-container">
            {alliedList.length === 0 ? (
              <div className="allied-self-contained">{t('allied_self_contained')}</div>
            ) : (
              alliedGroups.filter((g) => g.list.length > 0).map((g) => (
                <div className="allied-cat-row" key={g.label}>
                  <span className="allied-cat-label"><g.icon size={12} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '0.25rem' }} />{g.label}:</span>
                  {g.list.slice(0, 3).map((a, i) => (
                    <span key={i} className={`allied-tag allied-clickable-tag ${g.cls}`} title={a.title || a.label} onClick={() => onViewDetails(hit)}>
                      {a.target_is_code}
                    </span>
                  ))}
                  {g.list.length > 3 && <span className="allied-more">{t('more_count', { n: g.list.length - 3 })}</span>}
                </div>
              ))
            )}
          </div>

          <div className="card-actions">
            <button className="btn-action-outline" onClick={handleCopyCode} title={t('copy_code_title')}>
              {copiedCode ? <Check size={13} /> : <Copy size={13} />}
              <span>{copiedCode ? t('common_copied') : t('copy_code')}</span>
            </button>
            <button className="btn-action-outline" onClick={() => onViewDetails(hit)} title={t('view_details_title')}>
              <Info size={13} /><span>{t('view_details')}</span>
            </button>
            <button className="btn-action-primary" onClick={() => onOpenGeMClause(hit.is_code)} title={t('gem_clause_title')}>
              <FileText size={13} /><span>{t('gem_clause_btn')}</span>
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}
