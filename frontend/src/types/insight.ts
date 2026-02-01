export type InsightType = 'trend' | 'opportunity' | 'warning' | 'success' | 'pattern';
export type InsightPriority = 'high' | 'medium' | 'low';
export type TriggerType = 'manual' | 'impulse_completed' | 'recommendation_completed';

export interface Insight {
    id: string;
    project_id: string;
    title: string;
    content: string;
    insight_type: InsightType;
    priority: InsightPriority;
    trigger_type: TriggerType;
    trigger_entity_id: string | null;
    related_groups: string[];
    related_recommendations: string[];
    action_suggestions: string[];
    is_dismissed: boolean;
    created_at: string;
}

export interface GenerateInsightRequest {
    focus?: string;
}

export interface GeneratedInsight {
    id: string;
    title: string;
    content: string;
    insight_type: InsightType;
    priority: InsightPriority;
    related_groups: string[];
    related_recommendations: string[];
    action_suggestions: string[];
    created_at: string;
}

export interface GenerateInsightResponse {
    insight: GeneratedInsight;
}

// Note: Use t('enums:insightTypes.{key}.label') and t('enums:insightTypes.{key}.description') for translated text
export const INSIGHT_TYPE_INFO: Record<InsightType, { label: string; icon: string; color: string; description: string }> = {
    trend: {
        label: 'Trend', // Fallback - use translation
        icon: 'TrendingUp',
        color: 'blue',
        description: 'Entwicklung ueber Zeit' // Fallback - use translation
    },
    opportunity: {
        label: 'Chance', // Fallback - use translation
        icon: 'Sparkles',
        color: 'green',
        description: 'Verbesserungspotential' // Fallback - use translation
    },
    warning: {
        label: 'Warnung', // Fallback - use translation
        icon: 'AlertTriangle',
        color: 'amber',
        description: 'Erfordert Aufmerksamkeit' // Fallback - use translation
    },
    success: {
        label: 'Erfolg', // Fallback - use translation
        icon: 'CheckCircle',
        color: 'emerald',
        description: 'Positive Entwicklung' // Fallback - use translation
    },
    pattern: {
        label: 'Muster', // Fallback - use translation
        icon: 'Network',
        color: 'purple',
        description: 'Wiederkehrendes Thema' // Fallback - use translation
    },
} as const;

// Note: Use t('enums:insightPriority.{key}') for translated label
export const INSIGHT_PRIORITY_INFO: Record<InsightPriority, { label: string; color: string; bgColor: string; borderColor: string }> = {
    high: {
        label: 'Hohe Prioritaet', // Fallback - use translation
        color: 'text-red-700',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200'
    },
    medium: {
        label: 'Mittlere Prioritaet', // Fallback - use translation
        color: 'text-amber-700',
        bgColor: 'bg-amber-50',
        borderColor: 'border-amber-200'
    },
    low: {
        label: 'Niedrige Prioritaet', // Fallback - use translation
        color: 'text-gray-700',
        bgColor: 'bg-gray-50',
        borderColor: 'border-gray-200'
    },
} as const;

// Note: Use t('enums:triggerTypes.{key}') for translated label
export const TRIGGER_TYPE_INFO: Record<TriggerType, { label: string }> = {
    manual: { label: 'Manuell generiert' }, // Fallback - use translation
    impulse_completed: { label: 'Nach Impulse' }, // Fallback - use translation
    recommendation_completed: { label: 'Nach Handlung' }, // Fallback - use translation
} as const;
