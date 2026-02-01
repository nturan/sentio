import { useEffect, useState } from 'react';
import {
    Lightbulb,
    RefreshCw,
    Sparkles,
    TrendingUp,
    AlertTriangle,
    CheckCircle,
    Network,
    ChevronDown,
    X
} from 'lucide-react';
import {
    listInsights,
    generateInsight,
    dismissInsight,
} from '../../services/api';
import type { Insight, InsightType, InsightPriority } from '../../types/insight';
import { INSIGHT_TYPE_INFO, INSIGHT_PRIORITY_INFO, TRIGGER_TYPE_INFO } from '../../types/insight';

interface InsightsSectionProps {
    projectId: string;
}

// Icon component mapping
const TypeIcon = ({ type, className = '' }: { type: InsightType; className?: string }) => {
    const iconProps = { size: 18, className };
    switch (type) {
        case 'trend':
            return <TrendingUp {...iconProps} />;
        case 'opportunity':
            return <Sparkles {...iconProps} />;
        case 'warning':
            return <AlertTriangle {...iconProps} />;
        case 'success':
            return <CheckCircle {...iconProps} />;
        case 'pattern':
            return <Network {...iconProps} />;
        default:
            return <Lightbulb {...iconProps} />;
    }
};

// Format date to relative time
function formatRelativeTime(dateStr: string): string {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Gerade eben';
    if (diffMins < 60) return `vor ${diffMins} Min.`;
    if (diffHours < 24) return `vor ${diffHours} Std.`;
    if (diffDays < 7) return `vor ${diffDays} Tagen`;
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

interface InsightCardProps {
    insight: Insight;
    isExpanded: boolean;
    onToggle: () => void;
    onDismiss: () => void;
}

function InsightCard({ insight, isExpanded, onToggle, onDismiss }: InsightCardProps) {
    const typeInfo = INSIGHT_TYPE_INFO[insight.insight_type];
    const priorityInfo = INSIGHT_PRIORITY_INFO[insight.priority];
    const triggerInfo = TRIGGER_TYPE_INFO[insight.trigger_type];

    // Get icon color based on type
    const getIconColor = () => {
        switch (insight.insight_type) {
            case 'trend':
                return 'text-blue-500';
            case 'opportunity':
                return 'text-green-500';
            case 'warning':
                return 'text-amber-500';
            case 'success':
                return 'text-emerald-500';
            case 'pattern':
                return 'text-purple-500';
            default:
                return 'text-gray-500';
        }
    };

    return (
        <div
            className={`border rounded-lg transition-all ${priorityInfo.borderColor} ${priorityInfo.bgColor}`}
        >
            <div
                className="flex items-start justify-between p-4 cursor-pointer"
                onClick={onToggle}
            >
                <div className="flex items-start gap-3 flex-1">
                    <div className={`mt-0.5 ${getIconColor()}`}>
                        <TypeIcon type={insight.insight_type} />
                    </div>
                    <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-gray-900 truncate">{insight.title}</h3>
                        <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                            <span>{formatRelativeTime(insight.created_at)}</span>
                            <span>·</span>
                            <span>{typeInfo.label}</span>
                            <span>·</span>
                            <span className={priorityInfo.color}>{priorityInfo.label}</span>
                        </div>
                    </div>
                </div>
                <ChevronDown
                    size={20}
                    className={`text-gray-400 transition-transform flex-shrink-0 ml-2 ${isExpanded ? 'rotate-180' : ''}`}
                />
            </div>

            {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-200/50">
                    <p className="text-sm text-gray-700 mt-4 whitespace-pre-wrap">{insight.content}</p>

                    {insight.action_suggestions.length > 0 && (
                        <div className="mt-4">
                            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                                Vorgeschlagene Aktionen
                            </h4>
                            <ul className="space-y-1.5">
                                {insight.action_suggestions.map((action, i) => (
                                    <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                                        <span className="text-gray-400 mt-0.5">•</span>
                                        <span>{action}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-200/50">
                        <span className="text-xs text-gray-400">
                            {triggerInfo.label}
                        </span>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onDismiss();
                            }}
                            className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
                        >
                            <X size={14} />
                            Ausblenden
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

export function InsightsSection({ projectId }: InsightsSectionProps) {
    const [insights, setInsights] = useState<Insight[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [expandedId, setExpandedId] = useState<string | null>(null);

    const loadInsights = async () => {
        try {
            const data = await listInsights(projectId);
            setInsights(data);
            setError(null);
        } catch (err) {
            console.error('Failed to load insights:', err);
            setError('Insights konnten nicht geladen werden');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadInsights();
    }, [projectId]);

    const handleGenerate = async () => {
        setIsGenerating(true);
        setError(null);
        try {
            const response = await generateInsight(projectId);
            // Add the new insight to the list
            const newInsight: Insight = {
                id: response.insight.id,
                project_id: projectId,
                title: response.insight.title,
                content: response.insight.content,
                insight_type: response.insight.insight_type,
                priority: response.insight.priority,
                trigger_type: 'manual',
                trigger_entity_id: null,
                related_groups: response.insight.related_groups,
                related_recommendations: response.insight.related_recommendations,
                action_suggestions: response.insight.action_suggestions,
                is_dismissed: false,
                created_at: response.insight.created_at,
            };
            setInsights([newInsight, ...insights]);
            setExpandedId(newInsight.id); // Auto-expand new insight
        } catch (err) {
            console.error('Failed to generate insight:', err);
            setError('Insight konnte nicht generiert werden');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleDismiss = async (insightId: string) => {
        try {
            await dismissInsight(insightId);
            setInsights(insights.filter(i => i.id !== insightId));
            if (expandedId === insightId) {
                setExpandedId(null);
            }
        } catch (err) {
            console.error('Failed to dismiss insight:', err);
        }
    };

    return (
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Lightbulb size={20} className="text-purple-500" />
                    <h2 className="text-lg font-semibold text-gray-700">Insights</h2>
                    {insights.length > 0 && (
                        <span className="text-xs bg-purple-100 text-purple-600 px-2 py-0.5 rounded-full">
                            {insights.length}
                        </span>
                    )}
                </div>
                <button
                    onClick={handleGenerate}
                    disabled={isGenerating}
                    className="flex items-center gap-2 px-3 py-1.5 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm transition-colors"
                >
                    {isGenerating ? (
                        <RefreshCw size={14} className="animate-spin" />
                    ) : (
                        <Sparkles size={14} />
                    )}
                    Insight generieren
                </button>
            </div>

            {/* Error state */}
            {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                    {error}
                </div>
            )}

            {/* Loading state */}
            {isLoading ? (
                <div className="flex items-center justify-center py-12">
                    <RefreshCw size={24} className="text-gray-400 animate-spin" />
                </div>
            ) : insights.length === 0 ? (
                /* Empty state */
                <div className="text-center py-12">
                    <Lightbulb size={48} className="mx-auto mb-3 text-gray-300" />
                    <p className="text-gray-500 font-medium">Noch keine Insights</p>
                    <p className="text-sm text-gray-400 mt-1">
                        Klicken Sie auf "Insight generieren", um KI-basierte Erkenntnisse zu erhalten.
                    </p>
                </div>
            ) : (
                /* Insights list */
                <div className="space-y-3">
                    {insights.map(insight => (
                        <InsightCard
                            key={insight.id}
                            insight={insight}
                            isExpanded={expandedId === insight.id}
                            onToggle={() => setExpandedId(expandedId === insight.id ? null : insight.id)}
                            onDismiss={() => handleDismiss(insight.id)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
