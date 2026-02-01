import { useState, Component, type ReactNode } from 'react';
import { AppLayout } from './components/Layout/AppLayout';
import { TabNavigation } from './components/Layout/TabNavigation';
import { ChatContainer } from './components/Chat/ChatContainer';
import { DashboardContainer } from './components/Dashboard/DashboardContainer';
import { ImpulseContainer } from './components/Impulse/ImpulseContainer';
import { RecommendationsContainer } from './components/Recommendations/RecommendationsContainer';
import { StakeholderContainer } from './components/Stakeholder/StakeholderContainer';
import { SettingsContainer } from './components/Settings/SettingsContainer';
import { useProjects } from './context/ProjectContext';
import { StakeholderProvider } from './context/StakeholderContext';
import { RefreshProvider } from './context/RefreshContext';

// Error Boundary to catch rendering errors
class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('App Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen bg-gray-50">
          <div className="text-center">
            <h2 className="text-xl font-bold text-gray-700 mb-2">Etwas ist schiefgelaufen</h2>
            <p className="text-gray-500 mb-4">Bitte laden Sie die Seite neu.</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Neu laden
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

function AppContent() {
  const [activeTab, setActiveTab] = useState('chat');
  const { selectedProject } = useProjects();

  return (
    <div className="flex flex-col h-full">
      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

      <div className="flex-1 overflow-hidden relative flex flex-col bg-gray-50/20">
        {selectedProject ? (
          <>
            <div className={activeTab === 'chat' ? 'flex flex-col flex-1 overflow-hidden' : 'hidden'}>
              <ChatContainer projectId={selectedProject.id} />
            </div>

            <div className={activeTab === 'dashboard' ? 'flex flex-col flex-1 overflow-hidden' : 'hidden'}>
              <DashboardContainer projectId={selectedProject.id} />
            </div>

            <div className={activeTab === 'impulse' ? 'flex flex-col flex-1 overflow-hidden' : 'hidden'}>
              <ImpulseContainer projectId={selectedProject.id} />
            </div>

            <div className={activeTab === 'recommendations' ? 'flex flex-col flex-1 overflow-hidden' : 'hidden'}>
              <RecommendationsContainer
                projectId={selectedProject.id}
                onNavigateToImpulse={() => setActiveTab('impulse')}
              />
            </div>

            <div className={activeTab === 'stakeholder' ? 'flex flex-col flex-1 overflow-hidden' : 'hidden'}>
              <StakeholderContainer projectId={selectedProject.id} />
            </div>

            <div className={activeTab === 'settings' ? 'flex flex-col flex-1 overflow-hidden' : 'hidden'}>
              <SettingsContainer projectId={selectedProject.id} />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-gray-400">Waehlen Sie ein Projekt aus der Seitenleiste</p>
          </div>
        )}
      </div>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <RefreshProvider>
        <StakeholderProvider>
          <AppLayout>
            <AppContent />
          </AppLayout>
        </StakeholderProvider>
      </RefreshProvider>
    </ErrorBoundary>
  );
}

export default App;
