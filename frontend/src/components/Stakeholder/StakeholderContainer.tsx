import { useEffect, useState, Fragment } from 'react';
import { createPortal } from 'react-dom';
import { Users, Plus, RefreshCw, X, ClipboardCheck, FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useStakeholder } from '../../context/StakeholderContext';
import { MendelowMatrix } from './MendelowMatrix';
import { StakeholderGroupCard } from './StakeholderGroupCard';
import { AddStakeholderModal } from './AddStakeholderModal';
import { ManualAssessmentModal } from '../Impulse/ManualAssessmentModal';
import { SurveyGeneratorModal } from '../Impulse/SurveyGeneratorModal';
import type { CreateStakeholderGroupRequest, StakeholderGroupWithAssessments, CreateStakeholderAssessmentRequest } from '../../types/stakeholder';
import { getStakeholderGroup, batchAddAssessmentsWithDate, getImpulseHistory } from '../../services/api';
import type { ImpulseHistory } from '../../types/impulse';

interface StakeholderContainerProps {
    projectId: string;
}

export function StakeholderContainer({ projectId }: StakeholderContainerProps) {
    const {
        groups,
        isLoading,
        loadGroups,
        createGroup,
        selectGroup,
        deleteGroup,
    } = useStakeholder();
    const { t } = useTranslation('stakeholder');

    const [showAddModal, setShowAddModal] = useState(false);
    const [selectedGroupForImpulse, setSelectedGroupForImpulse] = useState<StakeholderGroupWithAssessments | null>(null);
    const [selectedGroupForSurvey, setSelectedGroupForSurvey] = useState<StakeholderGroupWithAssessments | null>(null);
    const [impulseHistoryForSurvey, setImpulseHistoryForSurvey] = useState<ImpulseHistory | undefined>(undefined);
    const [showActionChoice, setShowActionChoice] = useState<StakeholderGroupWithAssessments | null>(null);

    useEffect(() => {
        loadGroups(projectId);
    }, [projectId, loadGroups]);

    const handleCreateGroup = async (data: CreateStakeholderGroupRequest) => {
        await createGroup(projectId, data);
    };

    const handleDeleteGroup = async (groupId: string) => {
        if (confirm(t('deleteConfirm'))) {
            await deleteGroup(groupId);
        }
    };

    const handleStartImpulse = async (groupId: string) => {
        try {
            const groupWithAssessments = await getStakeholderGroup(groupId);
            // For Mitarbeitende and Multiplikatoren, show choice modal
            if (groupWithAssessments.group_type === 'mitarbeitende' || groupWithAssessments.group_type === 'multiplikatoren') {
                setShowActionChoice(groupWithAssessments);
            } else {
                // For Fuehrungskraefte, go directly to manual assessment
                setSelectedGroupForImpulse(groupWithAssessments);
            }
        } catch (err) {
            console.error('Failed to load group details:', err);
        }
    };

    const handleChooseManual = () => {
        if (showActionChoice) {
            setSelectedGroupForImpulse(showActionChoice);
            setShowActionChoice(null);
        }
    };

    const handleChooseSurvey = async () => {
        if (showActionChoice) {
            setSelectedGroupForSurvey(showActionChoice);
            // Also fetch impulse history for context
            try {
                const history = await getImpulseHistory(showActionChoice.id);
                setImpulseHistoryForSurvey(history);
            } catch (err) {
                console.error('Failed to load impulse history:', err);
            }
            setShowActionChoice(null);
        }
    };

    const handleSaveImpulse = async (assessments: CreateStakeholderAssessmentRequest[], assessedAt: string) => {
        if (!selectedGroupForImpulse) return;
        await batchAddAssessmentsWithDate(selectedGroupForImpulse.id, assessments, assessedAt);
        // Refresh groups
        loadGroups(projectId);
    };

    return (
        <Fragment>
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-6xl mx-auto space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Users className="text-blue-600" size={24} />
                            <h1 className="text-2xl font-bold text-gray-800">{t('title')}</h1>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => loadGroups(projectId)}
                                disabled={isLoading}
                                className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
                            </button>
                            <button
                                onClick={() => setShowAddModal(true)}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                            >
                                <Plus size={16} />
                                {t('addGroup')}
                            </button>
                        </div>
                    </div>

                    {isLoading && groups.length === 0 ? (
                        <div className="flex items-center justify-center py-20">
                            <RefreshCw size={32} className="text-gray-400 animate-spin" />
                        </div>
                    ) : groups.length === 0 ? (
                        <div className="text-center py-20">
                            <Users size={48} className="mx-auto text-gray-300 mb-4" />
                            <h2 className="text-lg font-medium text-gray-700 mb-2">{t('noGroups.title')}</h2>
                            <p className="text-sm text-gray-500 mb-4">
                                {t('noGroups.description')}
                            </p>
                            <button
                                onClick={() => setShowAddModal(true)}
                                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                            >
                                <Plus size={16} />
                                {t('addFirstGroup')}
                            </button>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            {/* Stakeholder List */}
                            <div className="lg:col-span-2 space-y-4">
                                <h2 className="text-lg font-semibold text-gray-700">{t('groupsTitle')}</h2>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {groups.map(group => (
                                        <StakeholderGroupCard
                                            key={group.id}
                                            group={group}
                                            onSelect={() => selectGroup(group.id)}
                                            onDelete={() => handleDeleteGroup(group.id)}
                                            onStartImpulse={() => handleStartImpulse(group.id)}
                                        />
                                    ))}
                                </div>
                            </div>

                            {/* Mendelow Matrix */}
                            <div>
                                <MendelowMatrix
                                    groups={groups}
                                    onSelectGroup={(groupId) => selectGroup(groupId)}
                                />
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Add Modal - rendered outside scrollable container */}
            {showAddModal && (
                <AddStakeholderModal
                    onClose={() => setShowAddModal(false)}
                    onSubmit={handleCreateGroup}
                />
            )}

            {/* Action Choice Modal for Mitarbeitende/Multiplikatoren */}
            {showActionChoice && createPortal(
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
                    onClick={() => setShowActionChoice(null)}
                >
                    <div
                        style={{
                            backgroundColor: 'white',
                            borderRadius: '12px',
                            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                            width: '100%',
                            maxWidth: '400px',
                            padding: '24px',
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#1f2937', margin: 0 }}>
                                {t('newImpulse')}
                            </h2>
                            <button
                                onClick={() => setShowActionChoice(null)}
                                style={{ padding: '8px', background: 'transparent', border: 'none', cursor: 'pointer' }}
                            >
                                <X size={20} color="#6b7280" />
                            </button>
                        </div>
                        <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '20px' }}>
                            {t('impulseChoice', { groupName: showActionChoice.name || showActionChoice.group_type })}
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            <button
                                onClick={handleChooseManual}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '8px',
                                    padding: '14px 20px',
                                    backgroundColor: '#2563eb',
                                    color: 'white',
                                    borderRadius: '8px',
                                    border: 'none',
                                    fontSize: '14px',
                                    fontWeight: 500,
                                    cursor: 'pointer',
                                }}
                            >
                                <ClipboardCheck size={20} />
                                {t('manualAssessment')}
                            </button>
                            <button
                                onClick={handleChooseSurvey}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '8px',
                                    padding: '14px 20px',
                                    backgroundColor: '#9333ea',
                                    color: 'white',
                                    borderRadius: '8px',
                                    border: 'none',
                                    fontSize: '14px',
                                    fontWeight: 500,
                                    cursor: 'pointer',
                                }}
                            >
                                <FileText size={20} />
                                {t('createSurvey')}
                            </button>
                        </div>
                    </div>
                </div>,
                document.body
            )}

            {/* Manual Assessment Modal */}
            {selectedGroupForImpulse && (
                <ManualAssessmentModal
                    group={selectedGroupForImpulse}
                    onClose={() => setSelectedGroupForImpulse(null)}
                    onSave={handleSaveImpulse}
                />
            )}

            {/* Survey Generator Modal */}
            {selectedGroupForSurvey && (
                <SurveyGeneratorModal
                    group={selectedGroupForSurvey}
                    projectId={projectId}
                    impulseHistory={impulseHistoryForSurvey}
                    onClose={() => {
                        setSelectedGroupForSurvey(null);
                        setImpulseHistoryForSurvey(undefined);
                    }}
                />
            )}
        </Fragment>
    );
}
