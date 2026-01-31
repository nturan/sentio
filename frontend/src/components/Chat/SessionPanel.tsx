import { useState } from 'react';
import { useChatSessions } from '../../context/ChatSessionContext';
import { SessionItem } from './SessionItem';

export function SessionPanel() {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const { sessions, currentSession, isLoading, error, createNewSession, deleteSession, selectSession, updateSessionTitle } = useChatSessions();

    const handleNewChat = async () => {
        await createNewSession();
    };

    if (isCollapsed) {
        return (
            <div className="w-10 border-r border-gray-200 bg-gray-50 flex flex-col items-center py-3">
                <button
                    onClick={() => setIsCollapsed(false)}
                    className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                    title="Expand sessions"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                    </svg>
                </button>
            </div>
        );
    }

    return (
        <div className="w-56 border-r border-gray-200 bg-gray-50 flex flex-col h-full">
            {/* Header */}
            <div className="p-3 border-b border-gray-200 flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Chats</span>
                <button
                    onClick={() => setIsCollapsed(true)}
                    className="p-1 hover:bg-gray-200 rounded transition-colors"
                    title="Collapse"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                    </svg>
                </button>
            </div>

            {/* New Chat Button */}
            <div className="p-3">
                <button
                    onClick={handleNewChat}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Neuer Chat
                </button>
            </div>

            {/* Session List */}
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {isLoading && sessions.length === 0 ? (
                    <div className="text-center text-gray-400 text-sm py-4">Lädt...</div>
                ) : error ? (
                    <div className="text-center text-gray-400 text-xs py-4 px-2">
                        Server nicht erreichbar
                    </div>
                ) : sessions.length === 0 ? (
                    <div className="text-center text-gray-400 text-sm py-4">Keine Chats</div>
                ) : (
                    sessions.map(session => (
                        <SessionItem
                            key={session.id}
                            session={session}
                            isActive={currentSession?.id === session.id}
                            onSelect={() => selectSession(session)}
                            onDelete={() => deleteSession(session.id)}
                            onRename={(newTitle) => updateSessionTitle(session.id, newTitle)}
                        />
                    ))
                )}
            </div>
        </div>
    );
}
