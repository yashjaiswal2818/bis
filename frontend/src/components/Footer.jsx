import React from 'react';

export default function Footer() {
  return (
    <footer className="portal-footer">
      <div className="portal-footer-inner">
        <div className="footer-left">
          <div className="footer-brand">Indian Standards Recommendation Platform</div>
          <div className="footer-desc">
            Automating standard identification and tender compliance verification.
          </div>
        </div>
        <div className="footer-columns">
          <div className="footer-col">
            <h4>The engine</h4>
            <ul>
              <li>Find Standards</li>
              <li>Tender & BoQ Auditor</li>
              <li>Evaluation Sandbox</li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>Data & provenance</h4>
            <ul>
              <li>Registry Snapshot: 2026-09-10</li>
              <li>QCO Source: bis.gov.in</li>
              <li><a href="#">Known Limitations</a></li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>Resources</h4>
            <ul>
              <li><a href="https://bis.gov.in" target="_blank" rel="noreferrer">bis.gov.in</a></li>
              <li><a href="https://standardsbis.bsbedge.com" target="_blank" rel="noreferrer">standardsbis.bsbedge.com</a></li>
              <li><a href="https://manakonline.in" target="_blank" rel="noreferrer">manakonline.in</a></li>
            </ul>
          </div>
        </div>
      </div>
      <div className="footer-bottom">
        <span>Built for Smart India Hackathon 2026 · PS 26108 · Not an official BIS service.</span>
      </div>
    </footer>
  );
}
