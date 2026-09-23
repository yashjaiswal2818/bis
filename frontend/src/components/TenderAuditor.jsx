import React, { useState, useRef } from 'react';
import { Upload, FileText, Download, CheckCircle, AlertTriangle, Loader2, Info } from 'lucide-react';
import { auditTenderFile, exportPdfReport } from '../api/client';
import { useLanguage } from '../i18n';

// Four states, one per parsed line item. NO_CONFIDENT_MATCH is the default: an item the
// engine could not assess is not an item that passed.
const AUDIT_STATE_ORDER = ['COMPLIANT', 'QCO_REQUIRED', 'STANDARD_SUGGESTED', 'NO_CONFIDENT_MATCH'];

const AUDIT_STATE_META = {
  COMPLIANT: { labelKey: 'audit_state_compliant', tone: 'green', hintKey: 'audit_state_compliant_hint' },
  QCO_REQUIRED: { labelKey: 'audit_state_qco', tone: 'amber', hintKey: 'audit_state_qco_hint' },
  STANDARD_SUGGESTED: { labelKey: 'audit_state_suggested', tone: 'blue', hintKey: 'audit_state_suggested_hint' },
  NO_CONFIDENT_MATCH: { labelKey: 'audit_state_none', tone: 'grey', hintKey: 'audit_state_none_hint' },
};

const normalizeAuditState = (state) => (AUDIT_STATE_ORDER.includes(state) ? state : 'NO_CONFIDENT_MATCH');

