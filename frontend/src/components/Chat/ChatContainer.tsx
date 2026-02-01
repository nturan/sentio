import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useChat } from '../../hooks/useChat';
import { useChatSessions } from '../../context/ChatSessionContext';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { SessionPanel } from './SessionPanel';

interface ChatContainerProps {
    projectId: string;
}

export function ChatContainer({ projectId }: ChatContainerProps) {
    const { t } = useTranslation('chat');
    const { currentSession, isLoading: isSessionLoading, error: sessionError, updateSessionTitle } = useChatSessions();
    const bottomRef = useRef<HTMLDivElement>(null);

    const { messages, sendMessage, isTyping } = useChat(projectId, currentSession?.id || null, {
        onUpdateSessionTitle: updateSessionTitle
    });

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="flex-1 flex overflow-hidden h-full">
            <SessionPanel />

            <div className="flex-1 flex flex-col overflow-hidden">
                {isSessionLoading && !currentSession ? (
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-gray-400 text-sm">{t('loading')}</div>
                    </div>
                ) : sessionError ? (
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-center text-gray-500">
                            <p className="text-sm">{t('loadError')}</p>
                            <p className="text-xs mt-1">{t('loadErrorHint')}</p>
                        </div>
                    </div>
                ) : (
                    <>
                        <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-6 max-w-4xl mx-auto w-full">
                            {messages.map((msg) => (
                                <MessageBubble key={msg.id} message={msg} />
                            ))}

                            {isTyping && (
                                <div className="flex gap-4 animate-pulse">
                                    <div className="w-9 h-9 rounded-xl bg-gray-200 shrink-0"></div>
                                    <div className="bg-gray-100 p-4 rounded-2xl text-[10px] font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
                                        ...
                                    </div>
                                </div>
                            )}

                            <div ref={bottomRef} />
                        </div>

                        <ChatInput onSend={sendMessage} isLoading={isTyping} />
                    </>
                )}
            </div>
        </div>
    );
}
