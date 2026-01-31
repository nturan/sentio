import { useState } from 'react';
import { Sidebar } from '../Sidebar/Sidebar';
import { ProjectProvider } from '../../context/ProjectContext';
import { ChatSessionProvider } from '../../context/ChatSessionContext';
import { OnboardingModal } from '../Onboarding/OnboardingModal';

interface AppLayoutProps {
    children: React.ReactNode;
}

function AppLayoutContent({ children }: AppLayoutProps) {
    const [isModalOpen, setIsModalOpen] = useState(false);

    return (
        <div className="flex h-screen bg-gray-50 text-gray-900 overflow-hidden font-sans">
            <Sidebar onStartNewProject={() => setIsModalOpen(true)} />
            <div className="flex-1 flex flex-col min-w-0 bg-white">
                {children}
            </div>
            <OnboardingModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
        </div>
    );
}

export function AppLayout({ children }: AppLayoutProps) {
    return (
        <ProjectProvider>
            <ChatSessionProvider>
                <AppLayoutContent>{children}</AppLayoutContent>
            </ChatSessionProvider>
        </ProjectProvider>
    );
}
