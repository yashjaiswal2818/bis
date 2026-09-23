import React, { useState, useEffect } from 'react';
import { X, Copy, Check, Download, FileText, AlertTriangle } from 'lucide-react';
import { useLanguage } from '../i18n';

export default function GeMClauseModal({ isOpen, onClose, isCode, clauseData, isLoading, error }) {
  const { t } = useLanguage();
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

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
        <div className="modal-header">
          <div className="modal-title-group">
            <FileText size={17} color="#0C4DA1" />
            <span className="standard-full-title" style={{ marginBottom: 0, fontSize: '1rem' }}>
              {t('gem_title_prefix')}<span className="mono">{isCode}</span>
            </span>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label={t('close_modal')}><X size={18} /></button>
        </div>

        <div className="modal-body">
          {isLoading ? (
            <div className="audit-loading">
              <p>{t('gem_drafting', { code: isCode })}</p>
            </div>
          ) : error ? (
            <div className="error-banner">
              <AlertTriangle size={18} />
              <span>{error}</span>
            </div>
          ) : (
            <>
              <div className="clause-guidance">
                <strong>{t('gem_guidance_label')}</strong> {t('gem_guidance_text')}
              </div>
              <textarea className="clause-textarea" readOnly value={clauseData?.full_tender_specification_text || ''} />
            </>
          )}
        </div>

        <div className="modal-footer">
          <span style={{ fontSize: '0.78rem', color: 'var(--ink-muted)' }}>
            {t('gem_compliance_footer')}
          </span>
          <div style={{ display: 'flex', gap: '0.6rem' }}>
            <button className="btn-action-outline" onClick={handleDownload} disabled={isLoading || !clauseData}>
              <Download size={14} /><span>{t('download_txt')}</span>
            </button>
            <button className="btn-action-primary" onClick={handleCopy} disabled={isLoading || !clauseData}>
              {copied ? <Check size={14} /> : <Copy size={14} />}
              <span>{copied ? t('copied_clipboard') : t('copy_clause_gem')}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
