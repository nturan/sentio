import { useState, useCallback, useEffect, useRef } from 'react';
import type { Message } from '../types/chat';
import { API_CONFIG, postStream, getSession, saveMessage } from '../services/api';

const WELCOME_MESSAGE: Message = {
    id: 'welcome',
    role: 'assistant',
    user: 'AI Assistant',
    content: 'Willkommen zurück! Ich habe die neuesten Workshop-Ergebnisse analysiert. Es gibt Klärungsbedarf bei der IT-Führungsebene. Wie möchtest du fortfahren?',
    timestamp: new Date().toISOString(),
};

// Generate a short title from message content
function generateTitle(content: string): string {
    // Take first 40 chars, cut at last word boundary
    const maxLength = 40;
    if (content.length <= maxLength) return content;

    const truncated = content.substring(0, maxLength);
    const lastSpace = truncated.lastIndexOf(' ');
    return (lastSpace > 20 ? truncated.substring(0, lastSpace) : truncated) + '...';
}

interface UseChatOptions {
    onUpdateSessionTitle?: (sessionId: string, title: string) => Promise<void>;
    onMessageComplete?: () => void;
}

export function useChat(projectId: string, sessionId: string | null, options: UseChatOptions = {}) {
    const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
    const [isTyping, setIsTyping] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const lastSessionIdRef = useRef<string | null>(null);
    const hasGeneratedTitleRef = useRef<Set<string>>(new Set());

    // Load messages when session changes
    useEffect(() => {
        if (!sessionId || sessionId === lastSessionIdRef.current) return;

        lastSessionIdRef.current = sessionId;
        setIsLoading(true);

        getSession(sessionId)
            .then(session => {
                if (session.messages.length === 0) {
                    // New session - show welcome message
                    setMessages([WELCOME_MESSAGE]);
                } else {
                    // Convert session messages to Message format
                    const loadedMessages: Message[] = session.messages.map(m => ({
                        id: m.id,
                        role: m.role,
                        user: m.role === 'user' ? 'Du' : 'AI Assistant',
                        content: m.content,
                        timestamp: m.created_at,
                    }));
                    setMessages(loadedMessages);
                }
            })
            .catch(err => {
                console.error('Failed to load session messages:', err);
                setMessages([WELCOME_MESSAGE]);
            })
            .finally(() => {
                setIsLoading(false);
            });
    }, [sessionId]);

    const sendMessage = useCallback(async (content: string) => {
        if (!sessionId) {
            console.error('No session selected');
            return;
        }

        const newMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            user: 'Du',
            content,
            timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, newMessage]);
        setIsTyping(true);

        // Save user message to backend
        try {
            await saveMessage(sessionId, { role: 'user', content });

            // Generate title on first user message
            if (options.onUpdateSessionTitle && !hasGeneratedTitleRef.current.has(sessionId)) {
                // Check if this is the first user message (only welcome message exists)
                const userMessages = messages.filter(m => m.role === 'user');
                if (userMessages.length === 0) {
                    hasGeneratedTitleRef.current.add(sessionId);
                    const title = generateTitle(content);
                    options.onUpdateSessionTitle(sessionId, title).catch(err => {
                        console.error('Failed to update session title:', err);
                    });
                }
            }
        } catch (err) {
            console.error('Failed to save user message:', err);
        }

        try {
            // Prepare history for context
            const history = messages.map(m => ({ role: m.role, content: m.content }));

            // Create placeholder for AI response
            const responseId = (Date.now() + 1).toString();
            let fullContent = '';

            const initialResponseMsg: Message = {
                id: responseId,
                role: 'assistant',
                user: 'AI Assistant',
                content: '',
                timestamp: new Date().toISOString(),
            };

            setMessages(prev => [...prev, initialResponseMsg]);

            // Call chat API with streaming
            await postStream(API_CONFIG.chat, {
                body: {
                    message: content,
                    projectId,
                    history
                }
            }, (chunk: string) => {
                fullContent += chunk;
                setMessages(prev => prev.map(m =>
                    m.id === responseId
                        ? { ...m, content: fullContent }
                        : m
                ));
            });

            // Save assistant response to backend
            if (fullContent) {
                try {
                    await saveMessage(sessionId, { role: 'assistant', content: fullContent });
                } catch (err) {
                    console.error('Failed to save assistant message:', err);
                }
            }

            // Trigger refresh callback after message exchange completes
            if (options.onMessageComplete) {
                options.onMessageComplete();
            }
        } catch (error) {
            console.error('Chat error:', error);
            const errorMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                user: 'System',
                content: 'Fehler bei der Verbindung zum AI-Service. Bitte überprüfen Sie Ihre Verbindung.',
                timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsTyping(false);
        }
    }, [messages, projectId, sessionId, options.onUpdateSessionTitle]);

    return {
        messages,
        sendMessage,
        isTyping,
        isLoading
    };
}
