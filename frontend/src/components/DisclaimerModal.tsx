import React, { useState } from 'react';
import { AlertTriangle, ArrowRight } from 'lucide-react';

interface DisclaimerModalProps {
  isOpen: boolean;
  onAccept: () => void;
}

export const DisclaimerModal: React.FC<DisclaimerModalProps> = ({ isOpen, onAccept }) => {
  const [isChecked, setIsChecked] = useState(false);

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 100,
      backgroundColor: 'rgba(3, 5, 10, 0.88)',
      backdropFilter: 'blur(20px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem',
    }}>
      <div className="glass-panel-elevated animate-fade-in" style={{
        maxWidth: '680px',
        width: '100%',
        padding: '2.5rem',
        border: '1px solid var(--border-gold)',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(212, 168, 67, 0.2)',
        position: 'relative',
      }}>
        {/* Header Icon */}
        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '16px',
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '1.5rem',
        }}>
          <AlertTriangle style={{ width: '28px', height: '28px', color: '#ef4444' }} />
        </div>

        <h2 style={{ fontSize: '1.75rem', marginBottom: '0.8rem' }}>
          Mandatory Statutory Notice & Disclaimer
        </h2>

        <div style={{
          background: 'rgba(255, 255, 255, 0.03)',
          borderLeft: '4px solid var(--gold-primary)',
          padding: '1rem 1.25rem',
          borderRadius: '0 8px 8px 0',
          marginBottom: '1.5rem',
          fontSize: '0.94rem',
          color: 'var(--text-muted)',
          lineHeight: '1.7',
        }}>
          <strong style={{ color: '#fff' }}>NyayaPath</strong> is a specialized <strong>portfolio and educational AI research system</strong>.
          It provides high-level educational orientation on Indian criminal procedure (IPC/CrPC & BNS/BNSS).
        </div>

        <ul style={{
          listStyle: 'none',
          padding: 0,
          margin: '0 0 2rem 0',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          fontSize: '0.92rem',
          color: 'var(--text-muted)',
        }}>
          <li style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem' }}>
            <span style={{ color: '#ef4444', fontWeight: 'bold' }}>✕</span>
            <span><strong>NOT Legal Advice:</strong> This software does not offer legal representation or privileged counsel.</span>
          </li>
          <li style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem' }}>
            <span style={{ color: '#ef4444', fontWeight: 'bold' }}>✕</span>
            <span><strong>NO Guaranteed Outcomes:</strong> Court outcomes cannot be guaranteed under any circumstance.</span>
          </li>
          <li style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem' }}>
            <span style={{ color: 'var(--bns-emerald)', fontWeight: 'bold' }}>✓</span>
            <span><strong>Consult an Advocate:</strong> You must consult a qualified advocate enrolled with the Bar Council of India or contact NALSA at <strong>15100</strong>.</span>
          </li>
        </ul>

        {/* Checkbox */}
        <label style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.8rem',
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-md)',
          padding: '1rem',
          cursor: 'pointer',
          marginBottom: '1.75rem',
        }}>
          <input
            type="checkbox"
            checked={isChecked}
            onChange={(e) => setIsChecked(e.target.checked)}
            style={{ width: '20px', height: '20px', marginTop: '2px', accentColor: 'var(--gold-primary)', cursor: 'pointer' }}
          />
          <span style={{ fontSize: '0.88rem', color: '#e2e8f0', lineHeight: '1.5' }}>
            I acknowledge that NyayaPath is an educational AI system and does not constitute legal counsel. I agree to verify all legal procedures with a licensed advocate.
          </span>
        </label>

        {/* Continue Button */}
        <button
          onClick={onAccept}
          disabled={!isChecked}
          className="btn-primary"
          style={{ width: '100%', padding: '0.95rem', fontSize: '1.05rem' }}
        >
          <span>Acknowledge & Proceed to NyayaPath</span>
          <ArrowRight style={{ width: '18px', height: '18px' }} />
        </button>
      </div>
    </div>
  );
};
