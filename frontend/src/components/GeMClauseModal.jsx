import React, { useState } from 'react';
import { X, Copy, Check, Download, FileText, AlertTriangle, ShieldCheck } from 'lucide-react';

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
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <FileText size={18} color="#1d4ed8" />
            <span style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--primary-navy)' }}>
              GeM Technical Specification Clause: {isCode}
            </span>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        {/* Modal Content */}
        <div className="modal-body">
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              <p>Drafting official GeM & GFR 2017 compliant specification clause for <strong>{isCode}</strong>...</p>
            </div>
          ) : error ? (
            <div style={{
              color: '#991b1b',
              padding: '1.25rem',
              background: '#fef2f2',
              borderRadius: 'var(--radius-md)',
              border: '1px solid #fecaca',
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem'
            }}>
              <AlertTriangle size={18} flexShrink={0} />
              <span>{error}</span>
            </div>
          ) : (
            <>
              <div style={{
                fontSize: '0.85rem',
                color: '#1e40af',
                background: '#eff6ff',
                padding: '0.85rem 1rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #bfdbfe'
              }}>
                <strong>Procurement Guidance (GFR 2017 Rule 144):</strong> This clause specifies standard compliance without proprietary vendor lock-in. Paste directly into your GeM Custom Bid Additional Terms & Conditions (ATC) or Tender Specification Schedule.
              </div>

              <textarea
                className="clause-textarea"
                readOnly
                value={clauseData?.full_tender_specification_text || ''}
              />
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Compliance: Bureau of Indian Standards Act, 2016 & GeM Procurement Manual
          </span>
          <div style={{ display: 'flex', gap: '0.6rem' }}>
            <button
              className="btn-action-outline"
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
              {copied ? <Check size={14} color="#059669" /> : <Copy size={14} />}
              <span>{copied ? 'Copied to Clipboard!' : 'Copy Clause for GeM'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
