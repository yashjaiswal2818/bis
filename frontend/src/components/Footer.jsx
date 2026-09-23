import React from 'react';
import { useLanguage } from '../i18n';

export default function Footer() {
  const { t } = useLanguage();
  return (
    <footer className="portal-footer">
      <div className="portal-footer-inner">
        <div className="footer-left">
          <div className="footer-brand">Standard Mark</div>
          <div className="footer-desc">
            {t('footer_desc')}
          </div>
        </div>
        <div className="footer-columns">
          <div className="footer-col">
            <h4>{t('footer_col_engine')}</h4>
            <ul>
              <li>{t('nav_find_standards')}</li>
              <li>{t('nav_tender_auditor')}</li>
              <li>{t('nav_evaluation_sandbox')}</li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>{t('footer_col_data')}</h4>
            <ul>
              <li>{t('footer_registry_snapshot', { date: '2026-09-10' })}</li>
              <li>{t('footer_qco_source')}</li>
              <li><a href="#">{t('footer_known_limitations')}</a></li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>{t('footer_col_resources')}</h4>
            <ul>
              <li><a href="https://bis.gov.in" target="_blank" rel="noreferrer">bis.gov.in</a></li>
              <li><a href="https://standardsbis.bsbedge.com" target="_blank" rel="noreferrer">standardsbis.bsbedge.com</a></li>
              <li><a href="https://manakonline.in" target="_blank" rel="noreferrer">manakonline.in</a></li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
}
