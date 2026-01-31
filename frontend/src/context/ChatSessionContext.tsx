import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import type { ChatSession } from '../types/session';
import { listSessions, createSession, deleteSession as apiDeleteSession, updateSessionTitle as apiUpdateSessionTitle } from '../services/api';
import { useProjects } from './ProjectContext';

interface ChatSessionContextType {
    sessions: ChatSession[];
    currentSession: ChatSession | null;
    isLoading: boolean;
    error: string | null;
    selectSession: (session: ChatSession) => void;
    createNewSession: (title?: string) => Promise<ChatSession | null>;
    deleteSession: (sessionId: string) => Promise<void>;
    updateSessionTitle: (sessionId: string, title: string) => Promise<void>;
    refreshSessions: () => Promise<void>;
}

const ChatSessionContext = createContext<ChatSessionContextType | undefined>(undefined);

export function ChatSessionProvider({ children }: { children: ReactNode }) {
    const { selectedProject } = useProjects();
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const refreshSessions = useCallback(async () => {
        if (!selectedProject) {
            setSessions([]);
            setCurrentSession(null);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const fetchedSessions = await listSessions(selectedProject.id);
            setSessions(fetchedSessions);

            // If we have sessions, select the first (most recent)
            if (fetchedSessions.length > 0) {
                setCurrentSession(fetchedSessions[0]);
            } else {
                // Auto-create a session if none exist
                try {
                    const newSession = await createSession(selectedProject.id, { title: 'New Chat' });
                    setSessions([newSession]);
                    setCurrentSession(newSession);
                } catch (createErr) {
                    console.error('Failed to create initial session:', createErr);
                    // Still allow the app to function without a session
                    setCurrentSession(null);
                }
            }
        } catch (err) {
            console.error('Failed to load sessions:', err);
            setError(err instanceof Error ? err.message : 'Failed to load sessions');
            // Don't crash - just show empty state
            setSessions([]);
            setCurrentSession(null);
        } finally {
            setIsLoading(false);
        }
    }, [selectedProject]);

    // Load sessions when project changes
    useEffect(() => {
        if (selectedProject?.id) {
            setCurrentSession(null); // Reset current session when project changes
            refreshSessions().catch(err => {
                console.error('Error in refreshSessions:', err);
            });
        }
    }, [selectedProject?.id, refreshSessions]);

    const selectSession = useCallback((session: ChatSession) => {
        setCurrentSession(session);
    }, []);

    const createNewSession = useCallback(async (title?: string): Promise<ChatSession | null> => {
        if (!selectedProject) return null;

        try {
            const newSession = await createSession(selectedProject.id, { title: title || 'New Chat' });
            setSessions(prev => [newSession, ...prev]);
            setCurrentSession(newSession);
            return newSession;
        } catch (err) {
            console.error('Failed to create session:', err);
            setError(err instanceof Error ? err.message : 'Failed to create session');
            return null;
        }
    }, [selectedProject]);

    const deleteSessionHandler = useCallback(async (sessionId: string) => {
        try {
            await apiDeleteSession(sessionId);
            setSessions(prev => {
                const updated = prev.filter(s => s.id !== sessionId);
                // If we deleted the current session, switch to another
                if (currentSession?.id === sessionId) {
                    setCurrentSession(updated[0] || null);
                }
                return updated;
            });
        } catch (err) {
            console.error('Failed to delete session:', err);
            setError(err instanceof Error ? err.message : 'Failed to delete session');
        }
    }, [currentSession]);

    const updateSessionTitleHandler = useCallback(async (sessionId: string, title: string) => {
        try {
            const updatedSession = await apiUpdateSessionTitle(sessionId, title);
            setSessions(prev => prev.map(s =>
                s.id === sessionId ? { ...s, title: updatedSession.title } : s
            ));
            if (currentSession?.id === sessionId) {
                setCurrentSession(prev => prev ? { ...prev, title: updatedSession.title } : null);
            }
        } catch (err) {
            console.error('Failed to update session title:', err);
        }
    }, [currentSession]);

    return (
        <ChatSessionContext.Provider
            value={{
                sessions,
                currentSession,
                isLoading,
                error,
                selectSession,
                createNewSession,
                deleteSession: deleteSessionHandler,
                updateSessionTitle: updateSessionTitleHandler,
                refreshSessions
            }}
        >
            {children}
        </ChatSessionContext.Provider>
    );
}

export function useChatSessions() {
    const context = useContext(ChatSessionContext);
    if (context === undefined) {
        throw new Error('useChatSessions must be used within a ChatSessionProvider');
    }
    return context;
}
