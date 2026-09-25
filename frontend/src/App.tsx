import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DisclaimerModal } from './components/DisclaimerModal';
import { LandingHero } from './components/LandingHero';
import { ChatInterface } from './components/ChatInterface';
import { fetchHealth, fetchPresets } from './services/api';
import type { DemoScenario } from './services/api';

export function App() {
  const [currentView, setCurrentView] = useState<'landing' | 'chat'>('landing');
  const [disclaimerAccepted, setDisclaimerAccepted] = useState<boolean>(() => {
    return localStorage.getItem('nyayapath_disclaimer_accepted') === 'true';
  });
  const [ragDocCount, setRagDocCount] = useState<number>(2820);
  const [presets, setPresets] = useState<DemoScenario[]>([]);
  const [selectedInitialPrompt, setSelectedInitialPrompt] = useState<string | undefined>(undefined);

  useEffect(() => {
    // Fetch live system health
    fetchHealth()
      .then((data) => {
        if (data.rag_documents_count) {
          setRagDocCount(data.rag_documents_count);
        }
      })
      .catch((err) => {
        console.warn('Could not connect to live backend health:', err);
      });

    // Fetch demo presets
    fetchPresets()
      .then((data) => {
        setPresets(data);
      })
      .catch((err) => {
        console.warn('Could not fetch presets:', err);
      });
  }, []);

  const handleAcceptDisclaimer = () => {
    setDisclaimerAccepted(true);
    localStorage.setItem('nyayapath_disclaimer_accepted', 'true');
  };

  const handleStartChatWithPrompt = (prompt?: string) => {
    if (prompt) {
      setSelectedInitialPrompt(prompt);
    }
    setCurrentView('chat');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* FR-1 Statutory Disclaimer Modal */}
      <DisclaimerModal
        isOpen={!disclaimerAccepted}
        onAccept={handleAcceptDisclaimer}
      />

      {/* Main Navbar */}
      <Navbar
        currentView={currentView}
        onNavigate={(view) => setCurrentView(view)}
        ragDocCount={ragDocCount}
      />

      {/* Main Content Area */}
      <main style={{ flex: 1 }}>
        {currentView === 'landing' ? (
          <LandingHero
            presets={presets}
            onStartChat={handleStartChatWithPrompt}
          />
        ) : (
          <ChatInterface
            initialPrompt={selectedInitialPrompt}
            onClearInitialPrompt={() => setSelectedInitialPrompt(undefined)}
          />
        )}
      </main>
    </div>
  );
}

export default App;
