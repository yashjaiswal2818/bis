import React from 'react';
import { ShieldCheck, Activity, Building2, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Header({ isOnline, latency }) {
  return (
    <>
      {/* Official Government Procurement Top Strip */}
      <div className="gov-topbar">
        <div className="gov-topbar-inner">
          <div className="gov-topbar-left">
            <span>🇮🇳 Government of India • Ministry of Consumer Affairs, Food & Public Distribution</span>
          </div>
          <div className="gov-topbar-right">
            <span>General Financial Rules (GFR) Rule 144 Compliant</span>
            <span>•</span>
            <span>Bureau of Indian Standards Act, 2016</span>
          </div>
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
                <span className="brand-tag">Procurement Intelligence</span>
              </div>
              <div className="brand-subtitle">
                Official AI-Powered Standards Identification, QCO Verification & GeM Clause Generator
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
