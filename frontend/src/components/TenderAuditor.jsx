import React, { useState, useRef } from 'react';
import { Upload, FileSpreadsheet, FileText, Download, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { auditTenderFile } from '../api/client';

export default function TenderAuditor({ onOpenGeMClause }) {
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
    csvContent += 'Item / Technical Specification,Quantity,Unit,Recommended IS Codes,Highest Confidence\n';

    items.forEach((item) => {
      const desc = (item.item_description || item.clause_text || '').replace(/"/g, '""');
      const qty = item.quantity || 'N/A';
      const unit = item.unit || 'N/A';
      const codes = (item.recommended_standards || []).map((r) => `${r.is_code} (${r.title})`).join('; ').replace(/"/g, '""');
      const conf = (item.recommended_standards || [])[0]?.confidence || 'N/A';

      csvContent += `"${desc}","${qty}","${unit}","${codes}","${conf}"\n`;
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
      {/* Officer Advice */}
      <div className="officer-banner">
        <FileSpreadsheet size={20} className="officer-banner-icon" />
        <div className="officer-banner-text">
          <h3>Tender Document & Bill of Quantities (BoQ) Auditor</h3>
          <p>
            Upload your draft tender document (PDF) or Schedule of Quantities (CSV) from CPWD/PWD/NIC formats. The engine will extract each line item, cross-reference against BIS standard databases, and alert you if any items require mandatory ISI/CRS certification.
          </p>
        </div>
      </div>

      {/* Dropzone */}
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
          <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            Upload Draft Tender PDF or BoQ CSV
          </h4>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Drag & drop files here, or click to browse (supports .pdf tenders and .csv schedules)
          </p>
        </div>
      </div>

      {/* Loading Status */}
      {isAuditing && (
        <div style={{ textAlign: 'center', padding: '2.5rem', color: '#60a5fa' }}>
          <Loader2 size={32} className="spin-icon" style={{ margin: '0 auto 0.75rem' }} />
          <p style={{ fontWeight: 600 }}>Auditing {currentFileName} against Indian Standards & QCOs...</p>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Parsing technical specifications and matching IS codes</span>
        </div>
      )}

      {/* Error Message */}
      {auditError && (
        <div style={{ background: 'var(--alert-red-soft)', border: '1px solid var(--alert-red-border)', borderRadius: 'var(--radius-md)', padding: '1rem', color: '#f87171', marginTop: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle size={18} />
          <span>{auditError}</span>
        </div>
      )}

      {/* Results Section */}
      {auditResult && (
        <div style={{ marginTop: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                Audit Results: {currentFileName}
              </h3>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Document Type: {auditResult.type?.toUpperCase()} | Items Audited: {items.length}
              </span>
            </div>

            <button className="btn-action-primary" onClick={handleExportAuditedBoQ}>
              <Download size={15} />
              <span>Export Audited BoQ (.csv)</span>
            </button>
          </div>

          {auditResult.warning && (
            <div style={{ background: 'var(--warning-amber-soft)', border: '1px solid rgba(245, 158, 11, 0.4)', borderRadius: 'var(--radius-md)', padding: '0.8rem 1rem', color: '#fbbf24', fontSize: '0.82rem', marginBottom: '1rem' }}>
              <strong>Notice:</strong> {auditResult.warning}
            </div>
          )}

          <div className="table-wrapper">
            <table className="officer-table">
              <thead>
                <tr>
                  <th style={{ width: '4%' }}>#</th>
                  <th style={{ width: '38%' }}>Tender Item / Specification Clause</th>
                  <th style={{ width: '12%' }}>Quantity</th>
                  <th style={{ width: '34%' }}>Recommended Indian Standards</th>
                  <th style={{ width: '12%' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                      No technical items identified in document.
                    </td>
                  </tr>
                ) : (
                  items.map((item, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600, color: 'var(--text-muted)' }}>{idx + 1}</td>
                      <td>
                        <div style={{ fontWeight: 600, marginBottom: '0.2rem' }}>
                          {item.item_description || item.clause_text}
                        </div>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        {item.quantity ? `${item.quantity} ${item.unit || ''}` : 'Clause'}
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                          {item.recommended_standards?.map((rec, rIdx) => (
                            <div key={rIdx} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#60a5fa', fontSize: '0.82rem' }}>
                                {rec.is_code}
                              </span>
                              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                                ({rec.title})
                              </span>
                              <span className={`badge ${rec.confidence === 'HIGH' ? 'badge-emerald' : 'badge-amber'}`} style={{ fontSize: '0.65rem' }}>
                                {rec.confidence}
                              </span>
                            </div>
                          ))}
                        </div>
                      </td>
                      <td>
                        {item.recommended_standards?.[0] && (
                          <button
                            className="btn-action-primary"
                            style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                            onClick={() => onOpenGeMClause(item.recommended_standards[0].is_code)}
                          >
                            <FileText size={12} />
                            <span>Clause</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
