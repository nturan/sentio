import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import {
    listStakeholderGroups,
    createStakeholderGroup as apiCreateGroup,
    getStakeholderGroup as apiGetGroup,
    updateStakeholderGroup as apiUpdateGroup,
    deleteStakeholderGroup as apiDeleteGroup,
    addStakeholderAssessment as apiAddAssessment,
    batchAddAssessments as apiBatchAdd
} from '../services/api';
import type {
    StakeholderGroup,
    StakeholderGroupWithAssessments,
    CreateStakeholderGroupRequest,
    UpdateStakeholderGroupRequest,
    CreateStakeholderAssessmentRequest
} from '../types/stakeholder';

interface StakeholderContextType {
    // State
    groups: StakeholderGroup[];
    selectedGroup: StakeholderGroupWithAssessments | null;
    isLoading: boolean;
    error: string | null;

    // Actions
    loadGroups: (projectId: string) => Promise<void>;
    createGroup: (projectId: string, data: CreateStakeholderGroupRequest) => Promise<StakeholderGroup>;
    selectGroup: (groupId: string) => Promise<void>;
    updateGroup: (groupId: string, data: UpdateStakeholderGroupRequest) => Promise<StakeholderGroup>;
    deleteGroup: (groupId: string) => Promise<void>;
    addAssessment: (groupId: string, data: CreateStakeholderAssessmentRequest) => Promise<void>;
    batchAssessments: (groupId: string, assessments: CreateStakeholderAssessmentRequest[]) => Promise<void>;
    clearSelectedGroup: () => void;
}

const StakeholderContext = createContext<StakeholderContextType | undefined>(undefined);

export function StakeholderProvider({ children }: { children: ReactNode }) {
    const [groups, setGroups] = useState<StakeholderGroup[]>([]);
    const [selectedGroup, setSelectedGroup] = useState<StakeholderGroupWithAssessments | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadGroups = useCallback(async (projectId: string) => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await listStakeholderGroups(projectId);
            setGroups(data);
        } catch (err) {
            console.error('Failed to load stakeholder groups:', err);
            setError(err instanceof Error ? err.message : 'Failed to load groups');
        } finally {
            setIsLoading(false);
        }
    }, []);

    const createGroup = useCallback(async (projectId: string, data: CreateStakeholderGroupRequest): Promise<StakeholderGroup> => {
        const group = await apiCreateGroup(projectId, data);
        setGroups(prev => [...prev, group]);
        return group;
    }, []);

    const selectGroup = useCallback(async (groupId: string) => {
        setIsLoading(true);
        try {
            const group = await apiGetGroup(groupId);
            setSelectedGroup(group);
        } catch (err) {
            console.error('Failed to load stakeholder group:', err);
            setError(err instanceof Error ? err.message : 'Failed to load group');
        } finally {
            setIsLoading(false);
        }
    }, []);

    const updateGroup = useCallback(async (groupId: string, data: UpdateStakeholderGroupRequest): Promise<StakeholderGroup> => {
        const updated = await apiUpdateGroup(groupId, data);
        setGroups(prev => prev.map(g => g.id === groupId ? updated : g));
        if (selectedGroup?.id === groupId) {
            setSelectedGroup(prev => prev ? { ...prev, ...updated } : null);
        }
        return updated;
    }, [selectedGroup?.id]);

    const deleteGroup = useCallback(async (groupId: string) => {
        await apiDeleteGroup(groupId);
        setGroups(prev => prev.filter(g => g.id !== groupId));
        if (selectedGroup?.id === groupId) {
            setSelectedGroup(null);
        }
    }, [selectedGroup?.id]);

    const addAssessment = useCallback(async (groupId: string, data: CreateStakeholderAssessmentRequest) => {
        await apiAddAssessment(groupId, data);
        // Refresh the selected group to get updated assessments
        if (selectedGroup?.id === groupId) {
            const updated = await apiGetGroup(groupId);
            setSelectedGroup(updated);
        }
    }, [selectedGroup?.id]);

    const batchAssessments = useCallback(async (groupId: string, assessments: CreateStakeholderAssessmentRequest[]) => {
        await apiBatchAdd(groupId, assessments);
        // Refresh the selected group to get updated assessments
        if (selectedGroup?.id === groupId) {
            const updated = await apiGetGroup(groupId);
            setSelectedGroup(updated);
        }
    }, [selectedGroup?.id]);

    const clearSelectedGroup = useCallback(() => {
        setSelectedGroup(null);
    }, []);

    return (
        <StakeholderContext.Provider
            value={{
                groups,
                selectedGroup,
                isLoading,
                error,
                loadGroups,
                createGroup,
                selectGroup,
                updateGroup,
                deleteGroup,
                addAssessment,
                batchAssessments,
                clearSelectedGroup
            }}
        >
            {children}
        </StakeholderContext.Provider>
    );
}

export function useStakeholder() {
    const context = useContext(StakeholderContext);
    if (context === undefined) {
        throw new Error('useStakeholder must be used within a StakeholderProvider');
    }
    return context;
}
