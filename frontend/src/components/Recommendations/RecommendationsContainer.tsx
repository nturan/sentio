import { useEffect, useState, Fragment } from 'react';
import { Lightbulb, Plus, RefreshCw, Filter } from 'lucide-react';
import { useStakeholder } from '../../context/StakeholderContext';
import { useProjects } from '../../context/ProjectContext';
import { RecommendationCard } from './RecommendationCard';
import { GeneratorModal } from './GeneratorModal';
import { RejectModal } from './RejectModal';
import { EditModal } from './EditModal';
import type { Recommendation, RecommendationStatus } from '../../types/recommendation';
import { RECOMMENDATION_STATUS_INFO } from '../../types/recommendation';
import { listRecommendations, updateRecommendation } from '../../services/api';

interface RecommendationsContainerProps {
    projectId: string;
    onNavigateToImpulse?: () => void;
}

type FilterStatus = 'all' | RecommendationStatus;

export function RecommendationsContainer({ projectId, onNavigateToImpulse }: RecommendationsContainerProps) {
    const { groups, loadGroups } = useStakeholder();
    const { selectedProject } = useProjects();
    const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');

    // Modal states
    const [showGeneratorModal, setShowGeneratorModal] = useState(false);
    const [rejectingRecommendation, setRejectingRecommendation] = useState<Recommendation | null>(null);
    const [editingRecommendation, setEditingRecommendation] = useState<Recommendation | null>(null);
    const [regeneratingFrom, setRegeneratingFrom] = useState<Recommendation | null>(null);

    useEffect(() => {
        loadGroups(projectId);
        fetchRecommendations();
    }, [projectId]);

    const fetchRecommendations = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await listRecommendations(projectId);
            setRecommendations(data);
        } catch (err) {
            console.error('Failed to fetch recommendations:', err);
            setError(err instanceof Error ? err.message : 'Fehler beim Laden');
        } finally {
            setIsLoading(false);
        }
    };

    const handleRefresh = () => {
        fetchRecommendations();
    };

    const handleApprove = async (id: string) => {
        try {
            await updateRecommendation(id, { status: 'approved' });
            fetchRecommendations();
        } catch (err) {
            console.error('Failed to approve recommendation:', err);
        }
    };

    const handleReject = (id: string) => {
        const rec = recommendations.find(r => r.id === id);
        if (rec) {
            setRejectingRecommendation(rec);
        }
    };

    const handleStart = async (id: string) => {
        try {
            await updateRecommendation(id, { status: 'started' });
            fetchRecommendations();
        } catch (err) {
            console.error('Failed to start recommendation:', err);
        }
    };

    const handleComplete = async (id: string) => {
        try {
            await updateRecommendation(id, { status: 'completed' });
            fetchRecommendations();
        } catch (err) {
            console.error('Failed to complete recommendation:', err);
        }
    };

    const handleEdit = (recommendation: Recommendation) => {
        setEditingRecommendation(recommendation);
    };

    const handleRegenerate = (recommendation: Recommendation) => {
        setRegeneratingFrom(recommendation);
    };

    const handleMeasureImpact = (recommendation: Recommendation) => {
        // Navigate to Impulse tab
        if (onNavigateToImpulse) {
            onNavigateToImpulse();
        }
    };

    const filteredRecommendations = filterStatus === 'all'
        ? recommendations
        : recommendations.filter(r => r.status === filterStatus);

    // Group recommendations by status for display
    const groupedRecommendations = {
        pending_approval: filteredRecommendations.filter(r => r.status === 'pending_approval'),
        approved: filteredRecommendations.filter(r => r.status === 'approved'),
        started: filteredRecommendations.filter(r => r.status === 'started'),
        completed: filteredRecommendations.filter(r => r.status === 'completed'),
        rejected: filteredRecommendations.filter(r => r.status === 'rejected'),
    };

    const filterButtons: { value: FilterStatus; label: string }[] = [
        { value: 'all', label: 'Alle' },
        { value: 'pending_approval', label: 'Ausstehend' },
        { value: 'approved', label: 'Genehmigt' },
        { value: 'started', label: 'Gestartet' },
        { value: 'completed', label: 'Abgeschlossen' },
        { value: 'rejected', label: 'Abgelehnt' },
    ];

    return (
        <Fragment>
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-4xl mx-auto space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Lightbulb className="text-amber-500" size={24} />
                            <h1 className="text-2xl font-bold text-gray-800">Handlungsempfehlungen</h1>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={handleRefresh}
                                disabled={isLoading}
                                className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
                            </button>
                            <button
                                onClick={() => setShowGeneratorModal(true)}
                                className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors text-sm font-medium"
                            >
                                <Plus size={16} />
                                Neue Empfehlung generieren
                            </button>
                        </div>
                    </div>

                    {/* Filter Buttons */}
                    <div className="flex items-center gap-2 flex-wrap">
                        <Filter size={16} className="text-gray-400" />
                        {filterButtons.map(btn => (
                            <button
                                key={btn.value}
                                onClick={() => setFilterStatus(btn.value)}
                                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                                    filterStatus === btn.value
                                        ? 'bg-amber-100 text-amber-700'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                            >
                                {btn.label}
                                {btn.value !== 'all' && (
                                    <span className="ml-1 text-gray-400">
                                        ({groupedRecommendations[btn.value as RecommendationStatus].length})
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Error Display */}
                    {error && (
                        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                            {error}
                        </div>
                    )}

                    {/* Loading State */}
                    {isLoading && recommendations.length === 0 ? (
                        <div className="flex items-center justify-center py-20">
                            <RefreshCw size={32} className="text-gray-400 animate-spin" />
                        </div>
                    ) : filteredRecommendations.length === 0 ? (
                        <div className="text-center py-20">
                            <Lightbulb size={48} className="mx-auto text-gray-300 mb-4" />
                            <h2 className="text-lg font-medium text-gray-700 mb-2">
                                {filterStatus === 'all'
                                    ? 'Noch keine Handlungsempfehlungen'
                                    : `Keine Empfehlungen mit Status "${RECOMMENDATION_STATUS_INFO[filterStatus as RecommendationStatus]?.label || filterStatus}"`
                                }
                            </h2>
                            <p className="text-sm text-gray-500 mb-4">
                                Generieren Sie eine neue Empfehlung basierend auf Ihren Impulsen und Stakeholder-Daten.
                            </p>
                            <button
                                onClick={() => setShowGeneratorModal(true)}
                                className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors text-sm font-medium"
                            >
                                <Plus size={16} />
                                Empfehlung generieren
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {filterStatus === 'all' ? (
                                // Grouped view when showing all
                                <>
                                    {groupedRecommendations.pending_approval.length > 0 && (
                                        <div className="space-y-3">
                                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                                                Ausstehend ({groupedRecommendations.pending_approval.length})
                                            </h2>
                                            {groupedRecommendations.pending_approval.map(rec => (
                                                <RecommendationCard
                                                    key={rec.id}
                                                    recommendation={rec}
                                                    stakeholderGroups={groups}
                                                    onApprove={handleApprove}
                                                    onReject={handleReject}
                                                    onStart={handleStart}
                                                    onComplete={handleComplete}
                                                    onEdit={handleEdit}
                                                    onRegenerate={handleRegenerate}
                                                    onMeasureImpact={handleMeasureImpact}
                                                />
                                            ))}
                                        </div>
                                    )}
                                    {groupedRecommendations.approved.length > 0 && (
                                        <div className="space-y-3">
                                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                                                Genehmigt ({groupedRecommendations.approved.length})
                                            </h2>
                                            {groupedRecommendations.approved.map(rec => (
                                                <RecommendationCard
                                                    key={rec.id}
                                                    recommendation={rec}
                                                    stakeholderGroups={groups}
                                                    onApprove={handleApprove}
                                                    onReject={handleReject}
                                                    onStart={handleStart}
                                                    onComplete={handleComplete}
                                                    onEdit={handleEdit}
                                                    onRegenerate={handleRegenerate}
                                                    onMeasureImpact={handleMeasureImpact}
                                                />
                                            ))}
                                        </div>
                                    )}
                                    {groupedRecommendations.started.length > 0 && (
                                        <div className="space-y-3">
                                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                                                Gestartet ({groupedRecommendations.started.length})
                                            </h2>
                                            {groupedRecommendations.started.map(rec => (
                                                <RecommendationCard
                                                    key={rec.id}
                                                    recommendation={rec}
                                                    stakeholderGroups={groups}
                                                    onApprove={handleApprove}
                                                    onReject={handleReject}
                                                    onStart={handleStart}
                                                    onComplete={handleComplete}
                                                    onEdit={handleEdit}
                                                    onRegenerate={handleRegenerate}
                                                    onMeasureImpact={handleMeasureImpact}
                                                />
                                            ))}
                                        </div>
                                    )}
                                    {groupedRecommendations.completed.length > 0 && (
                                        <div className="space-y-3">
                                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                                                Abgeschlossen ({groupedRecommendations.completed.length})
                                            </h2>
                                            {groupedRecommendations.completed.map(rec => (
                                                <RecommendationCard
                                                    key={rec.id}
                                                    recommendation={rec}
                                                    stakeholderGroups={groups}
                                                    onApprove={handleApprove}
                                                    onReject={handleReject}
                                                    onStart={handleStart}
                                                    onComplete={handleComplete}
                                                    onEdit={handleEdit}
                                                    onRegenerate={handleRegenerate}
                                                    onMeasureImpact={handleMeasureImpact}
                                                />
                                            ))}
                                        </div>
                                    )}
                                    {groupedRecommendations.rejected.length > 0 && (
                                        <div className="space-y-3">
                                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                                                Abgelehnt ({groupedRecommendations.rejected.length})
                                            </h2>
                                            {groupedRecommendations.rejected.map(rec => (
                                                <RecommendationCard
                                                    key={rec.id}
                                                    recommendation={rec}
                                                    stakeholderGroups={groups}
                                                    onApprove={handleApprove}
                                                    onReject={handleReject}
                                                    onStart={handleStart}
                                                    onComplete={handleComplete}
                                                    onEdit={handleEdit}
                                                    onRegenerate={handleRegenerate}
                                                    onMeasureImpact={handleMeasureImpact}
                                                />
                                            ))}
                                        </div>
                                    )}
                                </>
                            ) : (
                                // Flat list when filtering
                                filteredRecommendations.map(rec => (
                                    <RecommendationCard
                                        key={rec.id}
                                        recommendation={rec}
                                        stakeholderGroups={groups}
                                        onApprove={handleApprove}
                                        onReject={handleReject}
                                        onStart={handleStart}
                                        onComplete={handleComplete}
                                        onEdit={handleEdit}
                                        onRegenerate={handleRegenerate}
                                        onMeasureImpact={handleMeasureImpact}
                                    />
                                ))
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Generator Modal */}
            {showGeneratorModal && (
                <GeneratorModal
                    projectId={projectId}
                    stakeholderGroups={groups}
                    projectGoal={selectedProject?.goal || null}
                    onClose={() => setShowGeneratorModal(false)}
                    onSaved={fetchRecommendations}
                />
            )}

            {/* Regenerate Modal (from rejected) */}
            {regeneratingFrom && (
                <GeneratorModal
                    projectId={projectId}
                    stakeholderGroups={groups}
                    projectGoal={selectedProject?.goal || null}
                    rejectedRecommendationId={regeneratingFrom.id}
                    rejectionReason={regeneratingFrom.rejection_reason || undefined}
                    onClose={() => setRegeneratingFrom(null)}
                    onSaved={fetchRecommendations}
                />
            )}

            {/* Reject Modal */}
            {rejectingRecommendation && (
                <RejectModal
                    recommendation={rejectingRecommendation}
                    onClose={() => setRejectingRecommendation(null)}
                    onRejected={fetchRecommendations}
                />
            )}

            {/* Edit Modal */}
            {editingRecommendation && (
                <EditModal
                    recommendation={editingRecommendation}
                    stakeholderGroups={groups}
                    onClose={() => setEditingRecommendation(null)}
                    onSaved={fetchRecommendations}
                />
            )}
        </Fragment>
    );
}
