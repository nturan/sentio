// Stakeholder group types
export type StakeholderGroupType = 'fuehrungskraefte' | 'multiplikatoren' | 'mitarbeitende';
export type PowerLevel = 'high' | 'low';
export type InterestLevel = 'high' | 'low';

export interface StakeholderGroup {
    id: string;
    project_id: string;
    group_type: StakeholderGroupType;
    name: string | null;
    power_level: PowerLevel;
    interest_level: InterestLevel;
    notes: string | null;
    created_at: string;
    mendelow_quadrant: string;
    mendelow_strategy: string;
}

export interface StakeholderGroupWithAssessments extends StakeholderGroup {
    assessments: StakeholderAssessment[];
    available_indicators: IndicatorDefinition[];
}

export interface StakeholderAssessment {
    id: string;
    stakeholder_group_id: string;
    indicator_key: string;
    rating: number;
    notes: string | null;
    assessed_at: string;
}

export interface IndicatorDefinition {
    key: string;
    name: string;
    description: string;
}

export interface StakeholderGroupTypeInfo {
    key: StakeholderGroupType;
    name: string;
    description: string;
    indicator_count: number;
}

// Request types
export interface CreateStakeholderGroupRequest {
    group_type: StakeholderGroupType;
    name?: string;
    power_level: PowerLevel;
    interest_level: InterestLevel;
    notes?: string;
}

export interface UpdateStakeholderGroupRequest {
    name?: string;
    power_level?: PowerLevel;
    interest_level?: InterestLevel;
    notes?: string;
}

export interface CreateStakeholderAssessmentRequest {
    indicator_key: string;
    rating: number;
    notes?: string;
}

// Mendelow Matrix quadrant display info
// Note: Use t('enums:mendelowQuadrants.{key}.description') for translated description
export const MENDELOW_QUADRANTS = {
    'Key Players': {
        color: 'bg-red-100 border-red-300',
        textColor: 'text-red-700',
    },
    'Keep Satisfied': {
        color: 'bg-yellow-100 border-yellow-300',
        textColor: 'text-yellow-700',
    },
    'Keep Informed': {
        color: 'bg-blue-100 border-blue-300',
        textColor: 'text-blue-700',
    },
    'Monitor': {
        color: 'bg-gray-100 border-gray-300',
        textColor: 'text-gray-700',
    }
} as const;

// Stakeholder group type display info
// Note: Use t('enums:stakeholderTypes.{key}.name') and t('enums:stakeholderTypes.{key}.subtitle') for translated text
export const GROUP_TYPE_INFO = {
    fuehrungskraefte: {
        key: 'fuehrungskraefte' as const,
        name: 'Fuehrungskraefte', // Fallback - use translation in components
        subtitle: 'Middle Management', // Fallback - use translation in components
        icon: '👔',
        color: 'bg-purple-100 border-purple-300'
    },
    multiplikatoren: {
        key: 'multiplikatoren' as const,
        name: 'Multiplikatoren', // Fallback - use translation in components
        subtitle: 'Change Manager/Stab', // Fallback - use translation in components
        icon: '🎯',
        color: 'bg-green-100 border-green-300'
    },
    mitarbeitende: {
        key: 'mitarbeitende' as const,
        name: 'Mitarbeitende', // Fallback - use translation in components
        subtitle: 'Die Betroffenen', // Fallback - use translation in components
        icon: '👥',
        color: 'bg-blue-100 border-blue-300'
    }
} as const;
