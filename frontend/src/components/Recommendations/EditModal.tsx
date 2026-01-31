import { useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Loader2, Plus, Trash2 } from 'lucide-react';
import type { Recommendation, RecommendationType, RecommendationPriority, UpdateRecommendationRequest } from '../../types/recommendation';
import { RECOMMENDATION_TYPE_INFO, PRIORITY_INFO } from '../../types/recommendation';
import type { StakeholderGroup } from '../../types/stakeholder';
import { GROUP_TYPE_INFO } from '../../types/stakeholder';
import { updateRecommendation } from '../../services/api';

interface EditModalProps {
    recommendation: Recommendation;
    stakeholderGroups: StakeholderGroup[];
    onClose: () => void;
    onSaved: () => void;
}

export function EditModal({ recommendation, stakeholderGroups, onClose, onSaved }: EditModalProps) {
    const [title, setTitle] = useState(recommendation.title);
    const [description, setDescription] = useState(recommendation.description || '');
    const [type, setType] = useState<RecommendationType>(recommendation.recommendation_type);
    const [priority, setPriority] = useState<RecommendationPriority>(recommendation.priority);
    const [affectedGroups, setAffectedGroups] = useState<string[]>(recommendation.affected_groups);
    const [steps, setSteps] = useState<string[]>(recommendation.steps);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSave = async () => {
        if (!title.trim()) {
            setError('Bitte geben Sie einen Titel ein');
            return;
        }

        setIsSaving(true);
        setError(null);
        try {
            const data: UpdateRecommendationRequest = {
                title: title.trim(),
                description: description.trim() || undefined,
                recommendation_type: type,
                priority,
                affected_groups: affectedGroups.length > 0 ? affectedGroups : ['all'],
                steps: steps.filter(s => s.trim())
            };
            await updateRecommendation(recommendation.id, data);
            onSaved();
            onClose();
        } catch (err) {
            console.error('Failed to update recommendation:', err);
            setError(err instanceof Error ? err.message : 'Fehler beim Speichern');
        } finally {
            setIsSaving(false);
        }
    };

    const handleToggleGroup = (groupId: string) => {
        if (affectedGroups.includes('all')) {
            setAffectedGroups([groupId]);
        } else if (affectedGroups.includes(groupId)) {
            setAffectedGroups(affectedGroups.filter(g => g !== groupId));
        } else {
            setAffectedGroups([...affectedGroups, groupId]);
        }
    };

    const handleToggleAll = () => {
        if (affectedGroups.includes('all')) {
            setAffectedGroups([]);
        } else {
            setAffectedGroups(['all']);
        }
    };

    const handleAddStep = () => {
        setSteps([...steps, '']);
    };

    const handleRemoveStep = (index: number) => {
        setSteps(steps.filter((_, i) => i !== index));
    };

    const handleUpdateStep = (index: number, value: string) => {
        const newSteps = [...steps];
        newSteps[index] = value;
        setSteps(newSteps);
    };

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
                if (e.target === e.currentTarget && !isSaving) onClose();
            }}
        >
            <div
                style={{
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                    width: '100%',
                    maxWidth: '40rem',
                    maxHeight: '90vh',
                    display: 'flex',
                    flexDirection: 'column',
                }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
                    <h2 className="text-lg font-semibold text-gray-800">
                        Empfehlung bearbeiten
                    </h2>
                    <button
                        onClick={onClose}
                        disabled={isSaving}
                        className="p-2 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
                    >
                        <X size={20} className="text-gray-500" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {/* Title */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Titel:</label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            disabled={isSaving}
                        />
                    </div>

                    {/* Description */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Beschreibung:</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                            disabled={isSaving}
                        />
                    </div>

                    {/* Type & Priority */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Typ:</label>
                            <select
                                value={type}
                                onChange={(e) => setType(e.target.value as RecommendationType)}
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
                            <label className="block text-sm font-medium text-gray-700 mb-1">Prioritaet:</label>
                            <select
                                value={priority}
                                onChange={(e) => setPriority(e.target.value as RecommendationPriority)}
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
                        <label className="block text-sm font-medium text-gray-700 mb-2">Betroffene Gruppen:</label>
                        <div className="flex flex-wrap gap-2">
                            <label className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded cursor-pointer hover:bg-gray-200">
                                <input
                                    type="checkbox"
                                    checked={affectedGroups.includes('all')}
                                    onChange={handleToggleAll}
                                    disabled={isSaving}
                                />
                                <span className="text-sm">Alle</span>
                            </label>
                            {stakeholderGroups.map(group => (
                                <label
                                    key={group.id}
                                    className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded cursor-pointer hover:bg-gray-200"
                                >
                                    <input
                                        type="checkbox"
                                        checked={affectedGroups.includes(group.id) || affectedGroups.includes('all')}
                                        onChange={() => handleToggleGroup(group.id)}
                                        disabled={isSaving || affectedGroups.includes('all')}
                                    />
                                    <span className="text-sm">
                                        {GROUP_TYPE_INFO[group.group_type]?.icon} {group.name || GROUP_TYPE_INFO[group.group_type]?.name}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Steps */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Konkrete Schritte:</label>
                        <div className="space-y-2">
                            {steps.map((step, index) => (
                                <div key={index} className="flex items-center gap-2">
                                    <span className="text-sm text-gray-500 w-6">{index + 1}.</span>
                                    <input
                                        type="text"
                                        value={step}
                                        onChange={(e) => handleUpdateStep(index, e.target.value)}
                                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Schritt beschreiben..."
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
                                Schritt hinzufuegen
                            </button>
                        </div>
                    </div>

                    {error && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                            {error}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3 flex-shrink-0">
                    <button
                        onClick={onClose}
                        disabled={isSaving}
                        className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                    >
                        Abbrechen
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={isSaving || !title.trim()}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                        {isSaving ? (
                            <>
                                <Loader2 size={16} className="animate-spin" />
                                Speichern...
                            </>
                        ) : (
                            'Speichern'
                        )}
                    </button>
                </div>
            </div>
        </div>
    );

    return createPortal(modalContent, document.body);
}
