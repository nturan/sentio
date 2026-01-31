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

export const RECOMMENDATION_TYPE_INFO: Record<RecommendationType, { label: string; icon: string; description: string }> = {
    habit: { label: 'Gewohnheit', icon: '🔄', description: 'Kleine taegliche/woechentliche Routine' },
    communication: { label: 'Kommunikation', icon: '📢', description: 'Kommunikationsverbesserung' },
    workshop: { label: 'Workshop', icon: '👥', description: 'Training oder Workshop-Session' },
    process: { label: 'Prozess', icon: '⚙️', description: 'Prozessaenderung' },
    campaign: { label: 'Kampagne', icon: '🚀', description: 'Groessere Initiative' },
} as const;

export const RECOMMENDATION_STATUS_INFO: Record<RecommendationStatus, { label: string; color: string; icon: string }> = {
    pending_approval: { label: 'Ausstehend', color: 'yellow', icon: '🟡' },
    approved: { label: 'Genehmigt', color: 'green', icon: '🟢' },
    rejected: { label: 'Abgelehnt', color: 'red', icon: '🔴' },
    started: { label: 'Gestartet', color: 'blue', icon: '🔵' },
    completed: { label: 'Abgeschlossen', color: 'gray', icon: '✅' },
} as const;

export const PRIORITY_INFO: Record<RecommendationPriority, { label: string; color: string }> = {
    high: { label: 'Hoch', color: 'red' },
    medium: { label: 'Mittel', color: 'yellow' },
    low: { label: 'Niedrig', color: 'green' },
} as const;
