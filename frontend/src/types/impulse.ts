// Impulse types

export interface ImpulseEntry {
    date: string;
    average_rating: number;
    ratings: Record<string, number>;
    notes: Record<string, string>;
    source: 'manual' | 'survey';
}

export interface ImpulseHistory {
    group_id: string;
    group_name: string | null;
    group_type: string;
    impulses: ImpulseEntry[];
}

// Survey types
export type SurveyQuestionType = 'scale' | 'freetext';

export interface SurveyQuestion {
    id: string;
    type: SurveyQuestionType;
    question: string;
    includeJustification?: boolean;
}

export interface Survey {
    id?: string;
    title: string;
    description: string;
    questions: SurveyQuestion[];
    stakeholder_group_id: string;
    estimated_duration?: string;
}

export interface GenerateSurveyRequest {
    stakeholder_group_id: string;
}

export interface GenerateSurveyResponse {
    survey: Survey;
}

export interface SaveSurveyRequest {
    survey: Survey;
}

export interface SaveSurveyResponse {
    file_path: string;
    survey_id: string;
}
