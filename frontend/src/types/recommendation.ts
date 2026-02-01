export type RecommendationType = 'habit' | 'communication' | 'workshop' | 'process' | 'campaign';
export type RecommendationPriority = 'high' | 'medium' | 'low';
export type RecommendationStatus = 'pending_approval' | 'approved' | 'rejected' | 'started' | 'completed';

export interface Recommendation {
    id: string;
    project_id: string;
    title: string;
    description: string | null;
    recommendation_type: RecommendationType;
    priority: RecommendationPriority;
    status: RecommendationStatus;
    affected_groups: string[];
    steps: string[];
    rejection_reason: string | null;
    parent_id: string | null;
    created_at: string;
    approved_at: string | null;
    started_at: string | null;
    completed_at: string | null;
}

export interface CreateRecommendationRequest {
    title: string;
    description?: string;
    recommendation_type: RecommendationType;
    priority: RecommendationPriority;
    affected_groups: string[];
    steps: string[];
}

export interface UpdateRecommendationRequest {
    title?: string;
    description?: string;
    recommendation_type?: RecommendationType;
    priority?: RecommendationPriority;
    status?: RecommendationStatus;
    affected_groups?: string[];
    steps?: string[];
    rejection_reason?: string;
}

export interface GeneratedRecommendation {
    title: string;
    description: string;
    recommendation_type: RecommendationType;
    priority: RecommendationPriority;
    affected_groups: string[];
    steps: string[];
}

export interface GenerateRecommendationResponse {
    recommendation: GeneratedRecommendation;
}

// Note: Use t('enums:recommendationTypes.{key}.label') and t('enums:recommendationTypes.{key}.description') for translated text
export const RECOMMENDATION_TYPE_INFO: Record<RecommendationType, { label: string; icon: string; description: string }> = {
    habit: { label: 'Gewohnheit', icon: '🔄', description: 'Kleine taegliche/woechentliche Routine' }, // Fallback - use translation
    communication: { label: 'Kommunikation', icon: '📢', description: 'Kommunikationsverbesserung' }, // Fallback - use translation
    workshop: { label: 'Workshop', icon: '👥', description: 'Training oder Workshop-Session' }, // Fallback - use translation
    process: { label: 'Prozess', icon: '⚙️', description: 'Prozessaenderung' }, // Fallback - use translation
    campaign: { label: 'Kampagne', icon: '🚀', description: 'Groessere Initiative' }, // Fallback - use translation
} as const;

// Note: Use t('enums:recommendationStatus.{key}') for translated label
export const RECOMMENDATION_STATUS_INFO: Record<RecommendationStatus, { label: string; color: string; icon: string }> = {
    pending_approval: { label: 'Ausstehend', color: 'yellow', icon: '🟡' }, // Fallback - use translation
    approved: { label: 'Genehmigt', color: 'green', icon: '🟢' }, // Fallback - use translation
    rejected: { label: 'Abgelehnt', color: 'red', icon: '🔴' }, // Fallback - use translation
    started: { label: 'Gestartet', color: 'blue', icon: '🔵' }, // Fallback - use translation
    completed: { label: 'Abgeschlossen', color: 'gray', icon: '✅' }, // Fallback - use translation
} as const;

// Note: Use t('enums:priority.{key}') for translated label
export const PRIORITY_INFO: Record<RecommendationPriority, { label: string; color: string }> = {
    high: { label: 'Hoch', color: 'red' }, // Fallback - use translation
    medium: { label: 'Mittel', color: 'yellow' }, // Fallback - use translation
    low: { label: 'Niedrig', color: 'green' }, // Fallback - use translation
} as const;
