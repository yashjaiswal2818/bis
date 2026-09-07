import React, { useState } from 'react';
import { X, Copy, Check, Download, FileText, AlertTriangle } from 'lucide-react';

export default function GeMClauseModal({ isOpen, onClose, isCode, clauseData, isLoading, error }) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopy = () => {
    if (clauseData?.full_tender_specification_text) {
      navigator.clipboard.writeText(clauseData.full_tender_specification_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!clauseData?.full_tender_specification_text) return;
    const element = document.createElement('a');
    const file = new Blob([clauseData.full_tender_specification_text], { type: 'text/plain;charset=utf-8' });
    element.href = URL.createObjectURL(file);
    element.download = `GeM_Tender_Clause_${isCode.replace(/\s+/g, '_')}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <FileText size={18} color="#60a5fa" />
            <span>Official GeM Tender Specification Clause: {isCode}</span>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              <p>Drafting official GeM & GFR 2017 compliant specification clause for <strong>{isCode}</strong>...</p>
            </div>
          ) : error ? (
            <div style={{ color: 'var(--alert-red)', padding: '1.5rem', background: 'var(--alert-red-soft)', borderRadius: 'var(--radius-md)' }}>
              <AlertTriangle size={18} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />
              {error}
            </div>
          ) : (
            <>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', background: 'var(--bg-muted)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <strong>Procurement Guidance:</strong> This clause is structured per <strong>Rule 144 of GFR 2017</strong> and GeM Custom Bid guidelines. Paste directly into your GeM ATC (Additional Terms & Conditions) or Schedule of Technical Specifications.
              </div>

              <textarea
                className="clause-textarea"
                readOnly
                value={clauseData?.full_tender_specification_text || ''}
              />
            </>
          )}
        </div>

        <div className="modal-footer">
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Compliance: BIS Act 2016 & GeM Portal Standards
          </span>
          <div style={{ display: 'flex', gap: '0.6rem' }}>
            <button
              className="btn-action-secondary"
              onClick={handleDownload}
              disabled={isLoading || !clauseData}
            >
              <Download size={14} />
              <span>Download (.txt)</span>
            </button>
            <button
              className="btn-action-primary"
              onClick={handleCopy}
              disabled={isLoading || !clauseData}
            >
              {copied ? <Check size={14} color="#34d399" /> : <Copy size={14} />}
              <span>{copied ? 'Copied to Clipboard!' : 'Copy Clause for GeM'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
