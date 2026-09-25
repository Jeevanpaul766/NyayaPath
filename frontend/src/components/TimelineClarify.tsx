import React, { useState } from 'react';
import { ArrowRight, Clock } from 'lucide-react';

interface TimelineClarifyProps {
  onSubmitDates: (offenceDate: string, firDate: string) => void;
  isLoading: boolean;
}

export const TimelineClarify: React.FC<TimelineClarifyProps> = ({ onSubmitDates, isLoading }) => {
  const [offenceDate, setOffenceDate] = useState('');
  const [firDate, setFirDate] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!offenceDate && !firDate) return;
    onSubmitDates(offenceDate, firDate);
  };

  return (
    <div className="glass-panel-elevated animate-fade-in" style={{
      padding: '1.75rem',
      margin: '1.5rem 0',
      border: '1px solid var(--ambiguous-amber)',
      boxShadow: '0 8px 30px rgba(245, 158, 11, 0.15)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.8rem' }}>
        <Clock style={{ width: '20px', height: '20px', color: 'var(--ambiguous-amber)' }} />
        <h4 style={{ fontSize: '1.15rem', color: '#fff' }}>
          Timeline Clarification Needed
        </h4>
      </div>

      <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.25rem', lineHeight: '1.6' }}>
        India transitioned to new criminal codes on <strong>1 July 2024</strong>. Substantive offences committed prior to July 1 fall under the <strong>Indian Penal Code (IPC)</strong>, while subsequent offences fall under the <strong>Bharatiya Nyaya Sanhita (BNS)</strong>.
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '0.4rem', fontWeight: 600 }}>
              Roughly when did the incident occur?
            </label>
            <input
              type="text"
              placeholder="e.g. August 2024, January 2024, last year..."
              value={offenceDate}
              onChange={(e) => setOffenceDate(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-medium)',
                color: '#fff',
                fontSize: '0.9rem',
                outline: 'none',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '0.4rem', fontWeight: 600 }}>
              When was the notice or FIR received?
            </label>
            <input
              type="text"
              placeholder="e.g. September 2024, last week, yesterday..."
              value={firDate}
              onChange={(e) => setFirDate(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-medium)',
                color: '#fff',
                fontSize: '0.9rem',
                outline: 'none',
              }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
          <button
            type="submit"
            disabled={isLoading || (!offenceDate && !firDate)}
            className="btn-primary"
            style={{ padding: '0.65rem 1.4rem', fontSize: '0.9rem' }}
          >
            <span>Confirm Timeline & Resolve Regime</span>
            <ArrowRight style={{ width: '16px', height: '16px' }} />
          </button>
        </div>
      </form>
    </div>
  );
};
