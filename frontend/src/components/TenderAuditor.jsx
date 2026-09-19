import React, { useState, useRef } from 'react';
import { Upload, FileSpreadsheet, FileText, Download, CheckCircle, AlertTriangle, Loader2, Info, ArrowUpRight } from 'lucide-react';
import { auditTenderFile } from '../api/client';

// Four states, one per parsed line item. NO_CONFIDENT_MATCH is the default: an item the
// engine could not assess is not an item that passed.
const AUDIT_STATE_ORDER = ['COMPLIANT', 'QCO_REQUIRED', 'STANDARD_SUGGESTED', 'NO_CONFIDENT_MATCH'];

const AUDIT_STATE_META = {
  COMPLIANT: {
    label: 'Compliant',
    tone: 'green',
    hint: 'Matched at HIGH confidence, no unmet certification',
  },
  QCO_REQUIRED: {
    label: 'QCO required',
    tone: 'amber',
    hint: 'Mandatory ISI / CRS / Hallmark not referenced',
  },
  STANDARD_SUGGESTED: {
    label: 'Standard suggested',
    tone: 'blue',
    hint: 'No IS code in the item text; one matched at HIGH',
  },
  NO_CONFIDENT_MATCH: {
    label: 'Not assessed',
    tone: 'grey',
    hint: 'Confidence below HIGH, or no match found',
  },
};

const normalizeAuditState = (state) =>
  AUDIT_STATE_ORDER.includes(state) ? state : 'NO_CONFIDENT_MATCH';

