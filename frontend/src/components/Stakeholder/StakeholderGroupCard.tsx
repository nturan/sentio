import { MoreVertical, Trash2, Edit2, Zap } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { StakeholderGroup } from '../../types/stakeholder';
import { GROUP_TYPE_INFO, MENDELOW_QUADRANTS } from '../../types/stakeholder';

interface StakeholderGroupCardProps {
    group: StakeholderGroup;
    onSelect: () => void;
    onDelete: () => void;
    onStartImpulse?: () => void;
}

export function StakeholderGroupCard({ group, onSelect, onDelete, onStartImpulse }: StakeholderGroupCardProps) {
    const { t } = useTranslation('stakeholder');
    const { t: tEnums } = useTranslation('enums');
    const [showMenu, setShowMenu] = useState(false);

    const typeInfo = GROUP_TYPE_INFO[group.group_type];
    const typeName = tEnums(`stakeholderTypes.${group.group_type}.name`);
    const typeSubtitle = tEnums(`stakeholderTypes.${group.group_type}.subtitle`);
    const quadrantInfo = MENDELOW_QUADRANTS[group.mendelow_quadrant as keyof typeof MENDELOW_QUADRANTS] ||
        MENDELOW_QUADRANTS['Monitor'];

    return (
        <div className={`bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow`}>
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">{typeInfo.icon}</span>
                    <div>
                        <h3 className="font-semibold text-gray-800">
                            {group.name || typeName}
                        </h3>
                        <p className="text-xs text-gray-500">
                            {group.name ? `${typeName} - ${typeSubtitle}` : typeSubtitle}
                        </p>
                    </div>
                </div>

                <div className="relative">
                    <button
                        onClick={() => setShowMenu(!showMenu)}
                        className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
                    >
                        <MoreVertical size={16} />
                    </button>

                    {showMenu && (
                        <>
                            <div
                                className="fixed inset-0 z-10"
                                onClick={() => setShowMenu(false)}
                            />
                            <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1 min-w-[140px]">
                                <button
                                    onClick={() => {
                                        setShowMenu(false);
                                        onSelect();
                                    }}
                                    className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                                >
                                    <Edit2 size={14} />
                                    {t('card.showDetails')}
                                </button>
                                <button
                                    onClick={() => {
                                        setShowMenu(false);
                                        onDelete();
                                    }}
                                    className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                                >
                                    <Trash2 size={14} />
                                    {t('card.delete')}
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Mendelow Badge */}
            <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mb-3 ${quadrantInfo.color} ${quadrantInfo.textColor}`}>
                {group.mendelow_quadrant}
            </div>

            {/* Notes preview */}
            {group.notes && (
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {group.notes}
                </p>
            )}

            {/* Action button */}
            {onStartImpulse && (
                <button
                    onClick={onStartImpulse}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-sm font-medium"
                >
                    <Zap size={16} />
                    {t('newImpulse')}
                </button>
            )}
        </div>
    );
}
