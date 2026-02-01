import { Loader2 } from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { ProjectItem } from './ProjectItem';
import { NewProjectButton } from './NewProjectButton';

interface SidebarProps {
    onStartNewProject: () => void;
}

export function Sidebar({ onStartNewProject }: SidebarProps) {
    const { projects, selectedProject, setSelectedProject, isLoading } = useProjects();

    return (
        <aside className="w-[300px] bg-white border-r border-gray-200 flex flex-col py-4 gap-2 shadow-sm z-30 shrink-0">
            {/* App Logo/Icon */}
            <div className="flex items-center gap-3 px-4">
                <img src="/sentio.svg" alt="Sentio" className="w-10 h-10 shrink-0" />
                <span className="text-sm font-semibold text-gray-800 leading-tight">
                    Sentio Intelligence
                </span>
            </div>

            {/* Separator */}
            <div className="h-px bg-gray-200 mx-4 my-2" />

            {/* Projects Section Title */}
            <span className="text-[10px] font-medium text-gray-400 uppercase tracking-wider px-4">
                Projekte
            </span>

            {/* Project List */}
            <div className="w-full px-2 space-y-1 flex flex-col overflow-y-auto flex-1">
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
