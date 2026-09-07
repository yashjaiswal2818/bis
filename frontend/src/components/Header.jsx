import React from 'react';
import { ShieldCheck, Activity, Building2 } from 'lucide-react';

export default function Header({ isOnline, latency }) {
  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="brand-section">
          <div className="bis-emblem-badge">
            <span>BIS</span>
          </div>
          <div>
            <div className="brand-title">
              <span>Indian Standards (BIS) Recommendation Engine</span>
            </div>
            <div className="brand-subtitle">
              Official Compliance, Technical Clause Drafting & Mandatory QCO Auditing Portal
            </div>
          </div>
        </div>

        <div className="header-meta">
          <div className="officer-badge">
            <Building2 size={13} />
            <span>Govt Procurement Officer Mode</span>
          </div>

          <div className="health-badge">
            <span className={`status-dot ${isOnline ? 'online' : ''}`} />
            <span>
              {isOnline
                ? `Engine: Active ${latency ? `(${latency}s)` : ''}`
                : 'Engine: Connecting...'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
