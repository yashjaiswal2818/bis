import React from 'react';
import { ShieldCheck, Activity, Building2, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Header({ isOnline, latency }) {
  return (
    <>
      {/* Slim institutional identifier */}
      <div className="gov-topbar">
        <div className="gov-topbar-inner">
          <span>Government of India · Ministry of Consumer Affairs, Food &amp; Public Distribution</span>
          <span className="gov-topbar-right">BIS Act, 2016 · GFR Rule 144</span>
        </div>
      </div>

      {/* Main Header Bar */}
      <header className="app-header">
        <div className="header-inner">
          <div className="brand-section">
            <div className="bis-emblem-badge" title="Bureau of Indian Standards">
              <span>BIS</span>
            </div>
            <div className="brand-title-wrap">
              <div className="brand-title">
                <span>Indian Standards Recommendation Platform</span>
              </div>
              <div className="brand-subtitle">
                Standards identification, QCO verification and GeM clause drafting
              </div>
            </div>
          </div>

          <div className="header-meta">
            <div className="health-badge" title={isOnline ? 'Connected to local engine' : 'Checking server status'}>
              <span className={`status-dot ${isOnline ? 'online' : ''}`} />
              <span>
                {isOnline
                  ? `Engine Active ${latency ? `• ${latency}s` : ''}`
                  : 'Engine Connecting...'}
              </span>
            </div>
          </div>
        </div>
      </header>
    </>
  );
}
