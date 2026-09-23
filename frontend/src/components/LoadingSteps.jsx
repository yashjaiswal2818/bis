import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, Circle } from 'lucide-react';
import { useLanguage } from '../i18n';

const STEP_KEYS = ['load_step1', 'load_step2', 'load_step3', 'load_step4', 'load_step5'];

export default function LoadingSteps({ query }) {
  const { t } = useLanguage();
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => (prev < STEP_KEYS.length - 1 ? prev + 1 : prev));
    }, 450);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loading-box" role="status" aria-live="polite">
      <div className="loading-header">
        <Loader2 size={24} className="spin-icon" color="#0C4DA1" />
        <div>
          <h4 className="loading-title">{t('loading_title')}</h4>
          <p className="loading-subtitle">
            {t('loading_subtitle', { query: query.length > 55 ? query.slice(0, 55) + '...' : query })}
          </p>
        </div>
      </div>

      <div className="steps-list">
        {STEP_KEYS.map((stepKey, idx) => {
          const isDone = idx < currentStepIndex;
          const isActive = idx === currentStepIndex;

          return (
            <div
              key={idx}
              className={`step-item ${isDone ? 'done' : ''} ${isActive ? 'active' : ''}`}
            >
              <div className="step-icon-wrap">
                {isDone ? (
                  <CheckCircle2 size={15} color="#1E6B4F" />
                ) : isActive ? (
                  <Loader2 size={13} className="spin-icon" color="#0C4DA1" />
                ) : (
                  <Circle size={10} color="#64708A" />
                )}
              </div>
              <span>{t(stepKey)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
