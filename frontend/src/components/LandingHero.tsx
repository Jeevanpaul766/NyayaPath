import React from 'react';
import { 
  Sparkles, 
  ShieldCheck, 
  Database, 
  GitBranch, 
  ArrowRight,
  AlertCircle
} from 'lucide-react';
import type { DemoScenario } from '../services/api';

interface LandingHeroProps {
  onStartChat: (initialPrompt?: string) => void;
  presets: DemoScenario[];
}

export const LandingHero: React.FC<LandingHeroProps> = ({ onStartChat, presets }) => {
  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '3.5rem 1.5rem 5rem 1.5rem' }}>
      
      {/* Top Banner Tag */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.6rem',
          padding: '0.45rem 1.1rem',
          background: 'rgba(212, 168, 67, 0.1)',
          border: '1px solid var(--border-gold)',
          borderRadius: 'var(--radius-full)',
          boxShadow: 'var(--shadow-gold)',
        }}>
          <Sparkles style={{ width: '15px', height: '15px', color: 'var(--gold-primary)' }} />
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--gold-primary)' }}>
            Indian Criminal Law Overhaul · 1 July 2024 Transition Architecture
          </span>
        </div>
      </div>

      {/* Hero Headline */}
      <div style={{ textAlign: 'center', maxWidth: '900px', margin: '0 auto 3rem auto' }}>
        <h1 style={{
          fontSize: '3.6rem',
          lineHeight: '1.15',
          marginBottom: '1.25rem',
          letterSpacing: '-0.03em',
        }}>
          Ethical Procedural Guidance for <br />
          <span className="gold-gradient-text">Indian Criminal Justice</span>
        </h1>
        <p style={{
          fontSize: '1.2rem',
          color: 'var(--text-muted)',
          lineHeight: '1.7',
          marginBottom: '2.5rem',
        }}>
          NyayaPath uses <strong>12-node cyclic LangGraph orchestration</strong>, a <strong>2,820-section dual-regime Hybrid RAG engine</strong>, and <strong>deterministic zero-LLM output sanitization</strong> to guide citizens through procedural rights without hallucinating legal advice.
        </p>

        {/* Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <button 
            onClick={() => onStartChat()}
            className="btn-primary"
            style={{ fontSize: '1.05rem', padding: '0.9rem 2.2rem' }}
          >
            <span>Start Free Case Evaluation</span>
            <ArrowRight style={{ width: '18px', height: '18px' }} />
          </button>
          <a
            href="https://github.com/Jeevanpaul766/NyayaPath"
            target="_blank"
            rel="noreferrer"
            className="btn-secondary"
            style={{ textDecoration: 'none', fontSize: '1.05rem', padding: '0.9rem 1.8rem' }}
          >
            <Database style={{ width: '18px', height: '18px', color: 'var(--gold-primary)' }} />
            <span>2,820 Section RAG Corpus</span>
          </a>
        </div>
      </div>

      {/* Key Stats Counter Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '1.25rem',
        marginBottom: '4.5rem',
      }}>
        <div className="glass-panel" style={{ padding: '1.8rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
            <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)', fontWeight: 600 }}>RAG Corpus</span>
            <Database style={{ width: '20px', height: '20px', color: 'var(--gold-primary)' }} />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#fff', marginBottom: '0.3rem' }}>
            2,820
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Official Gazette bare acts: BNS (358), BNSS (1,075), IPC (710), CrPC (677).
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '1.8rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
            <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)', fontWeight: 600 }}>Section 482 Collision</span>
            <GitBranch style={{ width: '20px', height: '20px', color: 'var(--bns-emerald)' }} />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--bns-emerald)', marginBottom: '0.3rem' }}>
            100% Resolved
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            CrPC 482 (High Court Quashing) vs BNSS 482 (Anticipatory Bail) partitioned by date.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '1.8rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
            <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)', fontWeight: 600 }}>Safety Gate</span>
            <ShieldCheck style={{ width: '20px', height: '20px', color: '#60a5fa' }} />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#60a5fa', marginBottom: '0.3rem' }}>
            Zero-LLM
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Deterministic regex quality gate purges outcome guarantees & unverified sections.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '1.8rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
            <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)', fontWeight: 600 }}>Crisis Ordering</span>
            <AlertCircle style={{ width: '20px', height: '20px', color: 'var(--crisis-pink)' }} />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--crisis-pink)', marginBottom: '0.3rem' }}>
            Pre-Filter
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Distress detection runs strictly before safety to prevent suicidal refusals.
          </p>
        </div>
      </div>

      {/* Interactive 1-Click Test Scenarios Section */}
      <div>
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <h2 style={{ fontSize: '2.2rem', marginBottom: '0.6rem' }}>
            Interactive Demo Test Cases
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.05rem' }}>
            Click any real-world scenario below to simulate the agentic pipeline instantly.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: '1.5rem',
        }}>
          {presets.map((preset) => (
            <div
              key={preset.id}
              onClick={() => onStartChat(preset.prompt)}
              className="glass-panel"
              style={{
                padding: '1.75rem',
                cursor: 'pointer',
                transition: 'all 0.25s ease',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--gold-primary)';
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 12px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(212, 168, 67, 0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-subtle)';
                e.currentTarget.style.transform = 'none';
                e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
                  <span 
                    className="badge" 
                    style={{ 
                      backgroundColor: `${preset.badge_color}18`, 
                      color: preset.badge_color,
                      border: `1px solid ${preset.badge_color}40`,
                    }}
                  >
                    {preset.category}
                  </span>
                  <ArrowRight style={{ width: '16px', height: '16px', color: 'var(--text-dim)' }} />
                </div>
                <h3 style={{ fontSize: '1.2rem', marginBottom: '0.6rem', color: '#fff' }}>
                  {preset.title}
                </h3>
                <p style={{
                  fontSize: '0.88rem',
                  color: 'var(--text-muted)',
                  lineHeight: '1.6',
                  fontStyle: 'italic',
                }}>
                  "{preset.prompt}"
                </p>
              </div>

              <div style={{
                marginTop: '1.5rem',
                paddingTop: '1rem',
                borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '0.82rem',
                color: 'var(--gold-primary)',
                fontWeight: 600,
              }}>
                <span>Test with Full LangGraph Agent</span>
                <span>→</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
