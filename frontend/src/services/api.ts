import type {
    ChatSession,
    SessionWithMessages,
    CreateSessionRequest,
    CreateMessageRequest,
    SessionMessage
} from '../types/session';
import type {
    StakeholderGroup,
    StakeholderGroupWithAssessments,
    StakeholderAssessment,
    CreateStakeholderGroupRequest,
    UpdateStakeholderGroupRequest,
    CreateStakeholderAssessmentRequest,
    StakeholderGroupTypeInfo,
    IndicatorDefinition
} from '../types/stakeholder';

// Project types
export interface ProjectData {
    id: string;
    name: string;
    icon: string;
    goal?: string;
    created_at: string;
    updated_at: string;
}

export interface CreateProjectRequest {
    name: string;
    icon?: string;
    goal?: string;
}

// Dashboard types
export interface DashboardIndicatorScore {
    key: string;
    name: string;
    description: string;
    average_rating: number | null;
    latest_rating: number | null;
    rating_count: number;
}

export interface DashboardData {
    indicators: DashboardIndicatorScore[];
    trend_data: Array<Record<string, string | number>>;
}

export const API_CONFIG = {
    chat: '/api/chat',
    dashboard: '/api/dashboard',
    ingest: '/api/ingest',
    retrieval: '/api/retrieval',
    brain: '/api/brain',
};

interface ApiOptions {
    body?: any;
    headers?: Record<string, string>;
}

export async function post<T>(url: string, options: ApiOptions = {}): Promise<T> {
    if (!url) {
        throw new Error('API URL not configured');
    }

    // If body is FormData (file upload), let browser set Content-Type
    const isFormData = options.body instanceof FormData;

    const headers = {
        ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
        ...options.headers
    };

    const response = await fetch(url, {
        method: 'POST',
        headers,
        body: isFormData ? options.body : JSON.stringify(options.body)
    });

    if (!response.ok) {
        throw new Error(`API call failed: ${response.statusText}`);
    }

    const text = await response.text();
    return text ? JSON.parse(text) : {} as T;
}

export async function postStream(
    url: string,
    options: ApiOptions = {},
    onChunk: (text: string) => void
): Promise<void> {
    if (!url) throw new Error('API URL not configured');

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        body: JSON.stringify(options.body)
    });

    if (!response.ok) throw new Error(`Stream failed: ${response.statusText}`);
    if (!response.body) throw new Error('No response body');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Keep the last line in buffer if it's incomplete
        buffer = lines.pop() || '';

        for (const line of lines) {
            if (!line.trim()) continue;
            try {
                const data = JSON.parse(line);
                if (data.type === 'item' && data.content) {
                    onChunk(data.content);
                }
            } catch (e) {
                console.warn('Failed to parse stream line:', line);
            }
        }
    }
}

// Session API functions
export async function listSessions(projectId: string): Promise<ChatSession[]> {
    const response = await fetch(`/api/projects/${projectId}/sessions`);
    if (!response.ok) {
        throw new Error(`Failed to list sessions: ${response.statusText}`);
    }
    return response.json();
}

export async function createSession(projectId: string, data: CreateSessionRequest = {}): Promise<ChatSession> {
    const response = await fetch(`/api/projects/${projectId}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        throw new Error(`Failed to create session: ${response.statusText}`);
    }
    return response.json();
}

export async function getSession(sessionId: string): Promise<SessionWithMessages> {
    const response = await fetch(`/api/sessions/${sessionId}`);
    if (!response.ok) {
        throw new Error(`Failed to get session: ${response.statusText}`);
    }
    return response.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
    const response = await fetch(`/api/sessions/${sessionId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        throw new Error(`Failed to delete session: ${response.statusText}`);
    }
}

export async function updateSessionTitle(sessionId: string, title: string): Promise<ChatSession> {
    const response = await fetch(`/api/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title })
    });
    if (!response.ok) {
        throw new Error(`Failed to update session: ${response.statusText}`);
    }
    return response.json();
}

// Project API functions
export async function listProjects(): Promise<ProjectData[]> {
    const response = await fetch('/api/projects');
    if (!response.ok) {
        throw new Error(`Failed to list projects: ${response.statusText}`);
    }
    return response.json();
}

export async function createProject(data: CreateProjectRequest): Promise<ProjectData> {
    const response = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        throw new Error(`Failed to create project: ${response.statusText}`);
    }
    return response.json();
}

export async function deleteProject(projectId: string): Promise<void> {
    const response = await fetch(`/api/projects/${projectId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        throw new Error(`Failed to delete project: ${response.statusText}`);
    }
}

// Document types and API functions
export interface DocumentData {
    id: string;
    project_id: string;
    filename: string;
    file_size: number | null;
    content_type: string | null;
    created_at: string;
}

export async function listDocuments(projectId: string): Promise<DocumentData[]> {
    const response = await fetch(`/api/projects/${projectId}/documents`);
    if (!response.ok) {
        throw new Error(`Failed to list documents: ${response.statusText}`);
    }
    return response.json();
}

export async function uploadDocument(projectId: string, file: File): Promise<DocumentData> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`/api/projects/${projectId}/documents`, {
        method: 'POST',
        body: formData
    });
    if (!response.ok) {
        throw new Error(`Failed to upload document: ${response.statusText}`);
    }
    return response.json();
}