export default function TenderAuditor({ onOpenGeMClause, onViewDetails }) {
  const { t } = useLanguage();
  const [isDragging, setIsDragging] = useState(false);
  const [isAuditing, setIsAuditing] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [auditResult, setAuditResult] = useState(null);
  const [auditError, setAuditError] = useState(null);
  const [currentFileName, setCurrentFileName] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length > 0) processFile(e.dataTransfer.files[0]);
  };
  const handleFileChange = (e) => { if (e.target.files?.length > 0) processFile(e.target.files[0]); };

  const processFile = async (file) => {
    setIsAuditing(true);
    setAuditError(null);
    setCurrentFileName(file.name);
    try {
      const data = await auditTenderFile(file);
      setAuditResult(data);
    } catch (err) {
      setAuditError(err.message || 'Failed to audit tender document');
    } finally {
      setIsAuditing(false);
    }
  };

  const handleExportPdf = async () => {
    if (!auditResult) return;
    setIsExportingPdf(true);
    setAuditError(null);
    try {
      const pdfBlob = await exportPdfReport(auditResult, `Audit_${currentFileName || 'Report'}.pdf`);
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Audit_${currentFileName || 'Report'}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      setAuditError(err.message || 'Failed to export PDF');
    } finally {
      setIsExportingPdf(false);
    }
  };

  const handleExportAuditedBoQ = () => {
    if (!auditResult) return;
    const items = auditResult.items_audited || auditResult.clauses_analyzed || [];
    if (items.length === 0) return;

    let csvContent = 'data:text/csv;charset=utf-8,';
    csvContent += 'Item / Technical Specification,Quantity,Unit,Recommended IS Codes,Compliance Status,Missing IS Code,Missing Hallmark / Mark,Verdict\n';
    items.forEach((item) => {
      const desc = (item.item_description || item.clause_text || '').replace(/"/g, '""');
      const qty = item.quantity || 'N/A';
      const unit = item.unit || 'N/A';
      const codes = (item.recommended_standards || []).map((r) => `${r.is_code} (${r.title})`).join('; ').replace(/"/g, '""');
      const cv = item.compliance_verdict || {};
      const status = normalizeAuditState(cv.audit_status);
      const missingCode = (cv.missing_is_code || 'None').replace(/"/g, '""');
      const missingMark = (cv.missing_mark_label || 'None').replace(/"/g, '""');
      const verdict = (cv.audit_status_reason || cv.verdict || 'Not assessed').replace(/"/g, '""');
      csvContent += `"${desc}","${qty}","${unit}","${codes}","${status}","${missingCode}","${missingMark}","${verdict}"\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `Audited_${currentFileName || 'Tender_BoQ'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const items = auditResult?.items_audited || auditResult?.clauses_analyzed || [];

  return (
    <div className="tender-auditor-container">
      <div className="officer-banner">
        <Info size={20} className="officer-banner-icon" />
        <div className="officer-banner-text">
          <h3>{t('tender_banner_title')}</h3>
          <p>
            {t('tender_banner_desc')}
          </p>
        </div>
      </div>

      <div
        className={`dropzone-box ${isDragging ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input type="file" ref={fileInputRef} style={{ display: 'none' }} accept=".pdf,.csv" onChange={handleFileChange} />
        <Upload className="dropzone-icon" />
        <div>
          <h4 className="dropzone-title">{t('dropzone_title')}</h4>
          <p className="dropzone-sub">{t('dropzone_sub')}</p>
        </div>
      </div>

      {isAuditing && (
        <div className="audit-loading">
          <Loader2 size={30} className="spin-icon" color="#0C4DA1" />
          <p>{t('audit_loading_title', { file: currentFileName })}</p>
          <span>{t('audit_loading_sub')}</span>
        </div>
      )}

      {auditError && (
        <div className="error-banner" style={{ marginTop: '1.5rem' }}>
          <AlertTriangle size={18} />
          <span>{auditError}</span>
        </div>
      )}

      {auditResult && (
        <div style={{ marginTop: '2rem' }}>
          <div className="audit-results-header">
            <div>
              <h3 className="audit-results-title">{t('audit_results_title', { file: currentFileName })}</h3>
              <span className="audit-results-meta">
                {t('audit_meta', { fmt: auditResult.type?.toUpperCase(), n: auditResult.items_assessed ?? items.length })}
                {auditResult.items_parsed > (auditResult.items_assessed ?? items.length) ? t('audit_meta_of_parsed', { total: auditResult.items_parsed }) : ''}
              </span>
            </div>
            <div className="audit-export-actions">
              <button className="btn-action-outline" onClick={handleExportPdf} disabled={isExportingPdf}>
                {isExportingPdf ? <Loader2 size={15} className="spin-icon" /> : <FileText size={15} />}
                <span>{isExportingPdf ? t('generating') : t('export_pdf')}</span>
              </button>
              <button className="btn-action-outline" onClick={handleExportAuditedBoQ}>
                <Download size={15} /><span>{t('export_csv')}</span>
              </button>
            </div>
          </div>

          {auditResult.warning && (
            <div className="audit-warning-notice"><strong>{t('notice_label')}</strong> {auditResult.warning}</div>
          )}

          <div className="audit-summary-strip">
            {AUDIT_STATE_ORDER.map((state) => {
              const meta = AUDIT_STATE_META[state];
              const count = auditResult.audit_status_counts?.[state] ?? 0;
              return (
                <div key={state} className={`audit-summary-cell audit-state-${meta.tone}`}>
                  <span className="audit-summary-count">{count}</span>
                  <span className="audit-summary-label">{t(meta.labelKey)}</span>
                  <span className="audit-summary-hint">{t(meta.hintKey)}</span>
                </div>
              );
            })}
          </div>

          {auditResult.audit_truncated && (
            <div className="audit-cap-notice">
              <AlertTriangle size={15} />
              <span>
                {t('audit_cap_notice', { n: auditResult.items_assessed, m: auditResult.items_parsed, cap: auditResult.audit_cap })}
              </span>
            </div>
          )}

          <div className="table-wrapper">
            <table className="officer-table">
              <thead>
                <tr>
                  <th style={{ width: '4%' }}>#</th>
                  <th style={{ width: '32%' }}>{t('tbl_item_spec')}</th>
                  <th style={{ width: '14%' }}>{t('tbl_status')}</th>
                  <th style={{ width: '8%' }}>{t('tbl_quantity')}</th>
                  <th style={{ width: '32%' }}>{t('tbl_recommended')}</th>
                  <th style={{ width: '10%' }}>{t('tbl_actions')}</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr><td colSpan={6} className="table-empty">{t('no_items_found')}</td></tr>
                ) : (
                  items.map((item, idx) => {
                    const state = normalizeAuditState(item.compliance_verdict?.audit_status);
                    const meta = AUDIT_STATE_META[state];
                    return (
                      <tr key={idx}>
                        <td className="item-index">{idx + 1}</td>
                        <td><div className="item-desc">{item.item_description || item.clause_text}</div></td>
                        <td><span className={`audit-chip audit-state-${meta.tone}`} title={item.compliance_verdict?.audit_status_reason || t(meta.hintKey)}>{t(meta.labelKey)}</span></td>
                        <td className="item-qty">{item.quantity ? `${item.quantity} ${item.unit || ''}` : t('clause_fallback')}</td>
                        <td>
                          {item.recommended_standards?.map((rec, rIdx) => (
                            <div key={rIdx} className="rec-standard-row">
                              <span className="rec-code mono">{rec.is_code}</span>
                              <span className="rec-title">({rec.title})</span>
                              <span className={`badge ${rec.confidence === 'HIGH' ? 'badge-emerald' : 'badge-amber'}`} style={{ fontSize: '0.68rem' }}>{rec.confidence}</span>
                            </div>
                          ))}
                        </td>
                        <td>
                          {item.recommended_standards?.[0] && (
                            <div className="row-actions">
                              <button className="btn-action-primary" onClick={() => onOpenGeMClause(item.recommended_standards[0].is_code)} title="Generate GeM procurement clause">
                                <FileText size={12} /><span>{t('row_gem')}</span>
                              </button>
                              {onViewDetails && (
                                <button className="btn-action-outline" onClick={() => onViewDetails(item.recommended_standards[0])} title="View standard details">
                                  <span>{t('row_details')}</span>
                                </button>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {items.length > 0 && (() => {
            const qcoItems = items
              .map((item, idx) => ({ item, index: idx + 1 }))
              .filter(({ item }) => normalizeAuditState(item.compliance_verdict?.audit_status) === 'QCO_REQUIRED');

            const missingISItems = qcoItems
              .map(({ item, index }) => ({
                index, desc: item.item_description || item.clause_text,
                missing_is_code: item.compliance_verdict?.missing_is_code,
                is_missing: Boolean(item.compliance_verdict?.is_code_missing),
              }))
              .filter((it) => it.is_missing && it.missing_is_code);

            const missingMarkItems = qcoItems
              .map(({ item, index }) => {
                const cv = item.compliance_verdict;
                let mark = null;
                if (cv?.hallmark_missing) mark = cv.missing_hallmark || t('mark_hallmark_fallback');
                else if (cv?.isi_mark_missing) mark = cv.missing_isi_mark || t('mark_isi_fallback');
                else if (cv?.crs_missing) mark = cv.missing_crs || t('mark_crs_fallback');
                return { index, desc: item.item_description || item.clause_text, missing_mark: mark, is_missing: Boolean(mark) };
              })
              .filter((it) => it.is_missing);

            const isEverythingFine = qcoItems.length === 0;

            return (
              <div className="audit-bottom-container">
                {isEverythingFine ? (
                  <div className="audit-bottom-card audit-bottom-fine">
                    <CheckCircle size={30} />
                    <div>
                      <h4>{t('audit_fine_title')}</h4>
                      <p>
                        {t('audit_fine_text')}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="audit-bottom-card audit-bottom-warning">
                    <div className="audit-bottom-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <AlertTriangle size={20} color="#D51820" />
                        <h4>{t('audit_warning_title')}</h4>
                      </div>
                      <span className="audit-bottom-meta">{t('audit_warning_meta')}</span>
                    </div>

                    {missingISItems.length > 0 && (
                      <div className="missing-group-box">
                        <div className="missing-group-title"><AlertTriangle size={15} /><span>{t('missing_is_title')}</span></div>
                        <div className="missing-items-list">
                          {missingISItems.map((mItem, idx) => (
                            <div key={idx} className="missing-item-row">
                              <span className="missing-item-num">{t('missing_item_num', { n: mItem.index })}</span>
                              <span className="missing-item-desc" title={mItem.desc}>{mItem.desc}</span>
                              <span className="missing-arrow">→</span>
                              <span className="missing-solution-badge">{t('missing_is_badge', { code: mItem.missing_is_code })}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {missingMarkItems.length > 0 && (
                      <div className="missing-group-box">
                        <div className="missing-group-title hallmark-title"><AlertTriangle size={15} /><span>{t('missing_mark_title')}</span></div>
                        <div className="missing-items-list">
                          {missingMarkItems.map((mItem, idx) => (
                            <div key={idx} className="missing-item-row">
                              <span className="missing-item-num">{t('missing_item_num', { n: mItem.index })}</span>
                              <span className="missing-item-desc" title={mItem.desc}>{mItem.desc}</span>
                              <span className="missing-arrow">→</span>
                              <span className="missing-solution-badge hallmark-badge">{t('missing_mark_badge', { mark: mItem.missing_mark })}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}
