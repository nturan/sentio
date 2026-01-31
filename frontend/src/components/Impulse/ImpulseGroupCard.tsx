import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import type { StakeholderGroup } from '../../types/stakeholder';
import type { ImpulseEntry } from '../../types/impulse';
import { GROUP_TYPE_INFO } from '../../types/stakeholder';

interface ImpulseGroupCardProps {
    group: StakeholderGroup;
    impulses: ImpulseEntry[];
    indicatorCount: number;
    onManualAssessment: () => void;
    onCreateSurvey?: () => void;
}

export function ImpulseGroupCard({
    group,
    impulses,
    indicatorCount,
    onManualAssessment,
    onCreateSurvey
}: ImpulseGroupCardProps) {
    const [isExpanded, setIsExpanded] = useState(true);
    const typeInfo = GROUP_TYPE_INFO[group.group_type];
    const showSurveyButton = group.group_type === 'mitarbeitende' || group.group_type === 'multiplikatoren';

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('de-DE', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    };

    const formatRatings = (ratings: Record<string, number>) => {
        const entries = Object.entries(ratings);
        if (entries.length <= 2) {
            return entries.map(([key, value]) => `${key}: ${value}`).join(', ');
        }
        return `${entries.length} Bewertungen`;
    };

    return (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            {/* Header */}
            <div
                className="px-5 py-4 flex items-center justify-between cursor-pointer hover:bg-gray-50"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-3">
                    <span className="text-2xl">{typeInfo?.icon || '👤'}</span>
                    <div>
                        <h3 className="font-semibold text-gray-800">
                            {typeInfo?.name || group.group_type}
                            {group.name && <span className="text-gray-500"> - {group.name}</span>}
                        </h3>
                        <p className="text-sm text-gray-500">
                            {group.mendelow_quadrant} | {indicatorCount} Bewertungsfaktoren
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {impulses.length > 0 && (
                        <span className="text-sm font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                            Aktuell: {impulses[0].average_rating.toFixed(1)}
                        </span>
                    )}
                    {isExpanded ? (
                        <ChevronUp size={20} className="text-gray-400" />
                    ) : (
                        <ChevronDown size={20} className="text-gray-400" />
                    )}
                </div>
            </div>

            {/* Content */}
            {isExpanded && (
                <div className="px-5 pb-4">
                    {/* Impulse History */}
                    <div className="bg-gray-50 rounded-lg p-4 mb-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Letzte Impulse:</h4>
                        {impulses.length === 0 ? (
                            <p className="text-sm text-gray-500 italic">Noch keine Bewertungen vorhanden</p>
                        ) : (
                            <ul className="space-y-1">
                                {impulses.map((impulse, idx) => (
                                    <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                                        <span className="text-gray-400">•</span>
                                        <span>
                                            <strong>{formatDate(impulse.date)}:</strong> Durchschnitt {impulse.average_rating.toFixed(1)}
                                            {impulse.source === 'survey' && (
                                                <span className="ml-1 text-xs text-purple-600">(aus Umfrage)</span>
                                            )}
                                            <span className="text-gray-400 ml-1">
                                                ({formatRatings(impulse.ratings)})
                                            </span>
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onManualAssessment();
                            }}
                            className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                        >
                            Manuelle Bewertung
                        </button>
                        {showSurveyButton && onCreateSurvey && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onCreateSurvey();
                                }}
                                className="px-4 py-2 text-sm font-medium text-purple-700 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
                            >
                                Umfrage erstellen
                            </button>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
