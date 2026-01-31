import { Check, Play, X, Edit2, RefreshCw, BarChart2 } from 'lucide-react';
import type { Recommendation, RecommendationStatus } from '../../types/recommendation';
import { RECOMMENDATION_TYPE_INFO, RECOMMENDATION_STATUS_INFO, PRIORITY_INFO } from '../../types/recommendation';
import type { StakeholderGroup } from '../../types/stakeholder';
import { GROUP_TYPE_INFO } from '../../types/stakeholder';

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
    const statusInfo = RECOMMENDATION_STATUS_INFO[recommendation.status];
    const typeInfo = RECOMMENDATION_TYPE_INFO[recommendation.recommendation_type];
    const priorityInfo = PRIORITY_INFO[recommendation.priority];

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('de-DE', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    };

    const getAffectedGroupsDisplay = () => {
        if (recommendation.affected_groups.includes('all')) {
            return 'Alle';
        }
        return recommendation.affected_groups
            .map(id => {
                const group = stakeholderGroups.find(g => g.id === id);
                if (group) {
                    return group.name || GROUP_TYPE_INFO[group.group_type]?.name || group.group_type;
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
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-100">
                <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2 min-w-0">
                        <span className="text-lg">{statusInfo.icon}</span>
                        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                            {statusInfo.label}
                        </span>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="text-lg" title={typeInfo.description}>{typeInfo.icon}</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPriorityBadgeColor()}`}>
                            {priorityInfo.label}
                        </span>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="p-4">
                <h3 className="text-base font-semibold text-gray-800 mb-2">
                    {recommendation.title}
                </h3>

                {recommendation.description && (
                    <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                        {recommendation.description}
                    </p>
                )}

                {/* Steps (collapsed preview) */}
                {recommendation.steps && recommendation.steps.length > 0 && (
                    <div className="mb-3">
                        <p className="text-xs font-medium text-gray-500 mb-1">Schritte:</p>
                        <ul className="text-sm text-gray-600 list-disc list-inside">
                            {recommendation.steps.slice(0, 2).map((step, idx) => (
                                <li key={idx} className="truncate">{step}</li>
                            ))}
                            {recommendation.steps.length > 2 && (
                                <li className="text-gray-400">+{recommendation.steps.length - 2} weitere...</li>
                            )}
                        </ul>
                    </div>
                )}

                {/* Meta info */}
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
                    <span>Betrifft: {getAffectedGroupsDisplay()}</span>
                    <span>Erstellt: {formatDate(recommendation.created_at)}</span>
                    {recommendation.status === 'approved' && recommendation.approved_at && (
                        <span>Genehmigt: {formatDate(recommendation.approved_at)}</span>
                    )}
                    {recommendation.status === 'started' && recommendation.started_at && (
                        <span>Gestartet: {formatDate(recommendation.started_at)}</span>
                    )}
                    {recommendation.status === 'completed' && recommendation.completed_at && (
                        <span>Abgeschlossen: {formatDate(recommendation.completed_at)}</span>
                    )}
                </div>

                {/* Rejection reason */}
                {recommendation.status === 'rejected' && recommendation.rejection_reason && (
                    <div className="mt-3 p-2 bg-red-50 rounded text-sm text-red-700">
                        <span className="font-medium">Grund:</span> {recommendation.rejection_reason}
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 flex flex-wrap gap-2">
                {recommendation.status === 'pending_approval' && (
                    <>
                        <button
                            onClick={() => onApprove(recommendation.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700 transition-colors"
                        >
                            <Check size={14} />
                            Genehmigen
                        </button>
                        <button
                            onClick={() => onReject(recommendation.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 text-white rounded text-sm font-medium hover:bg-red-700 transition-colors"
                        >
                            <X size={14} />
                            Ablehnen
                        </button>
                        <button
                            onClick={() => onEdit(recommendation)}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-200 text-gray-700 rounded text-sm font-medium hover:bg-gray-300 transition-colors"
                        >
                            <Edit2 size={14} />
                            Bearbeiten
                        </button>
                    </>
                )}

                {recommendation.status === 'approved' && (
                    <button
                        onClick={() => onStart(recommendation.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 transition-colors"
                    >
                        <Play size={14} />
                        Starten
                    </button>
                )}

                {recommendation.status === 'started' && (
                    <button
                        onClick={() => onComplete(recommendation.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700 transition-colors"
                    >
                        <Check size={14} />
                        Als abgeschlossen markieren
                    </button>
                )}

                {recommendation.status === 'completed' && (
                    <button
                        onClick={() => onMeasureImpact(recommendation)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white rounded text-sm font-medium hover:bg-purple-700 transition-colors"
                    >
                        <BarChart2 size={14} />
                        Wirkung messen (Impuls starten)
                    </button>
                )}

                {recommendation.status === 'rejected' && (
                    <button
                        onClick={() => onRegenerate(recommendation)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 transition-colors"
                    >
                        <RefreshCw size={14} />
                        Neue Empfehlung generieren
                    </button>
                )}
            </div>
        </div>
    );
}