export async function deleteDocument(documentId: string): Promise<void> {
    const response = await fetch(`/api/documents/${documentId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        throw new Error(`Failed to delete document: ${response.statusText}`);
    }
}

export async function saveMessage(sessionId: string, message: CreateMessageRequest): Promise<SessionMessage> {
    const response = await fetch(`/api/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(message)
    });
    if (!response.ok) {
        throw new Error(`Failed to save message: ${response.statusText}`);
    }
    return response.json();
}

// --- Dashboard API functions ---

export async function getDashboardData(projectId: string): Promise<DashboardData> {
    const response = await fetch(`/api/projects/${projectId}/dashboard-data`);
    if (!response.ok) {
        throw new Error(`Failed to get dashboard data: ${response.statusText}`);
    }
    return response.json();
}

export async function getPredefinedIndicators(): Promise<IndicatorDefinition[]> {
    const response = await fetch('/api/indicators/predefined');
    if (!response.ok) {
        throw new Error(`Failed to get predefined indicators: ${response.statusText}`);
    }
    return response.json();
}

export async function getCoreIndicators(): Promise<IndicatorDefinition[]> {
    const response = await fetch('/api/indicators/core');
    if (!response.ok) {
        throw new Error(`Failed to get core indicators: ${response.statusText}`);
    }
    return response.json();
}

// --- Stakeholder API functions ---

export async function getStakeholderGroupTypes(): Promise<StakeholderGroupTypeInfo[]> {
    const response = await fetch('/api/stakeholder-group-types');
    if (!response.ok) {
        throw new Error(`Failed to get stakeholder group types: ${response.statusText}`);
    }
    return response.json();
}

export async function listStakeholderGroups(projectId: string): Promise<StakeholderGroup[]> {
    const response = await fetch(`/api/projects/${projectId}/stakeholder-groups`);
    if (!response.ok) {
        throw new Error(`Failed to list stakeholder groups: ${response.statusText}`);
    }
    return response.json();
}

export async function createStakeholderGroup(projectId: string, data: CreateStakeholderGroupRequest): Promise<StakeholderGroup> {
    const response = await fetch(`/api/projects/${projectId}/stakeholder-groups`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create stakeholder group: ${response.statusText}`);
    }
    return response.json();
}

export async function getStakeholderGroup(groupId: string): Promise<StakeholderGroupWithAssessments> {
    const response = await fetch(`/api/stakeholder-groups/${groupId}`);
    if (!response.ok) {
        throw new Error(`Failed to get stakeholder group: ${response.statusText}`);
    }
    return response.json();
}

export async function updateStakeholderGroup(groupId: string, data: UpdateStakeholderGroupRequest): Promise<StakeholderGroup> {
    const response = await fetch(`/api/stakeholder-groups/${groupId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        throw new Error(`Failed to update stakeholder group: ${response.statusText}`);
    }
    return response.json();
}

export async function deleteStakeholderGroup(groupId: string): Promise<void> {
    const response = await fetch(`/api/stakeholder-groups/${groupId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        throw new Error(`Failed to delete stakeholder group: ${response.statusText}`);
    }
}

export async function listStakeholderAssessments(groupId: string): Promise<StakeholderAssessment[]> {
    const response = await fetch(`/api/stakeholder-groups/${groupId}/assessments`);
    if (!response.ok) {
        throw new Error(`Failed to list stakeholder assessments: ${response.statusText}`);
    }
    return response.json();
}

export async function addStakeholderAssessment(groupId: string, data: CreateStakeholderAssessmentRequest): Promise<StakeholderAssessment> {
    const response = await fetch(`/api/stakeholder-groups/${groupId}/assessments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to add stakeholder assessment: ${response.statusText}`);
    }
    return response.json();
}

export async function batchAddAssessments(groupId: string, assessments: CreateStakeholderAssessmentRequest[]): Promise<{
    success_count: number;
    error_count: number;
    results: StakeholderAssessment[];
    errors: Array<{ indicator_key: string; error: string }>;
}> {
    const response = await fetch(`/api/stakeholder-groups/${groupId}/assessments/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(assessments)
    });
    if (!response.ok) {
        throw new Error(`Failed to batch add assessments: ${response.statusText}`);
    }
    return response.json();
}

