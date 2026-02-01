import { useState, useCallback, useRef } from 'react';
import type { GeneratorChatMessage, CanvasData } from '../types/generatorChat';
import { postStream } from '../services/api';

const CANVAS_UPDATE_MARKER = '<<CANVAS_UPDATE>>';

interface UseGeneratorChatOptions<T extends CanvasData> {
    projectId: string;
    generatorType: 'recommendation' | 'insight' | 'survey';
    onCanvasUpdate: (updates: Partial<T>) => void;
}

export function useGeneratorChat<T extends CanvasData>(
    canvasData: T,
    options: UseGeneratorChatOptions<T>
) {
    const { projectId, generatorType, onCanvasUpdate } = options;

    const [messages, setMessages] = useState<GeneratorChatMessage[]>([]);
    const [isTyping, setIsTyping] = useState(false);
    const messagesRef = useRef<GeneratorChatMessage[]>([]);

    // Keep ref in sync with state for use in callbacks
    messagesRef.current = messages;

    const parseCanvasUpdate = useCallback((fullContent: string): { displayContent: string; updates: Partial<T> | null } => {
        const markerIndex = fullContent.indexOf(CANVAS_UPDATE_MARKER);

        if (markerIndex === -1) {
            return { displayContent: fullContent, updates: null };
        }

        const displayContent = fullContent.substring(0, markerIndex).trim();
        const jsonPart = fullContent.substring(markerIndex + CANVAS_UPDATE_MARKER.length).trim();

        try {
            // Try to parse the JSON
            const updates = JSON.parse(jsonPart) as Partial<T>;
            return { displayContent, updates };
        } catch {
            // JSON might be incomplete during streaming, return null
            return { displayContent, updates: null };
        }
    }, []);

    const sendMessage = useCallback(async (content: string) => {
        if (!content.trim()) return;

        // Create user message
        const userMessage: GeneratorChatMessage = {
            id: Date.now().toString(),
            role: 'user',
            content,
            timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, userMessage]);
        setIsTyping(true);

        // Prepare history for context (without canvas update markers)
        const history = messagesRef.current.map(m => ({
            role: m.role,
            content: m.content.split(CANVAS_UPDATE_MARKER)[0].trim()
        }));

        // Create placeholder for AI response
        const responseId = (Date.now() + 1).toString();
        let fullContent = '';
        let hasAppliedUpdate = false;

        const initialResponseMsg: GeneratorChatMessage = {
            id: responseId,
            role: 'assistant',
            content: '',
            timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, initialResponseMsg]);

        try {
            await postStream('/api/generator-chat', {
                body: {
                    message: content,
                    projectId,
                    generatorType,
                    canvasData,
                    history
                }
            }, (chunk: string) => {
                fullContent += chunk;

                // Parse for canvas updates
                const { displayContent, updates } = parseCanvasUpdate(fullContent);

                // Update the message display
                setMessages(prev => prev.map(m =>
                    m.id === responseId
                        ? { ...m, content: displayContent }
                        : m
                ));

                // Apply canvas update if found and not already applied
                if (updates && !hasAppliedUpdate) {
                    hasAppliedUpdate = true;
                    onCanvasUpdate(updates);
                }
            });

            // Final parse after stream completes
            const { displayContent, updates } = parseCanvasUpdate(fullContent);

            // Final message update with clean content
            setMessages(prev => prev.map(m =>
                m.id === responseId
                    ? { ...m, content: displayContent }
                    : m
            ));

            // Apply canvas update if not already applied
            if (updates && !hasAppliedUpdate) {
                onCanvasUpdate(updates);
            }

        } catch (error) {
            console.error('Generator chat error:', error);
            const errorMsg: GeneratorChatMessage = {
                id: (Date.now() + 2).toString(),
                role: 'assistant',
                content: 'Fehler bei der Verbindung zum AI-Service. Bitte versuchen Sie es erneut.',
                timestamp: new Date().toISOString(),
            };
            setMessages(prev => {
                // Remove the empty placeholder and add error message
                const filtered = prev.filter(m => m.id !== responseId);
                return [...filtered, errorMsg];
            });
        } finally {
            setIsTyping(false);
        }
    }, [projectId, generatorType, canvasData, parseCanvasUpdate, onCanvasUpdate]);

    const clearMessages = useCallback(() => {
        setMessages([]);
    }, []);

    return {
        messages,
        sendMessage,
        isTyping,
        clearMessages
    };
}
