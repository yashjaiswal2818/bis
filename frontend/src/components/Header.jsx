import React from 'react';
import { Search, FileSpreadsheet, Award } from 'lucide-react';

export default function Header({ isOnline, latency, activeTab, setActiveTab, displayLanguage, onLanguageChange }) {
  return (
    <>
      {/* Utility bar — thin dark strip */}
      <div className="utility-bar">
        <div className="utility-inner">
          <span className="utility-left">Smart India Hackathon 2026 · Problem Statement 26108</span>
          <div className="utility-right">
            <a href="#main-content" className="skip-link">Skip to main content</a>
            <div className="lang-toggle-group">
              <button
                className={`lang-btn ${displayLanguage === 'en' ? 'active' : ''}`}
                onClick={() => onLanguageChange('en')}
              >EN</button>
              <button
                className={`lang-btn ${displayLanguage === 'hi' ? 'active' : ''}`}
                onClick={() => onLanguageChange('hi')}
              >हिन्दी</button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Header */}
      <header className="portal-header">
        <div className="portal-header-inner">
          <div className="portal-brand">
            <div className="brand-icon" aria-label="Indian Standards mark">IS</div>
            <div className="brand-text">
              <div className="brand-title">Indian Standards Recommendation Platform</div>
              <div className="brand-tagline">Standards identification, QCO verification and GeM clause drafting</div>
            </div>
          </div>

          <div className="portal-nav-area">
            <nav className="portal-nav" aria-label="Main Navigation">
              <button
                className={`nav-btn ${activeTab === 'search' ? 'active' : ''}`}
                onClick={() => setActiveTab('search')}
              >
                <Search size={15} /> Find Standards
              </button>
              <button
                className={`nav-btn ${activeTab === 'tender' ? 'active' : ''}`}
                onClick={() => setActiveTab('tender')}
              >
                <FileSpreadsheet size={15} /> Tender &amp; BoQ Auditor
              </button>
              <button
                className={`nav-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
                onClick={() => setActiveTab('benchmark')}
              >
                <Award size={15} /> Evaluation Sandbox
              </button>
            </nav>
            <div className={`engine-status ${isOnline ? 'online' : ''}`}>
              <span className={`status-dot ${isOnline ? 'online' : ''}`} />
              <span>{isOnline ? 'Engine Active' : 'Connecting…'}</span>
            </div>
          </div>
        </div>
      </header>
    </>
  );
}
