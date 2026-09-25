import React, { useState } from 'react';
import { GitBranch, ChevronDown, ChevronUp, CheckCircle, Clock } from 'lucide-react';
import type { NodeTraceItem } from '../services/api';

interface PipelineVisualizerProps {
  trace: NodeTraceItem[];
}

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({ trace }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!trace || trace.length === 0) return null;

  const totalDuration = trace.reduce((acc, curr) => acc + curr.duration_ms, 0);

  return (
    <div className="glass-panel" style={{
      marginTop: '1.25rem',
      padding: '1rem 1.25rem',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      fontSize: '0.85rem',
    }}>
      <div 
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          userSelect: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <GitBranch style={{ width: '16px', height: '16px', color: 'var(--gold-primary)' }} />
          <span style={{ fontWeight: 600, color: '#fff' }}>
            LangGraph Execution Telemetry
          </span>
          <span className="badge badge-bns" style={{ fontSize: '0.72rem', padding: '0.1rem 0.5rem' }}>
            {trace.length} Nodes
          </span>
          <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>
            ({(totalDuration / 1000).toFixed(2)}s total)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          <a
            href="https://smith.langchain.com"
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              fontSize: '0.76rem',
              padding: '0.2rem 0.6rem',
              background: 'rgba(212, 168, 67, 0.15)',
              border: '1px solid rgba(212, 168, 67, 0.4)',
              borderRadius: '4px',
              color: 'var(--gold-primary)',
              textDecoration: 'none',
              fontWeight: 600,
            }}
            title="Inspect full graph execution traces, latency, and tokens in LangSmith"
          >
            <span>LangSmith ↗</span>
          </a>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem' }}>{isOpen ? 'Hide trace' : 'View node details'}</span>
            {isOpen ? <ChevronUp style={{ width: '16px', height: '16px' }} /> : <ChevronDown style={{ width: '16px', height: '16px' }} />}
          </div>
        </div>
      </div>

      {isOpen && (
        <div style={{
          marginTop: '1rem',
          paddingTop: '0.8rem',
          borderTop: '1px solid rgba(255, 255, 255, 0.06)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
        }}>
          {trace.map((node, idx) => (
            <div 
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.45rem 0.75rem',
                borderRadius: '6px',
                background: 'rgba(255, 255, 255, 0.02)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <CheckCircle style={{ width: '14px', height: '14px', color: 'var(--bns-emerald)' }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: '#e2e8f0' }}>
                  {idx + 1}. {node.name}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-dim)', fontSize: '0.78rem' }}>
                <Clock style={{ width: '12px', height: '12px' }} />
                <span>{node.duration_ms.toFixed(1)} ms</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
