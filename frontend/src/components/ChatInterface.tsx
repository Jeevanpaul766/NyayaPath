import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Send, 
  Scale, 
  User, 
  Loader2, 
  Trash2, 
  BookOpen, 
  FileDown, 
  Printer, 
  Copy, 
  Check, 
  ExternalLink 
} from 'lucide-react';
import type { ChatMessage, ChatResponse } from '../services/api';
import { sendChatMessage } from '../services/api';
import { TimelineClarify } from './TimelineClarify';
import { PipelineVisualizer } from './PipelineVisualizer';
import { downloadTextMemo, printMemoAsPDF } from '../utils/exportMemo';

interface ChatInterfaceProps {
  initialPrompt?: string;
  onClearInitialPrompt?: () => void;
}

interface EnrichedMessage extends ChatMessage {
  responseMeta?: ChatResponse;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  initialPrompt, 
  onClearInitialPrompt 
}) => {
  const [messages, setMessages] = useState<EnrichedMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeRegime, setActiveRegime] = useState<string | null>(null);
  const [awaitingClarification, setAwaitingClarification] = useState(false);
  const [lastUserStory, setLastUserStory] = useState('');
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Execute initial prompt if provided from landing page preset
  useEffect(() => {
    if (initialPrompt && initialPrompt.trim()) {
      handleSendMessage(initialPrompt);
      if (onClearInitialPrompt) onClearInitialPrompt();
    }
  }, [initialPrompt]);

  const handleSendMessage = async (textToSend: string, offenceDate?: string, firDate?: string) => {
    if (!textToSend.trim() || isLoading) return;

    const userMsg: EnrichedMessage = { role: 'user', content: textToSend };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    const rootStory = awaitingClarification && lastUserStory ? lastUserStory : textToSend;

    try {
      const resp = await sendChatMessage({
        user_story: textToSend,
        disclaimer_accepted: true,
        offence_date: offenceDate,
        fir_date: firDate,
        original_user_story: rootStory,
        messages: messages.map(m => ({ role: m.role, content: m.content })),
      });

      const assistantMsg: EnrichedMessage = {
        role: 'assistant',
        content: resp.final_guidance,
        responseMeta: resp,
      };

      setMessages((prev) => [...prev, assistantMsg]);
      
      if (resp.code_regime) {
        setActiveRegime(resp.code_regime);
      }

      if (resp.needs_clarification) {
        setAwaitingClarification(true);
        if (!lastUserStory) setLastUserStory(textToSend);
      } else {
        setAwaitingClarification(false);
        setLastUserStory('');
      }

    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ **System Error:** ${err.message || 'Unable to execute query.'} Please try again.`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTimelineSubmit = (offenceDate: string, firDate: string) => {
    let clarifiedPrompt = lastUserStory || "Here are the dates for my case:";
    if (offenceDate) clarifiedPrompt += ` The events occurred in ${offenceDate}.`;
    if (firDate) clarifiedPrompt += ` The FIR/notice was registered in ${firDate}.`;

    handleSendMessage(clarifiedPrompt, offenceDate, firDate);
  };

  const handleResetChat = () => {
    setMessages([]);
    setActiveRegime(null);
    setAwaitingClarification(false);
    setLastUserStory('');
  };

  const handleCopyMemo = (content: string, idx: number) => {
    navigator.clipboard.writeText(content);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div style={{
      maxWidth: '1080px',
      margin: '0 auto',
      padding: '1.5rem 1rem 3rem 1rem',
      display: 'flex',
      flexDirection: 'column',
      minHeight: 'calc(100vh - 85px)',
    }}>
      
      {/* Chat Top Header & Active Regime Pill */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingBottom: '1rem',
        borderBottom: '1px solid var(--border-subtle)',
        marginBottom: '1.5rem',
        flexWrap: 'wrap',
        gap: '0.8rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700 }}>
            Case Orientation Console
          </h2>
          {activeRegime === 'bns_bnss' && (
            <span className="badge badge-bns">
              🟢 BNS / BNSS (Post-1 July 2024)
            </span>
          )}
          {activeRegime === 'ipc_crpc' && (
            <span className="badge badge-ipc">
              🔴 IPC / CrPC (Pre-1 July 2024)
            </span>
          )}
          {activeRegime === 'ambiguous' && (
            <span className="badge badge-ambiguous">
              🟡 Ambiguous Timeline (Dual-Framing)
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          {/* LangSmith Direct Dashboard Link */}
          <a
            href="https://smith.langchain.com"
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.4rem 0.8rem',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-muted)',
              fontSize: '0.8rem',
              textDecoration: 'none',
              fontWeight: 500,
            }}
            title="Inspect project runs and traces in LangSmith"
          >
            <span>LangSmith Dashboard</span>
            <ExternalLink style={{ width: '13px', height: '13px' }} />
          </a>

          {messages.length > 0 && (
            <button 
              onClick={handleResetChat}
              className="btn-secondary"
              style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
            >
              <Trash2 style={{ width: '14px', height: '14px' }} />
              <span>Reset Session</span>
            </button>
          )}
        </div>
      </div>

      {/* Message List */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        gap: '1.75rem',
        marginBottom: '2rem',
      }}>
        {messages.length === 0 ? (
          <div className="glass-panel" style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            maxWidth: '680px',
            margin: '3rem auto',
            border: '1px dashed var(--border-medium)',
          }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'rgba(212, 168, 67, 0.1)',
              border: '1px solid var(--border-gold)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem auto',
            }}>
              <Scale style={{ width: '28px', height: '28px', color: 'var(--gold-primary)' }} />
            </div>
            <h3 style={{ fontSize: '1.4rem', marginBottom: '0.6rem' }}>
              How can NyayaPath guide you today?
            </h3>
            <p style={{ fontSize: '0.92rem', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '1.75rem' }}>
              Describe your legal situation in natural language. The agent determines whether the <strong>IPC (1860)</strong> or <strong>BNS (2023)</strong> applies, retrieves statutory sections from 2,820 bare acts, and outputs structured procedural guidance.
            </p>

            {/* Quick Starters */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', textAlign: 'left' }}>
              <div 
                onClick={() => setInputValue("My wife filed a 498A FIR against me. The incidents happened in August 2024. What should I do?")}
                style={{
                  padding: '0.8rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  fontSize: '0.86rem',
                  color: '#e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span>🟢 "My wife filed a 498A FIR against me in August 2024..."</span>
                <span style={{ color: 'var(--gold-primary)', fontSize: '0.8rem' }}>Try BNS 85 →</span>
              </div>

              <div 
                onClick={() => setInputValue("Someone cheated me of 2 lakh rupees in a property deal in January 2024. How do I file a complaint?")}
                style={{
                  padding: '0.8rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  fontSize: '0.86rem',
                  color: '#e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span>🔴 "Someone cheated me of 2 lakh rupees in January 2024..."</span>
                <span style={{ color: 'var(--gold-primary)', fontSize: '0.8rem' }}>Try IPC 420 →</span>
              </div>

              <div 
                onClick={() => setInputValue("Police came to my house with a notice. Can they arrest me without warrant?")}
                style={{
                  padding: '0.8rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  fontSize: '0.86rem',
                  color: '#e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span>🟡 "Police came to my house with a notice. Can they arrest me?"</span>
                <span style={{ color: 'var(--gold-primary)', fontSize: '0.8rem' }}>Try Ambiguous →</span>
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div 
              key={idx}
              className="animate-fade-in"
              style={{
                display: 'flex',
                gap: '1rem',
                alignItems: 'flex-start',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              {/* Avatar */}
              <div style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                flexShrink: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: msg.role === 'user' 
                  ? 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)' 
                  : 'linear-gradient(135deg, var(--gold-primary) 0%, #855e16 100%)',
                color: '#fff',
                boxShadow: msg.role === 'assistant' ? 'var(--shadow-gold)' : 'none',
              }}>
                {msg.role === 'user' ? <User style={{ width: '20px', height: '20px' }} /> : <Scale style={{ width: '20px', height: '20px' }} />}
              </div>

              {/* Message Body */}
              <div style={{
                maxWidth: '85%',
                width: msg.role === 'assistant' ? '85%' : 'auto',
                background: msg.role === 'user' ? 'rgba(59, 130, 246, 0.15)' : 'var(--bg-surface-elevated)',
                border: msg.role === 'user' ? '1px solid rgba(59, 130, 246, 0.35)' : '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-md)',
                padding: '1.5rem',
                fontSize: '0.94rem',
                lineHeight: '1.75',
                color: '#f8fafc',
                boxShadow: 'var(--shadow-sm)',
              }}>
                
                {/* Assistant Legal Memo Action Toolbar */}
                {msg.role === 'assistant' && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingBottom: '0.9rem',
                    marginBottom: '1.25rem',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                    flexWrap: 'wrap',
                    gap: '0.6rem',
                  }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--gold-primary)', fontWeight: 700, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                      ⚖️ Legal Guidance Memorandum
                    </span>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {/* PDF Print Button */}
                      <button
                        onClick={() => printMemoAsPDF(msg.content, msg.responseMeta?.code_regime)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          padding: '0.35rem 0.65rem',
                          background: 'rgba(255, 255, 255, 0.06)',
                          border: '1px solid var(--border-medium)',
                          borderRadius: 'var(--radius-sm)',
                          color: '#fff',
                          fontSize: '0.78rem',
                          cursor: 'pointer',
                        }}
                        title="Download as printable PDF memorandum"
                      >
                        <Printer style={{ width: '13px', height: '13px', color: 'var(--gold-primary)' }} />
                        <span>Download PDF</span>
                      </button>

                      {/* Text Memo Download Button */}
                      <button
                        onClick={() => downloadTextMemo(msg.content, msg.responseMeta?.code_regime)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          padding: '0.35rem 0.65rem',
                          background: 'rgba(255, 255, 255, 0.06)',
                          border: '1px solid var(--border-medium)',
                          borderRadius: 'var(--radius-sm)',
                          color: '#fff',
                          fontSize: '0.78rem',
                          cursor: 'pointer',
                        }}
                        title="Download structured text memo (.md)"
                      >
                        <FileDown style={{ width: '13px', height: '13px', color: 'var(--bns-emerald)' }} />
                        <span>Download Text</span>
                      </button>

                      {/* Copy Button */}
                      <button
                        onClick={() => handleCopyMemo(msg.content, idx)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          padding: '0.35rem 0.65rem',
                          background: 'rgba(255, 255, 255, 0.06)',
                          border: '1px solid var(--border-medium)',
                          borderRadius: 'var(--radius-sm)',
                          color: '#fff',
                          fontSize: '0.78rem',
                          cursor: 'pointer',
                        }}
                        title="Copy formatted text to clipboard"
                      >
                        {copiedIdx === idx ? (
                          <>
                            <Check style={{ width: '13px', height: '13px', color: 'var(--bns-emerald)' }} />
                            <span style={{ color: 'var(--bns-emerald)' }}>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy style={{ width: '13px', height: '13px' }} />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {/* Formatted Content Rendering (ReactMarkdown) */}
                {msg.role === 'assistant' ? (
                  <div className="memo-markdown">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div style={{ whiteSpace: 'pre-wrap' }}>
                    {msg.content}
                  </div>
                )}

                {/* Sources if present */}
                {msg.responseMeta && msg.responseMeta.sources && msg.responseMeta.sources.length > 0 && (
                  <div style={{
                    marginTop: '1.5rem',
                    paddingTop: '1rem',
                    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                  }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontWeight: 700, display: 'block', marginBottom: '0.5rem', letterSpacing: '0.03em' }}>
                      RETRIEVED STATUTORY SECTIONS & AUTHORITATIVE SOURCES:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {msg.responseMeta.sources.map((src, sIdx) => (
                        <div 
                          key={sIdx}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.4rem',
                            fontSize: '0.78rem',
                            padding: '0.3rem 0.7rem',
                            borderRadius: '6px',
                            background: 'rgba(212, 168, 67, 0.08)',
                            color: 'var(--gold-primary)',
                            border: '1px solid rgba(212, 168, 67, 0.25)',
                          }}
                        >
                          <BookOpen style={{ width: '13px', height: '13px' }} />
                          <span>{src.title}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Telemetry Trace */}
                {msg.responseMeta && msg.responseMeta.node_trace && (
                  <PipelineVisualizer trace={msg.responseMeta.node_trace} />
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'linear-gradient(135deg, var(--gold-primary) 0%, #855e16 100%)',
              color: '#fff',
            }}>
              <Scale style={{ width: '20px', height: '20px' }} />
            </div>
            <div className="glass-panel" style={{
              padding: '0.85rem 1.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              fontSize: '0.88rem',
              color: 'var(--gold-primary)',
            }}>
              <Loader2 style={{ width: '18px', height: '18px', animation: 'spin 1s linear infinite' }} />
              <span>Analyzing criminal law timeline & querying 2,820 bare acts...</span>
            </div>
          </div>
        )}

        {/* Timeline Clarification Component when requested */}
        {awaitingClarification && !isLoading && (
          <TimelineClarify 
            onSubmitDates={handleTimelineSubmit} 
            isLoading={isLoading} 
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div style={{
        position: 'sticky',
        bottom: '1rem',
        zIndex: 20,
      }}>
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage(inputValue);
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            background: 'rgba(17, 24, 39, 0.94)',
            backdropFilter: 'blur(20px)',
            border: '1px solid var(--border-medium)',
            borderRadius: 'var(--radius-lg)',
            padding: '0.6rem 0.8rem',
            boxShadow: 'var(--shadow-lg)',
          }}
        >
          <input
            type="text"
            placeholder={awaitingClarification ? "Or describe your timeline in natural language..." : "Describe your legal situation (e.g., 'My landlord locked me out in August 2024')..."}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#fff',
              fontSize: '0.96rem',
              padding: '0.5rem 0.75rem',
              fontFamily: 'inherit',
            }}
          />

          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="btn-primary"
            style={{
              padding: '0.7rem 1.25rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.9rem',
            }}
          >
            <span>Send</span>
            <Send style={{ width: '16px', height: '16px' }} />
          </button>
        </form>

        <p style={{
          textAlign: 'center',
          fontSize: '0.75rem',
          color: 'var(--text-dim)',
          marginTop: '0.6rem',
        }}>
          NyayaPath provides educational orientation only · Not legal advice · Always consult an advocate.
        </p>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
