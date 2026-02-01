import { useRef, useEffect, useState, type KeyboardEvent } from 'react';
import { Send, Loader2, MessageSquare } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { GeneratorChatMessage } from '../../types/generatorChat';
import { cn } from '../../utils/cn';

interface GeneratorChatPanelProps {
    messages: GeneratorChatMessage[];
    onSendMessage: (content: string) => void;
    isTyping: boolean;
    placeholder?: string;
}

function CompactMessageBubble({ message, userLabel }: { message: GeneratorChatMessage; userLabel: string }) {
    const isUser = message.role === 'user';

    return (
        <div className={cn("flex gap-2", isUser ? 'flex-row-reverse' : '')}>
            {/* Small Avatar */}
            <div className={cn(
                "w-6 h-6 rounded-full flex items-center justify-center text-[8px] font-bold shrink-0",
                isUser ? 'bg-blue-600 text-white' : 'bg-indigo-600 text-white'
            )}>
                {isUser ? userLabel.substring(0, 2).toUpperCase() : 'AI'}
            </div>

            {/* Content */}
            <div className={cn(
                "max-w-[85%] px-3 py-2 rounded-xl text-sm leading-relaxed",
                isUser
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-700'
            )}>
                <span className="whitespace-pre-wrap">{message.content}</span>
            </div>
        </div>
    );
}

function TypingIndicator() {
    return (
        <div className="flex gap-2">
            <div className="w-6 h-6 rounded-full flex items-center justify-center text-[8px] font-bold shrink-0 bg-indigo-600 text-white">
                AI
            </div>
            <div className="bg-white border border-gray-200 px-3 py-2 rounded-xl">
                <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
            </div>
        </div>
    );
}

export function GeneratorChatPanel({
    messages,
    onSendMessage,
    isTyping,
    placeholder
}: GeneratorChatPanelProps) {
    const { t } = useTranslation('chat');
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const userLabel = t('userLabel');
    const actualPlaceholder = placeholder || t('generator.placeholder');

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isTyping]);

    const handleSend = () => {
        if (input.trim() && !isTyping) {
            onSendMessage(input.trim());
            setInput('');
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }} className="bg-gray-50 border-l border-gray-200">
            {/* Header */}
            <div style={{ flexShrink: 0 }} className="px-4 py-3 border-b border-gray-200 bg-white">
                <div className="flex items-center gap-2">
                    <MessageSquare size={16} className="text-indigo-600" />
                    <h3 className="text-sm font-semibold text-gray-800">{t('generator.title')}</h3>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                    {t('generator.subtitle')}
                </p>
            </div>

            {/* Messages */}
            <div style={{ flex: '1 1 0%', minHeight: 0, overflowY: 'auto' }} className="p-4 space-y-3">
                {messages.length === 0 && !isTyping && (
                    <div className="text-center py-8">
                        <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-indigo-100 flex items-center justify-center">
                            <MessageSquare size={20} className="text-indigo-600" />
                        </div>
                        <p className="text-sm text-gray-500 max-w-[200px] mx-auto">
                            {t('generator.emptyState')}
                        </p>
                        <div className="mt-4 space-y-2">
                            <p className="text-xs text-gray-400">{t('generator.examples')}</p>
                            <div className="space-y-1">
                                <button
                                    onClick={() => onSendMessage(t('generator.exampleQuestions.stakeholders'))}
                                    className="text-xs text-indigo-600 hover:text-indigo-700 hover:underline block mx-auto"
                                    disabled={isTyping}
                                >
                                    "{t('generator.exampleQuestions.stakeholders')}"
                                </button>
                                <button
                                    onClick={() => onSendMessage(t('generator.exampleQuestions.priority'))}
                                    className="text-xs text-indigo-600 hover:text-indigo-700 hover:underline block mx-auto"
                                    disabled={isTyping}
                                >
                                    "{t('generator.exampleQuestions.priority')}"
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {messages.map(message => (
                    <CompactMessageBubble key={message.id} message={message} userLabel={userLabel} />
                ))}

                {isTyping && <TypingIndicator />}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div style={{ flexShrink: 0 }} className="p-3 border-t border-gray-200 bg-white">
                <div className="flex items-center gap-2">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={actualPlaceholder}
                        disabled={isTyping}
                        className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || isTyping}
                        className="p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isTyping ? (
                            <Loader2 size={18} className="animate-spin" />
                        ) : (
                            <Send size={18} />
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
