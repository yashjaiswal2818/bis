import React, { useState } from 'react';
import { ShieldAlert, CheckCircle2, AlertTriangle, FileText, Copy, Check, Award, Zap } from 'lucide-react';

export default function StandardCard({ hit, onOpenGeMClause }) {
  const [copiedCode, setCopiedCode] = useState(false);

  const isMandatoryQCO = hit.qco_rules && hit.qco_rules.length > 0 && hit.qco_rules[0].is_mandatory;
  const qcoDetails = isMandatoryQCO ? hit.qco_rules[0] : null;

  const handleCopyCode = () => {
    navigator.clipboard.writeText(hit.is_code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const confidenceScore = Math.round((hit.rerank_score || 0) * 100);

  // Determine QCO badge styling by Scheme
  const isHallmarking = qcoDetails && (qcoDetails.scheme_type?.includes('Scheme-IV') || qcoDetails.scheme_type?.includes('Hallmark'));
  const isCRS = qcoDetails && (qcoDetails.scheme_type?.includes('Scheme-II') || qcoDetails.scheme_type?.includes('CRS'));

  return (
    <article className="standard-card">
      <div className="card-header">
        <div>
          <div className="is-code-title-row">
            <span className="badge badge-blue">#{hit.rank} Match</span>
            <span className="is-code-text">{hit.is_code}</span>
          </div>
          <h3 className="standard-full-title">{hit.title}</h3>
        </div>

        <div className="header-badges">
          {hit.status === 'ACTIVE' ? (
            <span
              className="badge badge-emerald"
              title={`Current active Indian Standard${hit.reaffirmation_year ? ` • Reaffirmed ${hit.reaffirmation_year}` : ''}`}
            >
              <CheckCircle2 size={12} />
              <span>ACTIVE {hit.reaffirmation_year ? `(${hit.reaffirmation_year})` : ''}</span>
            </span>
          ) : (
            <span className="badge badge-amber" title="Superseded standard - Check updated version">
              <AlertTriangle size={12} />
              <span>SUPERSEDED {hit.superseded_by ? `(by ${hit.superseded_by})` : ''}</span>
            </span>
          )}

          {hit.amendments_count > 0 && (
            <span
              className="badge badge-blue"
              title={`${hit.amendments_count} gazetted technical amendment(s) applied`}
            >
              <span>{hit.amendments_count} Amend.</span>
            </span>
          )}

          <span
            className={`badge ${hit.confidence === 'HIGH' ? 'badge-emerald' : 'badge-amber'}`}
            title={`Rerank Score: ${(hit.rerank_score || 0).toFixed(3)}`}
          >
            {confidenceScore}% {hit.confidence}
          </span>
        </div>
      </div>

      {/* Mandatory QCO Regulatory Box with Scheme Identification */}
      {isMandatoryQCO && qcoDetails && (
        <div className={isHallmarking ? 'qco-box-gold' : isCRS ? 'qco-box-blue' : 'qco-box'}>
          <div className="qco-box-header">
            {isHallmarking ? (
              <>
                <Award size={16} />
                <span>DOCA MANDATORY HALLMARKING (SCHEME-IV) — 6-DIGIT HUID REQUIRED</span>
              </>
            ) : isCRS ? (
              <>
                <Zap size={16} />
                <span>MANDATORY COMPULSORY REGISTRATION (SCHEME-II CRS) — R-NUMBER REQUIRED</span>
              </>
            ) : (
              <>
                <ShieldAlert size={16} />
                <span>MANDATORY COMPLIANCE BY LAW — {qcoDetails.scheme_type || 'SCHEME-I (ISI MARK)'}</span>
              </>
            )}
          </div>
          <div className="qco-box-content">
            {qcoDetails.compliance_warning ||
              'This product is notified under a mandatory Quality Control Order (QCO) under Section 16 of the BIS Act, 2016. Procurement of non-certified products is illegal under public procurement rules.'}
          </div>
        </div>
      )}

      {/* Standard Official Scope */}
      <div className="scope-box">
        <strong style={{ color: 'var(--text-primary)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.2rem' }}>
          Standard Scope & Requirements:
        </strong>
        {hit.scope || 'Standard specification covering physical, chemical, performance and quality requirements for Indian standard conformance.'}
      </div>

      {/* Tender File Rationale / Justification */}
      <div className="rationale-box">
        <span className="rationale-label">TENDER AUDIT JUSTIFICATION:</span>
        <span>{hit.rationale}</span>
      </div>

      {/* Allied Standards & Actions Bar with Taxonomy Badges */}
      <div className="allied-bar">
        <div className="allied-group">
          <span className="allied-title">Allied Standards Taxonomy:</span>
          {hit.allied_standards && hit.allied_standards.length > 0 ? (
            hit.allied_standards.slice(0, 5).map((allied, idx) => {
              const rel = allied.relation_type;
              let tagClass = 'allied-tag';
              let prefix = '';
              if (rel === 'NORM_TEST') {
                tagClass += ' allied-tag-test';
                prefix = '🧪 ';
              } else if (rel === 'INSTALLATION') {
                tagClass += ' allied-tag-install';
                prefix = '🛠️ ';
              } else if (rel === 'SAFETY') {
                tagClass += ' allied-tag-safety';
                prefix = '🛡️ ';
              } else if (rel === 'TERMINOLOGY') {
                tagClass += ' allied-tag-terms';
                prefix = '📖 ';
              }

              return (
                <span
                  key={idx}
                  className={tagClass}
                  title={`${allied.label || 'Allied Standard'}: ${allied.title} (${allied.relation_type || 'Related'})`}
                >
                  {prefix}{allied.target_is_code}
                </span>
              );
            })
          ) : (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              No linked allied testing codes
            </span>
          )}
        </div>

        <div className="card-actions">
          <button
            className="btn-action-secondary"
            onClick={handleCopyCode}
            title="Copy standard code to clipboard"
          >
            {copiedCode ? <Check size={13} color="#34d399" /> : <Copy size={13} />}
            <span>{copiedCode ? 'Copied' : 'Copy IS Code'}</span>
          </button>
          <button
            className="btn-action-primary"
            onClick={() => onOpenGeMClause(hit.is_code)}
            title="Draft ready-to-paste GeM tender clause"
          >
            <FileText size={14} />
            <span>Generate GeM Clause</span>
          </button>
        </div>
      </div>
    </article>
  );
}