export default function TenderAuditor({ onOpenGeMClause, onViewDetails }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditResult, setAuditResult] = useState(null);
  const [auditError, setAuditError] = useState(null);
  const [currentFileName, setCurrentFileName] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

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
      {/* Officer Advisory Banner */}
      <div className="officer-banner">
        <Info size={20} className="officer-banner-icon" />
        <div className="officer-banner-text">
          <h3>Tender Document & Bill of Quantities (BoQ) Auditor</h3>
          <p>
            Upload your Notice Inviting Tender (NIT) PDF, technical specifications document, or Schedule of Quantities (CSV) from CPWD/MES/GeM/CPPP.
            The engine automatically isolates the scope of work, audits technical line items against BIS standards, and flags mandatory ISI/CRS certification rules under the BIS Act, 2016.
          </p>
        </div>
      </div>

      {/* Dropzone Area */}
      <div
        className={`dropzone-box ${isDragging ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          accept=".pdf,.csv"
          onChange={handleFileChange}
        />
        <Upload className="dropzone-icon" />
        <div>
          <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '0.35rem' }}>
            Upload Draft Tender PDF or BoQ Schedule (CSV)
          </h4>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Drag & drop tender document here, or click to browse (supports .pdf NIT notices, technical specs, and .csv BoQs)
          </p>
        </div>
      </div>

      {/* Loading Progress */}
      {isAuditing && (
        <div style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--primary-blue)' }}>
          <Loader2 size={32} className="spin-icon" style={{ margin: '0 auto 0.75rem' }} />
          <p style={{ fontWeight: 600, color: 'var(--primary-navy)' }}>
            Auditing {currentFileName} against Indian Standards & QCOs...
          </p>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Parsing engineering clauses, decomposing work scope & matching authentic IS codes
          </span>
        </div>
      )}

      {/* Error Message */}
      {auditError && (
        <div style={{
          background: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: 'var(--radius-md)',
          padding: '1rem 1.25rem',
          color: '#991b1b',
          marginTop: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem'
        }}>
          <AlertTriangle size={18} />
          <span>{auditError}</span>
        </div>
      )}

      {/* Audit Results Table */}
      {auditResult && (
        <div style={{ marginTop: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--primary-navy)' }}>
                Audit Results: {currentFileName}
              </h3>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Document Format: {auditResult.type?.toUpperCase()} | Line items assessed:{' '}
                {auditResult.items_assessed ?? items.length}
                {auditResult.items_parsed > (auditResult.items_assessed ?? items.length)
                  ? ` of ${auditResult.items_parsed} parsed`
                  : ''}
              </span>
            </div>

            <button className="btn-action-outline" onClick={handleExportAuditedBoQ}>
              <Download size={15} />
              <span>Export Audited Schedule (.csv)</span>
            </button>
          </div>

          {auditResult.warning && (
            <div style={{
              background: '#fffbeb',
              border: '1px solid #fde68a',
              borderRadius: 'var(--radius-md)',
              padding: '0.8rem 1rem',
              color: '#92400e',
              fontSize: '0.84rem',
              marginBottom: '1rem'
            }}>
              <strong>Notice:</strong> {auditResult.warning}
            </div>
          )}

          {/* Every parsed line item is counted here, including the ones with nothing wrong. */}
          <div className="audit-summary-strip">
            {AUDIT_STATE_ORDER.map((state) => {
              const meta = AUDIT_STATE_META[state];
              const count = auditResult.audit_status_counts?.[state] ?? 0;
              return (
                <div key={state} className={`audit-summary-cell audit-state-${meta.tone}`}>
                  <span className="audit-summary-count">{count}</span>
                  <span className="audit-summary-label">{meta.label}</span>
                  <span className="audit-summary-hint">{meta.hint}</span>
                </div>
              );
            })}
          </div>

          {auditResult.audit_truncated && (
            <div className="audit-cap-notice">
              <AlertTriangle size={15} />
              <span>
                Showing first <strong>{auditResult.items_assessed}</strong> of{' '}
                <strong>{auditResult.items_parsed}</strong> parsed line items. Each item runs a full
                hybrid search, so the audit is capped at {auditResult.audit_cap} per upload.
              </span>
            </div>
          )}

          <div className="table-wrapper">
            <table className="officer-table">
              <thead>
                <tr>
                  <th style={{ width: '4%' }}>#</th>
                  <th style={{ width: '32%' }}>Tender Item / Specification Clause</th>
                  <th style={{ width: '14%' }}>Status</th>
                  <th style={{ width: '8%' }}>Quantity</th>
                  <th style={{ width: '32%' }}>Recommended Indian Standards</th>
                  <th style={{ width: '10%' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                      No technical line items identified in this document.
                    </td>
                  </tr>
                ) : (
                  items.map((item, idx) => {
                    const state = normalizeAuditState(item.compliance_verdict?.audit_status);
                    const meta = AUDIT_STATE_META[state];
                    return (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600, color: 'var(--text-muted)' }}>{idx + 1}</td>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--primary-navy)', marginBottom: '0.2rem', lineHeight: 1.45 }}>
                          {item.item_description || item.clause_text}
                        </div>
                      </td>
                      <td>
                        <span
                          className={`audit-chip audit-state-${meta.tone}`}
                          title={item.compliance_verdict?.audit_status_reason || meta.hint}
                        >
                          {meta.label}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        {item.quantity ? `${item.quantity} ${item.unit || ''}` : 'Clause'}
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                          {item.recommended_standards?.map((rec, rIdx) => (
                            <div key={rIdx} style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
                              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--primary-blue)', fontSize: '0.82rem' }}>
                                {rec.is_code}
                              </span>
                              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                                ({rec.title})
                              </span>
                              <span className={`badge ${rec.confidence === 'HIGH' ? 'badge-emerald' : 'badge-amber'}`} style={{ fontSize: '0.68rem' }}>
                                {rec.confidence}
                              </span>
                            </div>
                          ))}
                        </div>
                      </td>
                      <td>
                        {item.recommended_standards?.[0] && (
                          <div style={{ display: 'flex', gap: '0.35rem' }}>
                            <button
                              className="btn-action-primary"
                              style={{ fontSize: '0.75rem', padding: '0.3rem 0.55rem' }}
                              onClick={() => onOpenGeMClause(item.recommended_standards[0].is_code)}
                              title="Generate GeM Procurement Clause"
                            >
                              <FileText size={12} />
                              <span>GeM</span>
                            </button>
                            {onViewDetails && (
                              <button
                                className="btn-action-outline"
                                style={{ fontSize: '0.75rem', padding: '0.3rem 0.55rem' }}
                                onClick={() => onViewDetails(item.recommended_standards[0])}
                                title="View Standard Details"
                              >
                                <span>Details</span>
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

          {/* Bottom Audit Section: QCO_REQUIRED items only. Everything else is in the table. */}
          {items.length > 0 && (() => {
            const qcoItems = items
              .map((item, idx) => ({ item, index: idx + 1 }))
              .filter(({ item }) => normalizeAuditState(item.compliance_verdict?.audit_status) === 'QCO_REQUIRED');

            const missingISItems = qcoItems
              .map(({ item, index }) => ({
                index,
                desc: item.item_description || item.clause_text,
                missing_is_code: item.compliance_verdict?.missing_is_code,
                is_missing: Boolean(item.compliance_verdict?.is_code_missing),
              }))
              .filter((it) => it.is_missing && it.missing_is_code);

            const missingMarkItems = qcoItems
              .map(({ item, index }) => {
                const cv = item.compliance_verdict;
                let mark = null;
                if (cv?.hallmark_missing) {
                  mark = cv.missing_hallmark || 'Mandatory BIS Hallmark with 6-digit HUID (Scheme-IV)';
                } else if (cv?.isi_mark_missing) {
                  mark = cv.missing_isi_mark || 'Mandatory BIS ISI Mark (Scheme-I under QCO)';
                } else if (cv?.crs_missing) {
                  mark = cv.missing_crs || 'Mandatory BIS CRS Registration (Scheme-II)';
                }
                return {
                  index,
                  desc: item.item_description || item.clause_text,
                  missing_mark: mark,
                  is_missing: Boolean(mark),
                };
              })
              .filter((it) => it.is_missing);

            const isEverythingFine = qcoItems.length === 0;

            return (
              <div className="audit-bottom-container">
                {isEverythingFine ? (
                  <div className="audit-bottom-card audit-bottom-fine">
                    <CheckCircle size={32} style={{ color: '#059669', flexShrink: 0 }} />
                    <div>
                      <h4 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#065f46', margin: '0 0 0.25rem 0' }}>
                        No unmet certification obligations
                      </h4>
                      <p style={{ margin: 0, fontSize: '0.88rem', color: '#047857', lineHeight: 1.45 }}>
                        No assessed line item carries a mandatory ISI, CRS or Hallmark requirement that
                        the tender text fails to reference. Per-item status for every row is in the table above —
                        items marked <strong>Not assessed</strong> were not checked and still need manual review.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="audit-bottom-card audit-bottom-warning">
                    <div className="audit-bottom-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <AlertTriangle size={22} style={{ color: '#dc2626' }} />
                        <h4 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--primary-navy)', margin: 0 }}>
                          Audit Findings: Missing Indian Standards & Hallmarks
                        </h4>
                      </div>
                      <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                        Statutory compliance under BIS Act 2016 & Line Ministry QCOs
                      </span>
                    </div>

                    {/* 1. Missing Indian Standards */}
                    {missingISItems.length > 0 && (
                      <div className="missing-group-box">
                        <div className="missing-group-title">
                          <AlertTriangle size={15} />
                          <span>Missing Indian Standards (IS Codes) in Tender Clauses:</span>
                        </div>
                        <div className="missing-items-list">
                          {missingISItems.map((mItem, idx) => (
                            <div key={idx} className="missing-item-row">
                              <span className="missing-item-num">Item #{mItem.index}:</span>
                              <span className="missing-item-desc" title={mItem.desc}>
                                {mItem.desc}
                              </span>
                              <span className="missing-arrow">➔</span>
                              <span className="missing-solution-badge is-badge">
                                Missing IS Code: <strong>{mItem.missing_is_code}</strong>
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 2. Missing Hallmarks & Mandatory Quality Certifications */}
                    {missingMarkItems.length > 0 && (
                      <div className="missing-group-box">
                        <div className="missing-group-title hallmark-title">
                          <AlertTriangle size={15} />
                          <span>Missing Mandatory Hallmarks & Quality Certifications:</span>
                        </div>
                        <div className="missing-items-list">
                          {missingMarkItems.map((mItem, idx) => (
                            <div key={idx} className="missing-item-row">
                              <span className="missing-item-num">Item #{mItem.index}:</span>
                              <span className="missing-item-desc" title={mItem.desc}>
                                {mItem.desc}
                              </span>
                              <span className="missing-arrow">➔</span>
                              <span className="missing-solution-badge hallmark-badge">
                                Missing Hallmark / Mark: <strong>{mItem.missing_mark}</strong>
                              </span>
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
