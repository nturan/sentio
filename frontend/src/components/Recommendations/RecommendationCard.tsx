import { Check, Play, X, Edit2, RefreshCw, BarChart2, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { Recommendation, RecommendationStatus } from '../../types/recommendation';
import { RECOMMENDATION_TYPE_INFO } from '../../types/recommendation';
import type { StakeholderGroup } from '../../types/stakeholder';

interface RecommendationCardProps {
    recommendation: Recommendation;
    stakeholderGroups: StakeholderGroup[];
    onApprove: (id: string) => void;
    onReject: (id: string) => void;
    onStart: (id: string) => void;
    onComplete: (id: string) => void;
    onEdit: (recommendation: Recommendation) => void;
    onRegenerate: (recommendation: Recommendation) => void;
    onMeasureImpact: (recommendation: Recommendation) => void;
}

export function RecommendationCard({
    recommendation,
    stakeholderGroups,
    onApprove,
    onReject,
    onStart,
    onComplete,
    onEdit,
    onRegenerate,
    onMeasureImpact
}: RecommendationCardProps) {
    const { t } = useTranslation('recommendations');
    const { t: tCommon } = useTranslation('common');
    const { t: tEnums } = useTranslation('enums');
    const [isExpanded, setIsExpanded] = useState(false);
    const typeInfo = RECOMMENDATION_TYPE_INFO[recommendation.recommendation_type];

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        const locale = import.meta.env.VITE_LOCALE === 'de' ? 'de-DE' : 'en-US';
        return date.toLocaleDateString(locale, {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    };

    const getAffectedGroupsDisplay = () => {
        if (recommendation.affected_groups.includes('all')) {
            return tCommon('all');
        }
        return recommendation.affected_groups
            .map(id => {
                const group = stakeholderGroups.find(g => g.id === id);
                if (group) {
                    return group.name || tEnums(`stakeholderTypes.${group.group_type}.name`, { defaultValue: group.group_type });
                }
                return id;
            })
            .join(', ');
    };

    const getStatusBorderColor = (status: RecommendationStatus) => {
        switch (status) {
            case 'pending_approval': return 'border-l-yellow-400';
            case 'approved': return 'border-l-green-400';
            case 'rejected': return 'border-l-red-400';
            case 'started': return 'border-l-blue-400';
            case 'completed': return 'border-l-gray-400';
            default: return 'border-l-gray-300';
        }
    };

    const getPriorityBadgeColor = () => {
        switch (recommendation.priority) {
            case 'high': return 'bg-red-100 text-red-700';
            case 'medium': return 'bg-yellow-100 text-yellow-700';
            case 'low': return 'bg-green-100 text-green-700';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    return (
        <div className={`bg-white rounded-lg border border-gray-200 border-l-4 ${getStatusBorderColor(recommendation.status)} shadow-sm overflow-hidden`}>
            {/* Header - Clickable to expand/collapse */}
            <div
                className="px-4 py-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                        <span className="text-lg">{tEnums(`recommendationStatus.${recommendation.status}.icon`, { defaultValue: '📋' })}</span>
                        <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                                    {tEnums(`recommendationStatus.${recommendation.status}.label`)}
                                </span>
                                <span className="text-lg" title={typeInfo.description}>{typeInfo.icon}</span>
                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPriorityBadgeColor()}`}>
                                    {tEnums(`priority.${recommendation.priority}`)}
                                </span>
                            </div>
                            <h3 className="text-base font-semibold text-gray-800 truncate">
                                {recommendation.title}
                            </h3>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                        {isExpanded ? (
                            <ChevronUp size={20} className="text-gray-400" />
                        ) : (
                            <ChevronDown size={20} className="text-gray-400" />
                        )}
                    </div>
                </div>
            </div>

            {/* Expandable Content */}
            {isExpanded && (
                <>
                    {/* Content */}
                    <div className="p-4">
                        {recommendation.description && (
                            <p className="text-sm text-gray-600 mb-3">
                                {recommendation.description}
                            </p>
                        )}

                        {/* Steps (full list when expanded) */}
                        {recommendation.steps && recommendation.steps.length > 0 && (
                            <div className="mb-3">
                                <p className="text-xs font-medium text-gray-500 mb-1">{t('meta.steps')}</p>
                                <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
                                    {recommendation.steps.map((step, idx) => (
                                        <li key={idx}>{step}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Meta info */}
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
                            <span>{t('meta.affects')} {getAffectedGroupsDisplay()}</span>
                            <span>{t('meta.created')} {formatDate(recommendation.created_at)}</span>
                            {recommendation.status === 'approved' && recommendation.approved_at && (
                                <span>{t('meta.approved')} {formatDate(recommendation.approved_at)}</span>
                            )}
                            {recommendation.status === 'started' && recommendation.started_at && (
                                <span>{t('meta.started')} {formatDate(recommendation.started_at)}</span>
                            )}
                            {recommendation.status === 'completed' && recommendation.completed_at && (
                                <span>{t('meta.completed')} {formatDate(recommendation.completed_at)}</span>
                            )}
                        </div>

                        {/* Rejection reason */}
                        {recommendation.status === 'rejected' && recommendation.rejection_reason && (
                            <div className="mt-3 p-2 bg-red-50 rounded text-sm text-red-700">
                                <span className="font-medium">{t('meta.reason')}</span> {recommendation.rejection_reason}
                            </div>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 flex flex-wrap gap-2">
                {recommendation.status === 'pending_approval' && (
                    <>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onApprove(recommendation.id);
                            }}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700 transition-colors"
                        >
                            <Check size={14} />
                            {t('actions.approve')}
                        </button>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onReject(recommendation.id);
                            }}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 text-white rounded text-sm font-medium hover:bg-red-700 transition-colors"
                        >
                            <X size={14} />
                            {t('actions.reject')}
                        </button>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onEdit(recommendation);
                            }}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-200 text-gray-700 rounded text-sm font-medium hover:bg-gray-300 transition-colors"
                        >
                            <Edit2 size={14} />
                            {t('actions.edit')}
                        </button>
                    </>
                )}

                {recommendation.status === 'approved' && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onStart(recommendation.id);
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 transition-colors"
                    >
                        <Play size={14} />
                        {t('actions.start')}
                    </button>
                )}

                {recommendation.status === 'started' && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onComplete(recommendation.id);
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700 transition-colors"
                    >
                        <Check size={14} />
                        {t('actions.markCompleted')}
                    </button>
                )}

                {recommendation.status === 'completed' && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onMeasureImpact(recommendation);
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white rounded text-sm font-medium hover:bg-purple-700 transition-colors"
                    >
                        <BarChart2 size={14} />
                        {t('actions.measureImpact')}
                    </button>
                )}

                {recommendation.status === 'rejected' && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onRegenerate(recommendation);
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 transition-colors"
                    >
                        <RefreshCw size={14} />
                        {t('actions.regenerate')}
                    </button>
                )}
            </div>
                </>
            )}
        </div>
    );
}
