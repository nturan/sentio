import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { listProjects, createProject as apiCreateProject, type ProjectData, type CreateProjectRequest } from '../services/api';

// Types
export interface Project {
    id: string;
    name: string;
    icon: string;
    goal?: string;
}

interface ProjectContextType {
    projects: Project[];
    selectedProject: Project | null;
    isLoading: boolean;
    error: string | null;
    setSelectedProject: (project: Project) => void;
    addProject: (project: Omit<Project, 'id'>) => Promise<Project>;
    refreshProjects: () => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
    const [projects, setProjects] = useState<Project[]>([]);
    const [selectedProject, setSelectedProject] = useState<Project | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const refreshProjects = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const fetchedProjects = await listProjects();
            const mappedProjects: Project[] = fetchedProjects.map(p => ({
                id: p.id,
                name: p.name,
                icon: p.icon,
                goal: p.goal
            }));
            setProjects(mappedProjects);

            // Select first project if none selected
            if (mappedProjects.length > 0 && !selectedProject) {
                setSelectedProject(mappedProjects[0]);
            } else if (selectedProject) {
                // Keep current selection if it still exists
                const exists = mappedProjects.find(p => p.id === selectedProject.id);
                if (!exists && mappedProjects.length > 0) {
                    setSelectedProject(mappedProjects[0]);
                } else if (!exists) {
                    setSelectedProject(null);
                }
            }
        } catch (err) {
            console.error('Failed to load projects:', err);
            setError(err instanceof Error ? err.message : 'Failed to load projects');
        } finally {
            setIsLoading(false);
        }
    }, [selectedProject]);

    // Load projects on mount
    useEffect(() => {
        refreshProjects();
    }, []);

    const addProject = useCallback(async (projectData: Omit<Project, 'id'>): Promise<Project> => {
        try {
            const request: CreateProjectRequest = {
                name: projectData.name,
                icon: projectData.icon,
                goal: projectData.goal
            };
            const created = await apiCreateProject(request);
            const newProject: Project = {
                id: created.id,
                name: created.name,
                icon: created.icon,
                goal: created.goal
            };
            setProjects(prev => [newProject, ...prev]);
            setSelectedProject(newProject);
            return newProject;
        } catch (err) {
            console.error('Failed to create project:', err);
            throw err;
        }
    }, []);

    return (
        <ProjectContext.Provider
            value={{
                projects,
                selectedProject,
                isLoading,
                error,
                setSelectedProject,
                addProject,
                refreshProjects
            }}
        >
            {children}
        </ProjectContext.Provider>
    );
}

export function useProjects() {
    const context = useContext(ProjectContext);
    if (context === undefined) {
        throw new Error('useProjects must be used within a ProjectProvider');
    }
    return context;
}
