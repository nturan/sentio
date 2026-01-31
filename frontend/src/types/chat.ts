export interface Attachment {
    id: string;
    name: string;
    type: 'image' | 'file';
    url?: string;
}

export interface AnalysisButton {
    label: string;
    action: string;
    style: 'primary' | 'secondary';
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    user: string; // Display name
    content: string;
    timestamp: string;
    projectId?: string;
    attachments?: Attachment[];
    hasAnalysis?: boolean;
    analysisButtons?: AnalysisButton[];
    isImage?: boolean; // Legacy support from mockup
}
