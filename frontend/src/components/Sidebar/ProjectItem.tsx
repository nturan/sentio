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
                "w-full px-2 py-2 rounded-lg flex items-center gap-3 transition-all",
                isSelected
                    ? 'bg-blue-50 text-blue-600'
                    : 'hover:bg-gray-100 text-gray-600'
            )}
        >
            <span className={cn(
                "w-9 h-9 rounded-lg flex items-center justify-center text-lg shrink-0",
                isSelected ? 'bg-blue-100' : 'bg-gray-100'
            )}>
                {project.icon}
            </span>
            <span className={cn(
                "text-sm font-medium truncate text-left",
                isSelected ? 'text-blue-700' : 'text-gray-700'
            )}>
                {project.name}
            </span>
        </button>
    );
}
