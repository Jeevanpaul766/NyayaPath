import React from 'react';
import { Scale, PhoneCall, Sparkles, BookOpen } from 'lucide-react';

interface NavbarProps {
  currentView: 'landing' | 'chat';
  onNavigate: (view: 'landing' | 'chat') => void;
  ragDocCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, onNavigate, ragDocCount }) => {
  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 40,
      backdropFilter: 'blur(20px)',
      backgroundColor: 'rgba(7, 9, 15, 0.85)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '0.85rem 2rem',
    }}>
      <div style={{
        maxWidth: '1300px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        {/* Brand */}
        <div 
          onClick={() => onNavigate('landing')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}
        >
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, rgba(212, 168, 67, 0.25) 0%, rgba(212, 168, 67, 0.05) 100%)',
            border: '1px solid var(--border-gold)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-gold)',
          }}>
            <Scale style={{ width: '22px', height: '22px', color: 'var(--gold-primary)' }} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.3rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#fff' }}>
                Nyaya<span style={{ color: 'var(--gold-primary)' }}>Path</span>
              </span>
              <span className="badge badge-bns" style={{ fontSize: '0.72rem', padding: '0.15rem 0.5rem' }}>
                v1.0
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Ethical Legal AI · Dual-Regime (IPC & BNS)
            </p>
          </div>
        </div>

        {/* Live Index Status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          padding: '0.4rem 0.9rem',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-full)',
          fontSize: '0.82rem',
        }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block', boxShadow: '0 0 8px #10b981' }} />
          <span style={{ color: 'var(--text-muted)' }}>Local RAG Corpus:</span>
          <strong style={{ color: 'var(--gold-primary)' }}>{ragDocCount > 0 ? `${ragDocCount.toLocaleString()} Sections` : '2,820 Sections'}</strong>
        </div>

        {/* Nav Links & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          {/* LangSmith Redirection Button */}
          <a
            href="https://smith.langchain.com"
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.45rem',
              padding: '0.5rem 0.95rem',
              background: 'rgba(212, 168, 67, 0.1)',
              border: '1px solid var(--border-gold)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--gold-primary)',
              textDecoration: 'none',
              fontSize: '0.84rem',
              fontWeight: 600,
              transition: 'all 0.2s ease',
            }}
            title="Open live telemetry and execution traces in LangSmith"
          >
            <Sparkles style={{ width: '14px', height: '14px' }} />
            <span>LangSmith Traces ↗</span>
          </a>

          <button
            onClick={() => onNavigate(currentView === 'landing' ? 'chat' : 'landing')}
            className={currentView === 'landing' ? 'btn-primary' : 'btn-secondary'}
            style={{ fontSize: '0.88rem', padding: '0.55rem 1.1rem' }}
          >
            {currentView === 'landing' ? (
              <>
                <Scale style={{ width: '16px', height: '16px' }} />
                <span>Launch Legal Agent</span>
              </>
            ) : (
              <>
                <BookOpen style={{ width: '16px', height: '16px' }} />
                <span>Overview & Docs</span>
              </>
            )}
          </button>

          {/* Emergency Helpline Capsule */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.45rem 0.85rem',
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            borderRadius: 'var(--radius-md)',
            color: '#f87171',
            fontSize: '0.82rem',
            fontWeight: 600,
          }}>
            <PhoneCall style={{ width: '14px', height: '14px' }} />
            <span>Emergency: 112 · Helpline: 14416</span>
          </div>
        </div>
      </div>
    </header>
  );
};