export async function deleteStakeholderAssessment(assessmentId: string): Promise<void> {
    const response = await fetch(`/api/stakeholder-assessments/${assessmentId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        throw new Error(`Failed to delete stakeholder assessment: ${response.statusText}`);
    }
}

// --- Impulse API functions ---

import type { ImpulseHistory, Survey, GenerateSurveyResponse, SaveSurveyResponse } from '../types/impulse';

export async function getImpulseHistory(groupId: string, limit: number = 50): Promise<ImpulseHistory> {
    const response = await fetch(`/api/stakeholder-groups/${groupId}/impulse-history?limit=${limit}`);
    if (!response.ok) {
        throw new Error(`Failed to get impulse history: ${response.statusText}`);
    }
    return response.json();
}

export async function batchAddAssessmentsWithDate(
    groupId: string,
    assessments: CreateStakeholderAssessmentRequest[],
    assessedAt: string
): Promise<{
    success_count: number;
    error_count: number;
    results: StakeholderAssessment[];
    errors: Array<{ indicator_key: string; error: string }>;
}> {
    // Add assessed_at to each assessment
    const assessmentsWithDate = assessments.map(a => ({
        ...a,
        assessed_at: assessedAt
    }));

    const response = await fetch(`/api/stakeholder-groups/${groupId}/assessments/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(assessmentsWithDate)
    });
    if (!response.ok) {
        throw new Error(`Failed to batch add assessments: ${response.statusText}`);
    }
    return response.json();
}

// --- Survey API functions ---

export async function generateSurvey(groupId: string): Promise<GenerateSurveyResponse> {
    const response = await fetch(`/api/stakeholder-groups/${groupId}/generate-survey`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) {
        throw new Error(`Failed to generate survey: ${response.statusText}`);
    }
    return response.json();
}

export async function saveSurvey(groupId: string, survey: Survey): Promise<SaveSurveyResponse> {
    const response = await fetch(`/api/stakeholder-groups/${groupId}/save-survey`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ survey })
    });
    if (!response.ok) {
        throw new Error(`Failed to save survey: ${response.statusText}`);
    }
    return response.json();
}

// --- Recommendations API functions ---

import type {
    Recommendation,
    CreateRecommendationRequest,
    UpdateRecommendationRequest,
    GenerateRecommendationResponse
} from '../types/recommendation';

export async function listRecommendations(projectId: string, status?: string): Promise<Recommendation[]> {
    const url = status
        ? `/api/projects/${projectId}/recommendations?status=${status}`
        : `/api/projects/${projectId}/recommendations`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Failed to list recommendations: ${response.statusText}`);
    }
    return response.json();
}

export async function getRecommendation(recId: string): Promise<Recommendation> {
    const response = await fetch(`/api/recommendations/${recId}`);
    if (!response.ok) {
        throw new Error(`Failed to get recommendation: ${response.statusText}`);
    }
    return response.json();
}

export async function createRecommendation(projectId: string, data: CreateRecommendationRequest): Promise<Recommendation> {
    const response = await fetch(`/api/projects/${projectId}/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        throw new Error(`Failed to create recommendation: ${response.statusText}`);
    }
    return response.json();
}

export async function updateRecommendation(recId: string, data: UpdateRecommendationRequest): Promise<Recommendation> {
    const response = await fetch(`/api/recommendations/${recId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        throw new Error(`Failed to update recommendation: ${response.statusText}`);
    }
    return response.json();
}

export async function deleteRecommendation(recId: string): Promise<void> {
    const response = await fetch(`/api/recommendations/${recId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        throw new Error(`Failed to delete recommendation: ${response.statusText}`);
    }
}

export async function generateRecommendation(projectId: string, focus?: string): Promise<GenerateRecommendationResponse> {
    const response = await fetch(`/api/projects/${projectId}/recommendations/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ focus })
    });
    if (!response.ok) {
        throw new Error(`Failed to generate recommendation: ${response.statusText}`);
    }
    return response.json();
}

export async function regenerateRecommendation(recId: string, additionalContext?: string): Promise<GenerateRecommendationResponse> {
    const response = await fetch(`/api/recommendations/${recId}/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ additional_context: additionalContext })
    });
    if (!response.ok) {
        throw new Error(`Failed to regenerate recommendation: ${response.statusText}`);
    }
    return response.json();
}
