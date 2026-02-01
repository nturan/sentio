import { useTranslation } from 'react-i18next';
import type { StakeholderGroup } from '../../types/stakeholder';
import { GROUP_TYPE_INFO } from '../../types/stakeholder';

interface MendelowMatrixProps {
    groups: StakeholderGroup[];
    onSelectGroup: (groupId: string) => void;
}

export function MendelowMatrix({ groups, onSelectGroup }: MendelowMatrixProps) {
    const { t } = useTranslation('stakeholder');

    // Categorize groups into quadrants
    const getQuadrantGroups = (power: 'high' | 'low', interest: 'high' | 'low') => {
        return groups.filter(g => g.power_level === power && g.interest_level === interest);
    };

    const renderQuadrant = (
        title: string,
        subtitle: string,
        power: 'high' | 'low',
        interest: 'high' | 'low',
        bgColor: string
    ) => {
        const quadrantGroups = getQuadrantGroups(power, interest);

        return (
            <div className={`${bgColor} p-3 rounded-lg min-h-[120px]`}>
                <div className="text-xs font-bold text-gray-700 mb-1">{title}</div>
                <div className="text-[10px] text-gray-500 mb-2">{subtitle}</div>
                <div className="space-y-1">
                    {quadrantGroups.map(group => {
                        const typeInfo = GROUP_TYPE_INFO[group.group_type];
                        return (
                            <button
                                key={group.id}
                                onClick={() => onSelectGroup(group.id)}
                                className="w-full text-left px-2 py-1 bg-white rounded text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-1 shadow-sm"
                            >
                                <span>{typeInfo.icon}</span>
                                <span className="truncate">{group.name || typeInfo.name}</span>
                            </button>
                        );
                    })}
                    {quadrantGroups.length === 0 && (
                        <div className="text-[10px] text-gray-400 italic">{t('mendelow.noGroups')}</div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('mendelow.title')}</h3>

            <div className="relative">
                {/* Y-axis label */}
                <div className="absolute -left-1 top-1/2 -translate-y-1/2 -rotate-90 text-[10px] font-medium text-gray-500 whitespace-nowrap">
                    {t('mendelow.power')}
                </div>

                {/* X-axis label */}
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-[10px] font-medium text-gray-500">
                    {t('mendelow.interest')}
                </div>

                <div className="ml-4 mb-4">
                    {/* High/Low indicators */}
                    <div className="flex justify-between mb-1 px-2">
                        <span className="text-[10px] text-gray-400">{t('common:levels.low')}</span>
                        <span className="text-[10px] text-gray-400">{t('common:levels.high')}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                        {/* Top row (High Power) */}
                        {renderQuadrant(
                            t('mendelow.quadrants.keepSatisfied.title'),
                            t('mendelow.quadrants.keepSatisfied.strategy'),
                            'high',
                            'low',
                            'bg-yellow-50'
                        )}
                        {renderQuadrant(
                            t('mendelow.quadrants.keyPlayers.title'),
                            t('mendelow.quadrants.keyPlayers.strategy'),
                            'high',
                            'high',
                            'bg-red-50'
                        )}

                        {/* Bottom row (Low Power) */}
                        {renderQuadrant(
                            t('mendelow.quadrants.monitor.title'),
                            t('mendelow.quadrants.monitor.strategy'),
                            'low',
                            'low',
                            'bg-gray-50'
                        )}
                        {renderQuadrant(
                            t('mendelow.quadrants.keepInformed.title'),
                            t('mendelow.quadrants.keepInformed.strategy'),
                            'low',
                            'high',
                            'bg-blue-50'
                        )}
                    </div>

                    {/* Power level indicators */}
                    <div className="flex flex-col justify-between absolute left-0 top-8 bottom-8 text-[10px] text-gray-400">
                        <span>{t('common:levels.high')}</span>
                        <span>{t('common:levels.low')}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
