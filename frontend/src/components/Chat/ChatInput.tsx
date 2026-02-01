import { useState, type KeyboardEvent } from 'react';
import { Send, Image as ImageIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from '../common/Button';

interface ChatInputProps {
    onSend: (message: string) => void;
    isLoading?: boolean;
}

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
    const [value, setValue] = useState('');
    const { t } = useTranslation('chat');

    const handleSend = () => {
        if (value.trim()) {
            onSend(value);
            setValue('');
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    };

    return (
        <div className="p-6 bg-white border-t border-gray-100 shadow-2xl z-10">
            <div className="max-w-3xl mx-auto space-y-4">
                {/* Recommended Actions could go here */}

                <div className="flex gap-3 relative items-center">
                    <button
                        className="p-3 bg-gray-50 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all border border-gray-100"
                        title={t('upload')}
                    >
                        <ImageIcon size={20} />
                    </button>

                    <input
                        className="flex-1 bg-gray-50 border border-gray-200 rounded-2xl py-4 px-6 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                        placeholder={t('inputPlaceholder')}
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isLoading}
                    />

                    <Button
                        onClick={handleSend}
                        disabled={!value.trim() || isLoading}
                        className="rounded-2xl h-auto py-4 px-4"
                    >
                        <Send size={20} />
                    </Button>
                </div>
            </div>
        </div>
    );
}
