
import { Plus } from 'lucide-react';
import { cn } from '../../utils/cn';

interface NewProjectButtonProps {
    onClick: () => void;
}

export function NewProjectButton({ onClick }: NewProjectButtonProps) {
    return (
        <div className="w-full border-t border-gray-100 my-2 pt-4 flex flex-col items-center gap-1 shrink-0">
            <button
                onClick={onClick}
                className={cn(
                    "w-12 h-12 rounded-xl border-2 border-dashed border-gray-200",
                    "flex items-center justify-center text-gray-400",
                    "hover:border-blue-400 hover:text-blue-500 hover:bg-blue-50",
                    "transition-all group relative"
                )}
            >
                <Plus size={20} />
                <span className="absolute left-16 bg-blue-600 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50 font-bold shadow-sm">
                    Neues Projekt
                </span>
            </button>
            <span className="text-[8px] font-black text-gray-300 uppercase text-center leading-tight">
                Neues<br />Projekt
            </span>
        </div>
    );
}
