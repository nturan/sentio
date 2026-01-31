import { cn } from '../../utils/cn';
import type { Project } from '../../context/ProjectContext';

interface ProjectItemProps {
    project: Project;
    isSelected: boolean;
    onClick: () => void;
}

export function ProjectItem({ project, isSelected, onClick }: ProjectItemProps) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "w-12 h-12 rounded-xl flex items-center justify-center text-xl transition-all relative group shrink-0",
                isSelected
                    ? 'bg-blue-50 text-blue-600 ring-2 ring-blue-500'
                    : 'hover:bg-gray-100 text-gray-400'
            )}
            title={project.name}
        >
            {project.icon}

            {/* Tooltip */}
            <span className="absolute left-16 bg-gray-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                {project.name}
            </span>

            {/* Unread Badge (Optional - can be added when notifications are implemented) */}
        </button>
    );
}
