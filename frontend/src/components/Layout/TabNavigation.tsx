import { MessageSquare, Activity, Users, Settings, UserCircle, Zap, Lightbulb } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useProjects } from '../../context/ProjectContext';

interface TabNavigationProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
}

export function TabNavigation({ activeTab, onTabChange }: TabNavigationProps) {
    const { selectedProject } = useProjects();

    const tabs = [
        { id: 'chat', label: 'Konversation', icon: <MessageSquare size={14} /> },
        { id: 'dashboard', label: 'Dashboard', icon: <Activity size={14} /> },
        { id: 'impulse', label: 'Impulse', icon: <Zap size={14} /> },
        { id: 'recommendations', label: 'Handlungen', icon: <Lightbulb size={14} /> },
        { id: 'stakeholder', label: 'Stakeholder', icon: <Users size={14} /> },
        { id: 'settings', label: 'Einstellungen', icon: <Settings size={14} /> },
    ];

    return (
        <header className="bg-gray-100 pt-2 px-2 flex items-end border-b border-gray-200 shrink-0">
            {/* Project Name */}
            {selectedProject && (
                <div className="flex items-center gap-2 px-4 mb-2 mr-4">
                    <span className="text-xl">{selectedProject.icon}</span>
                    <span className="text-sm font-bold text-gray-800">{selectedProject.name}</span>
                </div>
            )}

            <div className="flex-1 flex items-end gap-1">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => onTabChange(tab.id)}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2.5 rounded-t-lg text-[11px] font-bold transition-all",
                            activeTab === tab.id
                                ? 'bg-white text-blue-700 shadow-sm border-x border-t border-gray-200'
                                : 'text-gray-500 hover:bg-gray-50'
                        )}
                    >
                        {tab.icon} {tab.label}
                    </button>
                ))}
            </div>

            <div className="flex items-center gap-4 px-4 mb-2">
                <UserCircle size={24} className="text-gray-400" />
            </div>
        </header>
    );
}
