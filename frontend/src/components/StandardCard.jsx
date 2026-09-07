import React, { useState } from 'react';
import { ShieldAlert, CheckCircle2, AlertTriangle, FileText, Copy, Check, ExternalLink, BookOpen } from 'lucide-react';

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
            <span className="badge badge-emerald" title="Current valid BIS standard">
              <CheckCircle2 size={12} />
              <span>ACTIVE</span>
            </span>
          ) : (
            <span className="badge badge-amber" title="Superseded standard - Check updated version">
              <AlertTriangle size={12} />
              <span>SUPERSEDED {hit.superseded_by ? `(by ${hit.superseded_by})` : ''}</span>
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

      {/* Mandatory QCO Regulatory Box */}
      {isMandatoryQCO && qcoDetails && (
        <div className="qco-box">
          <div className="qco-box-header">
            <ShieldAlert size={15} />
            <span>MANDATORY COMPLIANCE BY LAW — {qcoDetails.scheme_type || 'QCO MANDATE'}</span>
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

      {/* Allied Standards & Actions Bar */}
      <div className="allied-bar">
        <div className="allied-group">
          <span className="allied-title">Allied Quality Codes:</span>
          {hit.allied_standards && hit.allied_standards.length > 0 ? (
            hit.allied_standards.slice(0, 4).map((allied, idx) => (
              <span
                key={idx}
                className="allied-tag"
                title={`${allied.label || 'Allied Standard'}: ${allied.title} (${allied.relation_type || 'Related'})`}
              >
                {allied.target_is_code}
              </span>
            ))
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
