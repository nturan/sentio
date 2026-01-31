
import { cn } from '../../utils/cn';
import type { Message } from '../../types/chat';

interface MessageBubbleProps {
    message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === 'user';

    return (
        <div className={cn("flex gap-4 animate-in fade-in slide-in-from-bottom-2", isUser ? 'flex-row-reverse' : '')}>
            {/* Avatar */}
            <div className={cn(
                "w-9 h-9 rounded-xl flex items-center justify-center font-bold text-[10px] shrink-0 shadow-sm",
                isUser ? 'bg-blue-600 text-white' : 'bg-indigo-600 text-white'
            )}>
                {isUser ? 'DU' : 'AI'}
            </div>

            {/* Content */}
            <div className={cn("max-w-[80%]", isUser ? 'text-right' : '')}>
                <p className="text-[10px] font-bold text-gray-400 uppercase mb-1.5 px-1">
                    {message.user}
                </p>

                <div className={cn(
                    "p-4 rounded-2xl text-sm shadow-sm leading-relaxed text-left",
                    isUser
                        ? (message.isImage ? 'bg-gray-100 text-gray-700 border border-gray-200' : 'bg-blue-600 text-white shadow-blue-100')
                        : 'bg-white border border-gray-100'
                )}>
                    {/* Legacy Image Support */}
                    {message.isImage && (
                        <div className="mb-2 w-full h-32 bg-gray-200 rounded-lg flex items-center justify-center text-gray-400 font-mono text-[10px] uppercase tracking-widest border border-gray-300 shadow-inner italic">
                            Workshop Foto Analyse läuft...
                        </div>
                    )}

                    <span className="whitespace-pre-wrap">{message.content}</span>

                    {/* Analysis Actions (Mock functionality) */}
                    {message.hasAnalysis && (
                        <div className="mt-4 pt-4 border-t border-gray-50 flex gap-2">
                            <button className="bg-blue-50 text-blue-600 px-3 py-1.5 rounded-lg text-[10px] font-bold hover:bg-blue-100 transition-colors">
                                Ja, wurde anerkannt
                            </button>
                            <button className="bg-gray-50 text-gray-600 px-3 py-1.5 rounded-lg text-[10px] font-bold hover:bg-gray-100 transition-colors">
                                Nein, wurde ignoriert
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
