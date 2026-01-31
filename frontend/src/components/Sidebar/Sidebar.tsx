import { Sparkles, Loader2 } from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { ProjectItem } from './ProjectItem';
import { NewProjectButton } from './NewProjectButton';

interface SidebarProps {
    onStartNewProject: () => void;
}

export function Sidebar({ onStartNewProject }: SidebarProps) {
    const { projects, selectedProject, setSelectedProject, isLoading } = useProjects();

    return (
        <aside className="w-24 bg-white border-r border-gray-200 flex flex-col items-center py-4 gap-4 shadow-sm z-30 shrink-0">
            {/* App Logo/Icon */}
            <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg mb-2">
                <Sparkles size={24} />
            </div>

            {/* Project List */}
            <div className="w-full px-2 space-y-4 flex flex-col items-center overflow-y-auto flex-1">
                {isLoading ? (
                    <Loader2 size={20} className="text-gray-400 animate-spin mt-4" />
                ) : (
                    projects.map((project) => (
                        <ProjectItem
                            key={project.id}
                            project={project}
                            isSelected={selectedProject?.id === project.id}
                            onClick={() => setSelectedProject(project)}
                        />
                    ))
                )}
            </div>

            {/* New Project Button - always at bottom */}
            <div className="px-2">
                <NewProjectButton onClick={onStartNewProject} />
            </div>
        </aside>
    );
}
