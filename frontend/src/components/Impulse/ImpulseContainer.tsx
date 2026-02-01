import { useEffect, useState, Fragment } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';
import { Zap, Plus, RefreshCw, X, ClipboardCheck, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { useStakeholder } from '../../context/StakeholderContext';
import { useRefresh, useRefreshSignal } from '../../context/RefreshContext';
import { ManualAssessmentModal } from './ManualAssessmentModal';
import { SurveyGeneratorModal } from './SurveyGeneratorModal';
import type { ImpulseHistory } from '../../types/impulse';
import type { StakeholderGroup, StakeholderGroupWithAssessments, CreateStakeholderAssessmentRequest } from '../../types/stakeholder';
import { getImpulseHistory, getStakeholderGroup, batchAddAssessmentsWithDate } from '../../services/api';
import { GROUP_TYPE_INFO } from '../../types/stakeholder';

interface ImpulseContainerProps {
    projectId: string;
}

// Historical assessment entry for the list
interface HistoricalAssessment {
    groupId: string;
    groupName: string | null;
    groupType: string;
    date: string;
    averageRating: number;
    ratings: Record<string, number>;
    notes: Record<string, string>;
    source: 'manual' | 'survey';
}

export function ImpulseContainer({ projectId }: ImpulseContainerProps) {
    const { t } = useTranslation('impulse');
    const { t: tEnums } = useTranslation('enums');
    const { groups, isLoading, loadGroups } = useStakeholder();
    const { triggerRefresh } = useRefresh();
    const impulsesRefreshSignal = useRefreshSignal('impulses');
    const [impulseHistories, setImpulseHistories] = useState<Record<string, ImpulseHistory>>({});
    const [selectedGroupForAssessment, setSelectedGroupForAssessment] = useState<StakeholderGroupWithAssessments | null>(null);
    const [selectedGroupForSurvey, setSelectedGroupForSurvey] = useState<StakeholderGroupWithAssessments | null>(null);
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);
    const [showGroupSelector, setShowGroupSelector] = useState(false);
    const [expandedRowId, setExpandedRowId] = useState<string | null>(null);

    useEffect(() => {
        loadGroups(projectId);
    }, [projectId, loadGroups, impulsesRefreshSignal]);

    useEffect(() => {
        const fetchHistories = async () => {
            if (groups.length === 0) return;
            setIsLoadingHistory(true);
            try {
                const histories: Record<string, ImpulseHistory> = {};
                await Promise.all(
                    groups.map(async (group) => {
                        try {
                            const history = await getImpulseHistory(group.id);
                            histories[group.id] = history;
                        } catch (err) {
                            console.error(`Failed to load impulse history for group ${group.id}:`, err);
                        }
                    })
                );
                setImpulseHistories(histories);
            } finally {
                setIsLoadingHistory(false);
            }
        };
        fetchHistories();
    }, [groups, impulsesRefreshSignal]);

    const handleRefresh = async () => {
        await loadGroups(projectId);
    };

    const handleOpenManualAssessment = async (groupId: string) => {
        try {
            const groupWithAssessments = await getStakeholderGroup(groupId);
            setSelectedGroupForAssessment(groupWithAssessments);
            setShowGroupSelector(false);
        } catch (err) {
            console.error('Failed to load group details:', err);
        }
    };

    const handleOpenSurveyGenerator = async (groupId: string) => {
        try {
            const groupWithAssessments = await getStakeholderGroup(groupId);
            setSelectedGroupForSurvey(groupWithAssessments);
            setShowGroupSelector(false);
        } catch (err) {
            console.error('Failed to load group details:', err);
        }
    };

    const handleSaveAssessments = async (assessments: CreateStakeholderAssessmentRequest[], assessedAt: string) => {
        if (!selectedGroupForAssessment) return;
        await batchAddAssessmentsWithDate(selectedGroupForAssessment.id, assessments, assessedAt);
        // Refresh the history for this group
        try {
            const history = await getImpulseHistory(selectedGroupForAssessment.id);
            setImpulseHistories(prev => ({
                ...prev,
                [selectedGroupForAssessment.id]: history
            }));
            // Trigger refresh for dashboard and other components
            triggerRefresh('impulses');
        } catch (err) {
            console.error('Failed to refresh impulse history:', err);
        }
    };

    // Helper to get translated group name
    const getGroupName = (groupName: string | null, groupType: string) => {
        if (groupName) return groupName;
        return tEnums(`stakeholderTypes.${groupType}.name`, { defaultValue: groupType });
    };

    // Build historical assessments list from all impulse histories
    const allHistoricalAssessments: HistoricalAssessment[] = [];
    for (const group of groups) {
        const history = impulseHistories[group.id];
        if (history?.impulses) {
            for (const impulse of history.impulses) {
                allHistoricalAssessments.push({
                    groupId: group.id,
                    groupName: group.name || null,
                    groupType: group.group_type,
                    date: impulse.date,
                    averageRating: impulse.average_rating,
                    ratings: impulse.ratings,
                    notes: impulse.notes,
                    source: impulse.source
                });
            }
        }
    }
    // Sort by date descending
    allHistoricalAssessments.sort((a, b) => b.date.localeCompare(a.date));

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const locale = import.meta.env.VITE_LOCALE === 'de' ? 'de-DE' : 'en-US';
        return date.toLocaleDateString(locale, {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    };

    return (
        <Fragment>
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-4xl mx-auto space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Zap className="text-yellow-500" size={24} />
                            <h1 className="text-2xl font-bold text-gray-800">{t('title')}</h1>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={handleRefresh}
                                disabled={isLoading || isLoadingHistory}
                                className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <RefreshCw size={16} className={(isLoading || isLoadingHistory) ? 'animate-spin' : ''} />
                            </button>
                            <button
                                onClick={() => setShowGroupSelector(true)}
                                disabled={groups.length === 0}
                                className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Plus size={16} />
                                {t('newImpulse')}
                            </button>
                        </div>
                    </div>

                    {/* Description */}
                    <p className="text-sm text-gray-600">
                        {t('description')}
                    </p>

                    {/* Loading State */}
                    {(isLoading && groups.length === 0) ? (
                        <div className="flex items-center justify-center py-20">
                            <RefreshCw size={32} className="text-gray-400 animate-spin" />
                        </div>
                    ) : groups.length === 0 ? (
                        <div className="text-center py-20">
                            <Zap size={48} className="mx-auto text-gray-300 mb-4" />
                            <h2 className="text-lg font-medium text-gray-700 mb-2">{t('noGroups.title')}</h2>
                            <p className="text-sm text-gray-500">
                                {t('noGroups.description')}
                            </p>
                        </div>
                    ) : (
                        <>
                            {/* Historical Assessments List */}
                            <div className="space-y-4">
                                <h2 className="text-lg font-semibold text-gray-700">{t('allImpulses')}</h2>
                                {allHistoricalAssessments.length === 0 ? (
                                    <div className="bg-gray-50 rounded-lg p-6 text-center">
                                        <p className="text-sm text-gray-500">{t('noImpulses')}</p>
                                    </div>
                                ) : (
                                    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                                        <table className="w-full">
                                            <thead className="bg-gray-50 border-b border-gray-200">
                                                <tr>
                                                    <th className="w-8 px-2"></th>
                                                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('table.date')}</th>
                                                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('table.group')}</th>
                                                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('table.type')}</th>
                                                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('table.average')}</th>
                                                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('table.source')}</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-100">
                                                {allHistoricalAssessments.map((assessment, idx) => {
                                                    const typeInfo = GROUP_TYPE_INFO[assessment.groupType as keyof typeof GROUP_TYPE_INFO];
                                                    const rowId = `${assessment.groupId}-${assessment.date}-${idx}`;
                                                    const isExpanded = expandedRowId === rowId;
                                                    const indicatorEntries = Object.entries(assessment.ratings);
                                                    return (
                                                        <Fragment key={rowId}>
                                                            <tr
                                                                className="hover:bg-gray-50 cursor-pointer transition-colors"
                                                                onClick={() => setExpandedRowId(isExpanded ? null : rowId)}
                                                            >
                                                                <td className="px-2 py-3 text-gray-400">
                                                                    {isExpanded ? (
                                                                        <ChevronUp size={16} />
                                                                    ) : (
                                                                        <ChevronDown size={16} />
                                                                    )}
                                                                </td>
                                                                <td className="px-4 py-3 text-sm text-gray-900">
                                                                    {formatDate(assessment.date)}
                                                                </td>
                                                                <td className="px-4 py-3 text-sm text-gray-900">
                                                                    <div className="flex items-center gap-2">
                                                                        <span>{typeInfo?.icon || '👤'}</span>
                                                                        <span>{getGroupName(assessment.groupName, assessment.groupType)}</span>
                                                                    </div>
                                                                </td>
                                                                <td className="px-4 py-3 text-sm text-gray-500">
                                                                    {tEnums(`stakeholderTypes.${assessment.groupType}.name`, { defaultValue: assessment.groupType })}
                                                                </td>
                                                                <td className="px-4 py-3 text-sm text-right">
                                                                    <span className={`font-semibold ${
                                                                        assessment.averageRating >= 7 ? 'text-green-600' :
                                                                        assessment.averageRating >= 5 ? 'text-yellow-600' :
                                                                        'text-red-600'
                                                                    }`}>
                                                                        {assessment.averageRating.toFixed(1)}
                                                                    </span>
                                                                </td>
                                                                <td className="px-4 py-3 text-sm">
                                                                    {assessment.source === 'survey' ? (
                                                                        <span className="inline-flex items-center gap-1 text-purple-600">
                                                                            <FileText size={14} />
                                                                            {t('source.survey')}
                                                                        </span>
                                                                    ) : (
                                                                        <span className="inline-flex items-center gap-1 text-blue-600">
                                                                            <ClipboardCheck size={14} />
                                                                            {t('source.manual')}
                                                                        </span>
                                                                    )}
                                                                </td>
                                                            </tr>
                                                            {/* Expanded Details Row */}
                                                            {isExpanded && (
                                                                <tr className="bg-gray-50">
                                                                    <td colSpan={6} className="px-4 py-4">
                                                                        <div className="pl-6">
                                                                            <h4 className="text-sm font-medium text-gray-700 mb-3">
                                                                                {t('details.title')}
                                                                            </h4>
                                                                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                                                                                {indicatorEntries.map(([key, rating]) => {
                                                                                    const indicatorName = t(`indicators.${key}`, { defaultValue: key });
                                                                                    const note = assessment.notes[key];
                                                                                    return (
                                                                                        <div
                                                                                            key={key}
                                                                                            className="bg-white rounded-lg border border-gray-200 p-3"
                                                                                        >
                                                                                            <div className="flex items-center justify-between mb-1">
                                                                                                <span className="text-sm font-medium text-gray-700 truncate">
                                                                                                    {indicatorName}
                                                                                                </span>
                                                                                                <span className={`text-lg font-bold ${
                                                                                                    rating >= 7 ? 'text-green-600' :
                                                                                                    rating >= 5 ? 'text-yellow-600' :
                                                                                                    'text-red-600'
                                                                                                }`}>
                                                                                                    {rating.toFixed(1)}
                                                                                                </span>
                                                                                            </div>
                                                                                            {/* Rating bar */}
                                                                                            <div className="w-full bg-gray-200 rounded-full h-2">
                                                                                                <div
                                                                                                    className={`h-2 rounded-full ${
                                                                                                        rating >= 7 ? 'bg-green-500' :
                                                                                                        rating >= 5 ? 'bg-yellow-500' :
                                                                                                        'bg-red-500'
                                                                                                    }`}
                                                                                                    style={{ width: `${rating * 10}%` }}
                                                                                                />
                                                                                            </div>
                                                                                            {note && (
                                                                                                <p className="text-xs text-gray-500 mt-2 italic">
                                                                                                    {note}
                                                                                                </p>
                                                                                            )}
                                                                                        </div>
                                                                                    );
                                                                                })}
                                                                            </div>
                                                                            {indicatorEntries.length === 0 && (
                                                                                <p className="text-sm text-gray-500 italic">
                                                                                    {t('details.noRatings')}
                                                                                </p>
                                                                            )}
                                                                        </div>
                                                                    </td>
                                                                </tr>
                                                            )}
                                                        </Fragment>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Group Selector Modal - rendered via portal */}
            {showGroupSelector && createPortal(
                <GroupSelectorModal
                    groups={groups}
                    onSelectManual={handleOpenManualAssessment}
                    onSelectSurvey={handleOpenSurveyGenerator}
                    onClose={() => setShowGroupSelector(false)}
                />,
                document.body
            )}

            {/* Manual Assessment Modal */}
            {selectedGroupForAssessment && (
                <ManualAssessmentModal
                    group={selectedGroupForAssessment}
                    onClose={() => setSelectedGroupForAssessment(null)}
                    onSave={handleSaveAssessments}
                />
            )}

            {/* Survey Generator Modal */}
            {selectedGroupForSurvey && (
                <SurveyGeneratorModal
                    group={selectedGroupForSurvey}
                    projectId={projectId}
                    impulseHistory={impulseHistories[selectedGroupForSurvey.id]}
                    onClose={() => setSelectedGroupForSurvey(null)}
                />
            )}
        </Fragment>
    );
}

// Group Selector Modal Component
interface GroupSelectorModalProps {
    groups: StakeholderGroup[];
    onSelectManual: (groupId: string) => void;
    onSelectSurvey: (groupId: string) => void;
    onClose: () => void;
}

function GroupSelectorModal({ groups, onSelectManual, onSelectSurvey, onClose }: GroupSelectorModalProps) {
    const { t } = useTranslation('impulse');
    const { t: tCommon } = useTranslation('common');
    const { t: tEnums } = useTranslation('enums');
    const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);

    const selectedGroup = selectedGroupId ? groups.find(g => g.id === selectedGroupId) : null;
    const canCreateSurvey = selectedGroup?.group_type === 'mitarbeitende' || selectedGroup?.group_type === 'multiplikatoren';

    return (
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
                if (e.target === e.currentTarget) onClose();
            }}
        >
            <div
                style={{
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                    width: '100%',
                    maxWidth: '28rem',
                    maxHeight: '90vh',
                    display: 'flex',
                    flexDirection: 'column',
                }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div style={{ padding: '16px 24px', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
                    <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#1f2937' }}>{t('newImpulse')}</h2>
                    <button
                        onClick={onClose}
                        style={{ padding: '8px', borderRadius: '8px', border: 'none', background: 'transparent', cursor: 'pointer' }}
                    >
                        <X size={20} color="#6b7280" />
                    </button>
                </div>

                {/* Content */}
                <div style={{ padding: '16px 24px', overflowY: 'auto', flex: 1 }}>
                    <label style={{ display: 'block', fontSize: '14px', fontWeight: 500, color: '#374151', marginBottom: '12px' }}>
                        {t('selectGroup')}
                    </label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {groups.map(group => {
                            const typeInfo = GROUP_TYPE_INFO[group.group_type];
                            const isSelected = selectedGroupId === group.id;
                            return (
                                <button
                                    key={group.id}
                                    onClick={() => setSelectedGroupId(group.id)}
                                    style={{
                                        width: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '12px',
                                        padding: '12px',
                                        borderRadius: '8px',
                                        border: isSelected ? '2px solid #eab308' : '2px solid #e5e7eb',
                                        backgroundColor: isSelected ? '#fefce8' : 'white',
                                        textAlign: 'left',
                                        cursor: 'pointer',
                                    }}
                                >
                                    <span style={{ fontSize: '24px', flexShrink: 0 }}>{typeInfo?.icon || '👤'}</span>
                                    <div style={{ minWidth: 0 }}>
                                        <p style={{ fontWeight: 500, color: '#1f2937', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {group.name || tEnums(`stakeholderTypes.${group.group_type}.name`)}
                                        </p>
                                        <p style={{ fontSize: '12px', color: '#6b7280', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {tEnums(`stakeholderTypes.${group.group_type}.subtitle`)} | {group.mendelow_quadrant}
                                        </p>
                                    </div>
                                </button>
                            );
                        })}
                    </div>

                    {/* Action Selection (when group is selected) */}
                    {selectedGroup && (
                        <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #e5e7eb' }}>
                            <p style={{ fontSize: '14px', fontWeight: 500, color: '#374151', marginBottom: '12px' }}>{t('selectAction')}</p>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <button
                                    onClick={() => onSelectManual(selectedGroup.id)}
                                    style={{
                                        flex: 1,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '8px',
                                        padding: '12px 16px',
                                        backgroundColor: '#2563eb',
                                        color: 'white',
                                        borderRadius: '8px',
                                        border: 'none',
                                        fontSize: '14px',
                                        fontWeight: 500,
                                        cursor: 'pointer',
                                    }}
                                >
                                    <ClipboardCheck size={18} />
                                    {t('manualAssessment')}
                                </button>
                                {canCreateSurvey && (
                                    <button
                                        onClick={() => onSelectSurvey(selectedGroup.id)}
                                        style={{
                                            flex: 1,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            gap: '8px',
                                            padding: '12px 16px',
                                            backgroundColor: '#9333ea',
                                            color: 'white',
                                            borderRadius: '8px',
                                            border: 'none',
                                            fontSize: '14px',
                                            fontWeight: 500,
                                            cursor: 'pointer',
                                        }}
                                    >
                                        <FileText size={18} />
                                        {t('createSurvey')}
                                    </button>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div style={{ padding: '16px 24px', borderTop: '1px solid #e5e7eb', display: 'flex', justifyContent: 'flex-end', flexShrink: 0 }}>
                    <button
                        onClick={onClose}
                        style={{
                            padding: '8px 16px',
                            fontSize: '14px',
                            fontWeight: 500,
                            color: '#374151',
                            backgroundColor: 'transparent',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: 'pointer',
                        }}
                    >
                        {tCommon('buttons.cancel')}
                    </button>
                </div>
            </div>
        </div>
    );
}
