export interface ChatSession {
    id: string;
    project_id: string;
    title: string;
    created_at: string;
    updated_at: string;
}

export interface SessionMessage {
    id: string;
    session_id: string;
    role: 'user' | 'assistant';
    content: string;
    created_at: string;
}

export interface SessionWithMessages extends ChatSession {
    messages: SessionMessage[];
}

export interface CreateSessionRequest {
    title?: string;
}

export interface CreateMessageRequest {
    role: 'user' | 'assistant';
    content: string;
}
