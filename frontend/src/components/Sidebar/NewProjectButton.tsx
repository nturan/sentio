import { Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';

interface NewProjectButtonProps {
    onClick: () => void;
}

export function NewProjectButton({ onClick }: NewProjectButtonProps) {
    const { t } = useTranslation('navigation');

    return (
        <div className="w-full border-t border-gray-100 pt-3 px-2 shrink-0">
            <button
                onClick={onClick}
                className={cn(
                    "w-full px-2 py-2 rounded-lg border-2 border-dashed border-gray-200",
                    "flex items-center gap-3 text-gray-400",
                    "hover:border-blue-400 hover:text-blue-500 hover:bg-blue-50",
                    "transition-all"
                )}
            >
                <span className="w-9 h-9 rounded-lg flex items-center justify-center bg-gray-50 shrink-0">
                    <Plus size={18} />
                </span>
                <span className="text-sm font-medium">
                    {t('sidebar.newProject')}
                </span>
            </button>
        </div>
    );
}
