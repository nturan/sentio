/**
 * Types for the Generator Chat feature - interactive chat panel in generator modals
 */

// Canvas data that can be modified by chat (recommendation-specific)
export interface RecommendationCanvasData {
    title: string;
    description: string;
    recommendation_type: string;
    priority: string;
    affected_groups: string[];
    steps: string[];
}

// Canvas data for survey generator
export interface SurveyCanvasData {
    title: string;
    description: string;
    questions: Array<{
        id: string;
        type: 'scale' | 'freetext';
        question: string;
        includeJustification?: boolean;
    }>;
    estimated_duration?: string;
}

// Generic canvas data type for reusability across generators
export type CanvasData = RecommendationCanvasData | SurveyCanvasData | Record<string, unknown>;

// Chat message in generator context
export interface GeneratorChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

// Request to generator chat endpoint
export interface GeneratorChatRequest {
    message: string;
    projectId: string;
    generatorType: 'recommendation' | 'insight' | 'survey';
    canvasData: CanvasData;
    history: Array<{ role: string; content: string }>;
}

// Streaming chunk types from backend
export interface GeneratorChatTextChunk {
    type: 'text';
    content: string;
}

export interface GeneratorChatCanvasUpdateChunk {
    type: 'canvas_update';
    updates: Partial<CanvasData>;
}

export interface GeneratorChatDoneChunk {
    type: 'done';
}

export type GeneratorChatChunk =
    | GeneratorChatTextChunk
    | GeneratorChatCanvasUpdateChunk
    | GeneratorChatDoneChunk;

// Hook options
export interface UseGeneratorChatOptions<T extends CanvasData> {
    projectId: string;
    generatorType: 'recommendation' | 'insight' | 'survey';
    canvasData: T;
    onCanvasUpdate: (updates: Partial<T>) => void;
}
