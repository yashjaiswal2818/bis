import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, Circle } from 'lucide-react';

const STEPS = [
  'Extracting technical concepts & specifications',
  'Searching 33,553+ authentic Indian Standards catalog',
  'Applying hardware-adaptive cross-encoder reranking',
  'Auditing mandatory Quality Control Orders (QCOs)',
  'Checking allied testing & safety standards',
];

export default function LoadingSteps({ query }) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 450);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loading-box" role="status" aria-live="polite">
      <div className="loading-header">
        <Loader2 size={24} className="spin-icon" color="#1d4ed8" />
        <div>
          <h4 className="loading-title">Understanding Procurement Requirement</h4>
          <h4 className="loading-title">Reading selected BIS sources and preparing an evidence-backed analysis...</h4>
          <p className="loading-subtitle">
            Analyzing "{query.length > 55 ? query.slice(0, 55) + '...' : query}" against national standards...
          </p>
        </div>
      </div>

      <div className="steps-list">
        {STEPS.map((step, idx) => {
          const isDone = idx < currentStepIndex;
          const isActive = idx === currentStepIndex;

          return (
            <div
              key={idx}
              className={`step-item ${isDone ? 'done' : ''} ${isActive ? 'active' : ''}`}
            >
              <div className="step-icon-wrap">
                {isDone ? (
                  <CheckCircle2 size={15} color="#059669" />
                ) : isActive ? (
                  <Loader2 size={13} className="spin-icon" color="#1d4ed8" />
                ) : (
                  <Circle size={10} color="#94a3b8" />
                )}
              </div>
              <span>{step}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
