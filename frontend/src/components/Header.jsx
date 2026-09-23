import React from 'react';
import { Search, FileSpreadsheet, Award } from 'lucide-react';
import { useLanguage } from '../i18n';

export default function Header({ isOnline, latency, activeTab, setActiveTab }) {
  const { lang, setLang, t } = useLanguage();
  return (
    <header className="portal-header">
      <a href="#main-content" className="skip-link">{t('header_skip_link')}</a>
      <div className="portal-header-inner">
        <div className="portal-brand">
          <div className="brand-mark-wrap">
            <img src="/bis-logo.png" alt="Bureau of Indian Standards" className="brand-logo-img" width="38" height="31" />
          </div>
          <div>
            <div className="brand-title">Standard Mark</div>
            <div className="brand-tagline">{t('header_tagline')}</div>
          </div>
        </div>

        <div className="portal-nav-area">
          <nav className="portal-nav" aria-label="Main Navigation">
            <button
              className={`nav-btn ${activeTab === 'search' ? 'active' : ''}`}
              onClick={() => setActiveTab('search')}
            >
              <Search size={15} /> <span>{t('nav_find_standards')}</span>
            </button>
            <button
              className={`nav-btn ${activeTab === 'tender' ? 'active' : ''}`}
              onClick={() => setActiveTab('tender')}
            >
              <FileSpreadsheet size={15} /> <span>{t('nav_tender_auditor')}</span>
            </button>
            <button
              className={`nav-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
              onClick={() => setActiveTab('benchmark')}
            >
              <Award size={15} /> <span>{t('nav_evaluation_sandbox')}</span>
            </button>
          </nav>
          <div className="lang-toggle-group">
            <button
              className={`lang-btn ${lang === 'en' ? 'active' : ''}`}
              onClick={() => setLang('en')}
            >EN</button>
            <button
              className={`lang-btn ${lang === 'hi' ? 'active' : ''}`}
              onClick={() => setLang('hi')}
            >हिन्दी</button>
          </div>
          <div className="engine-status">
            <span className={`status-dot ${isOnline ? 'online' : ''}`} />
            <span>{isOnline ? t('header_engine_active') : t('header_connecting')}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
