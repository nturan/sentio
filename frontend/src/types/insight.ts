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

export const INSIGHT_TYPE_INFO: Record<InsightType, { label: string; icon: string; color: string; description: string }> = {
    trend: {
        label: 'Trend',
        icon: 'TrendingUp',
        color: 'blue',
        description: 'Entwicklung ueber Zeit'
    },
    opportunity: {
        label: 'Chance',
        icon: 'Sparkles',
        color: 'green',
        description: 'Verbesserungspotential'
    },
    warning: {
        label: 'Warnung',
        icon: 'AlertTriangle',
        color: 'amber',
        description: 'Erfordert Aufmerksamkeit'
    },
    success: {
        label: 'Erfolg',
        icon: 'CheckCircle',
        color: 'emerald',
        description: 'Positive Entwicklung'
    },
    pattern: {
        label: 'Muster',
        icon: 'Network',
        color: 'purple',
        description: 'Wiederkehrendes Thema'
    },
} as const;

export const INSIGHT_PRIORITY_INFO: Record<InsightPriority, { label: string; color: string; bgColor: string; borderColor: string }> = {
    high: {
        label: 'Hohe Prioritaet',
        color: 'text-red-700',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200'
    },
    medium: {
        label: 'Mittlere Prioritaet',
        color: 'text-amber-700',
        bgColor: 'bg-amber-50',
        borderColor: 'border-amber-200'
    },
    low: {
        label: 'Niedrige Prioritaet',
        color: 'text-gray-700',
        bgColor: 'bg-gray-50',
        borderColor: 'border-gray-200'
    },
} as const;

export const TRIGGER_TYPE_INFO: Record<TriggerType, { label: string }> = {
    manual: { label: 'Manuell generiert' },
    impulse_completed: { label: 'Nach Impulse' },
    recommendation_completed: { label: 'Nach Handlung' },
} as const;
