/**
 * NyayaPath — Type-Safe API Client for FastAPI Backend
 */

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  user_story: string;
  disclaimer_accepted: boolean;
  offence_date?: string | null;
  fir_date?: string | null;
  original_user_story?: string | null;
  messages?: ChatMessage[];
}

export interface NodeTraceItem {
  name: string;
  duration_ms: number;
  completed: boolean;
  timestamp: string;
}

export interface SearchSource {
  title: string;
  url: string;
  snippet?: string;
}

export interface ChatResponse {
  final_guidance: string;
  code_regime?: 'bns_bnss' | 'ipc_crpc' | 'ambiguous' | null;
  needs_clarification: boolean;
  is_crisis: boolean;
  is_harmful: boolean;
  refusal_reason?: string | null;
  node_trace: NodeTraceItem[];
  sources: SearchSource[];
  output_check_passed?: boolean | null;
  validation_feedback: string[];
}

export interface SystemHealthResponse {
  status: string;
  version: string;
  rag_ready: boolean;
  rag_documents_count: number;
  rag_bm25_count: number;
  acts_indexed: Record<string, number>;
  ollama_model: string;
}

export interface DemoScenario {
  id: string;
  title: string;
  category: string;
  prompt: string;
  expected_regime: string;
  badge_color: string;
}

const API_BASE = '/api';

export async function fetchHealth(): Promise<SystemHealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchPresets(): Promise<DemoScenario[]> {
  const res = await fetch(`${API_BASE}/presets`);
  if (!res.ok) {
    throw new Error(`Presets fetch failed: ${res.statusText}`);
  }
  return res.json();
}

export async function sendChatMessage(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error (${res.status})`);
  }

  return res.json();
}
