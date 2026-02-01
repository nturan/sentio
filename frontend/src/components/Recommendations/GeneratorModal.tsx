import { useState, useEffect, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';
import { X, Loader2, Plus, Trash2 } from 'lucide-react';
import type { GeneratedRecommendation, RecommendationType, RecommendationPriority, CreateRecommendationRequest } from '../../types/recommendation';
import { RECOMMENDATION_TYPE_INFO, PRIORITY_INFO } from '../../types/recommendation';
import type { StakeholderGroup } from '../../types/stakeholder';
import { GROUP_TYPE_INFO } from '../../types/stakeholder';
import { generateRecommendation, regenerateRecommendation, createRecommendation } from '../../services/api';
import { useGeneratorChat } from '../../hooks/useGeneratorChat';
import { GeneratorChatPanel } from '../GeneratorChat';
import type { RecommendationCanvasData } from '../../types/generatorChat';

interface GeneratorModalProps {
    projectId: string;
    stakeholderGroups: StakeholderGroup[];
    projectGoal: string | null;
    // For regeneration from rejected recommendation
    rejectedRecommendationId?: string;
    rejectionReason?: string;
    onClose: () => void;
    onSaved: () => void;
}

export function GeneratorModal({
    projectId,
    stakeholderGroups,
    projectGoal,
    rejectedRecommendationId,
    rejectionReason,
    onClose,
    onSaved
}: GeneratorModalProps) {
    const { t } = useTranslation('recommendations');
    const { t: tCommon } = useTranslation('common');
    const { t: tEnums } = useTranslation('enums');
    const [focus, setFocus] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Editable generated recommendation
    const [generated, setGenerated] = useState<GeneratedRecommendation | null>(null);
    const [editedTitle, setEditedTitle] = useState('');
    const [editedDescription, setEditedDescription] = useState('');
    const [editedType, setEditedType] = useState<RecommendationType>('communication');
    const [editedPriority, setEditedPriority] = useState<RecommendationPriority>('medium');
    const [editedAffectedGroups, setEditedAffectedGroups] = useState<string[]>([]);
    const [editedSteps, setEditedSteps] = useState<string[]>([]);

    // Canvas data for chat - memoized to prevent unnecessary re-renders
    const canvasData = useMemo<RecommendationCanvasData>(() => ({
        title: editedTitle,
        description: editedDescription,
        recommendation_type: editedType,
        priority: editedPriority,
        affected_groups: editedAffectedGroups,
        steps: editedSteps
    }), [editedTitle, editedDescription, editedType, editedPriority, editedAffectedGroups, editedSteps]);

    // Handle canvas updates from chat
    const handleCanvasUpdate = useCallback((updates: Partial<RecommendationCanvasData>) => {
        if (updates.title !== undefined) setEditedTitle(updates.title);
        if (updates.description !== undefined) setEditedDescription(updates.description);
        if (updates.recommendation_type !== undefined) setEditedType(updates.recommendation_type as RecommendationType);
        if (updates.priority !== undefined) setEditedPriority(updates.priority as RecommendationPriority);
        if (updates.affected_groups !== undefined) setEditedAffectedGroups(updates.affected_groups);
        if (updates.steps !== undefined) setEditedSteps(updates.steps);
    }, []);

    // Generator chat hook
    const { messages, sendMessage, isTyping } = useGeneratorChat<RecommendationCanvasData>(
        canvasData,
        {
            projectId,
            generatorType: 'recommendation',
            onCanvasUpdate: handleCanvasUpdate
        }
    );

    // Update edited fields when generated recommendation changes
    useEffect(() => {
        if (generated) {
            setEditedTitle(generated.title);
            setEditedDescription(generated.description);
            setEditedType(generated.recommendation_type);
            setEditedPriority(generated.priority);
            setEditedAffectedGroups(generated.affected_groups);
            setEditedSteps(generated.steps);
        }
    }, [generated]);

    const handleGenerate = async () => {
        setIsGenerating(true);
        setError(null);
        try {
            let response;
            if (rejectedRecommendationId) {
                response = await regenerateRecommendation(rejectedRecommendationId, focus || undefined);
            } else {
                response = await generateRecommendation(projectId, focus || undefined);
            }
            setGenerated(response.recommendation);
        } catch (err) {
            console.error('Failed to generate recommendation:', err);
            setError(err instanceof Error ? err.message : t('generatorModal.generationError'));
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSave = async () => {
        if (!editedTitle.trim()) {
            setError(t('generatorModal.titleRequired'));
            return;
        }

        setIsSaving(true);
        setError(null);
        try {
            const data: CreateRecommendationRequest = {
                title: editedTitle,
                description: editedDescription || undefined,
                recommendation_type: editedType,
                priority: editedPriority,
                affected_groups: editedAffectedGroups.length > 0 ? editedAffectedGroups : ['all'],
                steps: editedSteps.filter(s => s.trim())
            };
            await createRecommendation(projectId, data);
            onSaved();
            onClose();
        } catch (err) {
            console.error('Failed to save recommendation:', err);
            setError(err instanceof Error ? err.message : tCommon('errors.saveFailed'));
        } finally {
            setIsSaving(false);
        }
    };

    const handleToggleGroup = (groupId: string) => {
        if (editedAffectedGroups.includes('all')) {
            // Switch from "all" to specific group
            setEditedAffectedGroups([groupId]);
        } else if (editedAffectedGroups.includes(groupId)) {
            setEditedAffectedGroups(editedAffectedGroups.filter(g => g !== groupId));
        } else {
            setEditedAffectedGroups([...editedAffectedGroups, groupId]);
        }
    };

    const handleToggleAll = () => {
        if (editedAffectedGroups.includes('all')) {
            setEditedAffectedGroups([]);
        } else {
            setEditedAffectedGroups(['all']);
        }
    };

    const handleAddStep = () => {
        setEditedSteps([...editedSteps, '']);
    };

    const handleRemoveStep = (index: number) => {
        setEditedSteps(editedSteps.filter((_, i) => i !== index));
    };

    const handleUpdateStep = (index: number, value: string) => {
        const newSteps = [...editedSteps];
        newSteps[index] = value;
        setEditedSteps(newSteps);
    };

    // Determine if chat panel should be shown (after generation)
    const showChat = generated !== null;

    const modalContent = (
        <div
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px',
                zIndex: 9999,
            }}
            onClick={(e) => {
                if (e.target === e.currentTarget && !isGenerating && !isSaving && !isTyping) onClose();
            }}
        >
            <div
                style={{
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                    width: '100%',
                    maxWidth: showChat ? '80rem' : '48rem',
                    maxHeight: '90vh',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'max-width 0.3s ease-in-out',
                }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div style={{ flexShrink: 0 }} className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-800">
                        {rejectedRecommendationId ? t('generatorModal.titleRegenerate') : t('generatorModal.title')}
                    </h2>
                    <button
                        onClick={onClose}
                        disabled={isGenerating || isSaving || isTyping}
                        className="p-2 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
                    >
                        <X size={20} className="text-gray-500" />
                    </button>
                </div>

                {/* Main Content - Split Layout when chat is visible */}
                <div style={{ flex: '1 1 0%', minHeight: 0, display: 'flex', flexDirection: showChat ? 'row' : 'column', overflow: 'hidden' }}>
                    {/* Canvas Panel (Left side when chat visible) */}
                    <div style={{
                        flex: showChat ? '0 0 60%' : '1 1 auto',
                        minHeight: 0,
                        overflowY: 'auto',
                        padding: '24px'
                    }} className="space-y-6">
                        {/* Context Display */}
                        <div className="bg-gray-50 rounded-lg p-4">
                            <h3 className="text-sm font-medium text-gray-700 mb-2">{t('generatorModal.contextTitle')}</h3>
                            <div className="text-sm text-gray-600 space-y-1">
                                <p><span className="font-medium">{t('generatorModal.projectGoal')}</span> {projectGoal || t('generatorModal.projectGoalNotDefined')}</p>
                                {stakeholderGroups.length > 0 && (
                                    <p><span className="font-medium">{t('generatorModal.stakeholderGroups')}</span> {stakeholderGroups.map(g => g.name || tEnums(`stakeholderTypes.${g.group_type}.name`)).join(', ')}</p>
                                )}
                                {rejectionReason && (
                                    <p className="text-red-600"><span className="font-medium">{t('generatorModal.rejectionReason')}</span> {rejectionReason}</p>
                                )}
                            </div>
                        </div>

                        {/* Focus Input */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('generatorModal.focusLabel')}
                            </label>
                            <input
                                type="text"
                                value={focus}
                                onChange={(e) => setFocus(e.target.value)}
                                placeholder={t('generatorModal.focusPlaceholder')}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                disabled={isGenerating || isSaving}
                            />
                        </div>

                        {/* Generate Button */}
                        {!generated && (
                            <button
                                onClick={handleGenerate}
                                disabled={isGenerating}
                                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
                            >
                                {isGenerating ? (
                                    <>
                                        <Loader2 size={18} className="animate-spin" />
                                        {t('generatorModal.generating')}
                                    </>
                                ) : (
                                    t('generatorModal.generateButton')
                                )}
                            </button>
                        )}

                        {/* Error Display */}
                        {error && (
                            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                                {error}
                            </div>
                        )}

                        {/* Generated Recommendation (Editable) */}
                        {generated && (
                            <div className="space-y-4 border-t border-gray-200 pt-6">
                                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
                                    {t('generatorModal.generatedTitle')}
                                </h3>

                                {/* Title */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('generatorModal.titleLabel')}</label>
                                    <input
                                        type="text"
                                        value={editedTitle}
                                        onChange={(e) => setEditedTitle(e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        disabled={isSaving}
                                    />
                                </div>

                                {/* Description */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('generatorModal.descriptionLabel')}</label>
                                    <textarea
                                        value={editedDescription}
                                        onChange={(e) => setEditedDescription(e.target.value)}
                                        rows={3}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                                        disabled={isSaving}
                                    />
                                </div>

                                {/* Type & Priority */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">{t('generatorModal.typeLabel')}</label>
                                        <select
                                            value={editedType}
                                            onChange={(e) => setEditedType(e.target.value as RecommendationType)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            disabled={isSaving}
                                        >
                                            {Object.entries(RECOMMENDATION_TYPE_INFO).map(([key, info]) => (
                                                <option key={key} value={key}>
                                                    {info.icon} {info.label}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">{t('generatorModal.priorityLabel')}</label>
                                        <select
                                            value={editedPriority}
                                            onChange={(e) => setEditedPriority(e.target.value as RecommendationPriority)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            disabled={isSaving}
                                        >
                                            {Object.entries(PRIORITY_INFO).map(([key, info]) => (
                                                <option key={key} value={key}>{info.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                {/* Affected Groups */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">{t('generatorModal.affectedGroupsLabel')}</label>
                                    <div className="flex flex-wrap gap-2">
                                        <label className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded cursor-pointer hover:bg-gray-200">
                                            <input
                                                type="checkbox"
                                                checked={editedAffectedGroups.includes('all')}
                                                onChange={handleToggleAll}
                                                disabled={isSaving}
                                            />
                                            <span className="text-sm">{tCommon('all')}</span>
                                        </label>
                                        {stakeholderGroups.map(group => (
                                            <label
                                                key={group.id}
                                                className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded cursor-pointer hover:bg-gray-200"
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={editedAffectedGroups.includes(group.id) || editedAffectedGroups.includes('all')}
                                                    onChange={() => handleToggleGroup(group.id)}
                                                    disabled={isSaving || editedAffectedGroups.includes('all')}
                                                />
                                                <span className="text-sm">
                                                    {GROUP_TYPE_INFO[group.group_type]?.icon} {group.name || tEnums(`stakeholderTypes.${group.group_type}.name`)}
                                                </span>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                {/* Steps */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">{t('generatorModal.stepsLabel')}</label>
                                    <div className="space-y-2">
                                        {editedSteps.map((step, index) => (
                                            <div key={index} className="flex items-center gap-2">
                                                <span className="text-sm text-gray-500 w-6">{index + 1}.</span>
                                                <input
                                                    type="text"
                                                    value={step}
                                                    onChange={(e) => handleUpdateStep(index, e.target.value)}
                                                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                    placeholder={t('generatorModal.stepPlaceholder')}
                                                    disabled={isSaving}
                                                />
                                                <button
                                                    onClick={() => handleRemoveStep(index)}
                                                    className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                                                    disabled={isSaving}
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        ))}
                                        <button
                                            onClick={handleAddStep}
                                            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                                            disabled={isSaving}
                                        >
                                            <Plus size={14} />
                                            {t('generatorModal.addStep')}
                                        </button>
                                    </div>
                                </div>

                                {/* Regenerate Button */}
                                <button
                                    onClick={handleGenerate}
                                    disabled={isGenerating}
                                    className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
                                >
                                    {isGenerating ? (
                                        <Loader2 size={14} className="animate-spin" />
                                    ) : (
                                        <span>{t('generatorModal.regenerate')}</span>
                                    )}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Chat Panel (Right side - only shown after generation) */}
                    {showChat && (
                        <div style={{
                            flex: '0 0 40%',
                            minHeight: 0,
                            position: 'relative',
                            overflow: 'hidden'
                        }}>
                            <div style={{
                                position: 'absolute',
                                top: 0,
                                left: 0,
                                right: 0,
                                bottom: 0,
                                display: 'flex',
                                flexDirection: 'column'
                            }}>
                                <GeneratorChatPanel
                                    messages={messages}
                                    onSendMessage={sendMessage}
                                    isTyping={isTyping}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div style={{ flexShrink: 0 }} className="px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
                    <button
                        onClick={onClose}
                        disabled={isGenerating || isSaving || isTyping}
                        className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                    >
                        {tCommon('buttons.cancel')}
                    </button>
                    {generated && (
                        <button
                            onClick={handleSave}
                            disabled={isSaving || !editedTitle.trim() || isTyping}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
                        >
                            {isSaving ? (
                                <>
                                    <Loader2 size={16} className="animate-spin" />
                                    {tCommon('buttons.saving')}
                                </>
                            ) : (
                                tCommon('buttons.save')
                            )}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );

    return createPortal(modalContent, document.body);
}
