import { useState } from 'react';
import { X } from 'lucide-react';
import type { StakeholderGroupType, PowerLevel, InterestLevel, CreateStakeholderGroupRequest } from '../../types/stakeholder';
import { GROUP_TYPE_INFO } from '../../types/stakeholder';

interface AddStakeholderModalProps {
    onClose: () => void;
    onSubmit: (data: CreateStakeholderGroupRequest) => Promise<void>;
}

const ALL_GROUP_TYPES: StakeholderGroupType[] = ['fuehrungskraefte', 'multiplikatoren', 'mitarbeitende'];

export function AddStakeholderModal({ onClose, onSubmit }: AddStakeholderModalProps) {
    const [selectedType, setSelectedType] = useState<StakeholderGroupType | null>(null);
    const [name, setName] = useState('');
    const [powerLevel, setPowerLevel] = useState<PowerLevel>('high');
    const [interestLevel, setInterestLevel] = useState<InterestLevel>('high');
    const [notes, setNotes] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async () => {
        if (!selectedType) return;

        setIsSubmitting(true);
        try {
            await onSubmit({
                group_type: selectedType,
                name: name.trim() || undefined,
                power_level: powerLevel,
                interest_level: interestLevel,
                notes: notes || undefined
            });
            onClose();
        } catch (error) {
            console.error('Failed to create stakeholder group:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    // Get placeholder name based on selected type
    const getPlaceholderName = () => {
        if (!selectedType) return '';
        return GROUP_TYPE_INFO[selectedType].name;
    };

    return (
        <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
            <div className="bg-white w-[500px] max-w-[95vw] max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200 shrink-0">
                    <h2 className="text-lg font-semibold text-gray-800">Stakeholder-Gruppe hinzufuegen</h2>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="p-4 space-y-6 overflow-y-auto flex-1">
                    {/* Step 1: Select Type */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            1. Gruppentyp waehlen
                        </label>
                        <div className="space-y-2">
                            {ALL_GROUP_TYPES.map(type => {
                                const info = GROUP_TYPE_INFO[type];
                                return (
                                    <button
                                        key={type}
                                        onClick={() => setSelectedType(type)}
                                        className={`w-full p-3 rounded-lg border-2 text-left transition-all ${
                                            selectedType === type
                                                ? 'border-blue-500 bg-blue-50'
                                                : 'border-gray-200 hover:border-gray-300'
                                        }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <span className="text-2xl">{info.icon}</span>
                                            <div>
                                                <div className="font-medium text-gray-800">{info.name}</div>
                                                <div className="text-xs text-gray-500">{info.subtitle}</div>
                                            </div>
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Step 2: Name */}
                    {selectedType && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                2. Name der Gruppe
                            </label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder={getPlaceholderName()}
                                className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                            />
                            <p className="text-xs text-gray-400 mt-1">
                                Optional - falls leer, wird der Gruppentyp als Name verwendet
                            </p>
                        </div>
                    )}

                    {/* Step 3: Mendelow Classification */}
                    {selectedType && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                3. Mendelow-Klassifizierung
                            </label>

                            <div className="grid grid-cols-2 gap-4">
                                {/* Power Level */}
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Macht</label>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setPowerLevel('high')}
                                            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                                                powerLevel === 'high'
                                                    ? 'bg-blue-600 text-white'
                                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                            }`}
                                        >
                                            Hoch
                                        </button>
                                        <button
                                            onClick={() => setPowerLevel('low')}
                                            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                                                powerLevel === 'low'
                                                    ? 'bg-blue-600 text-white'
                                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                            }`}
                                        >
                                            Niedrig
                                        </button>
                                    </div>
                                </div>

                                {/* Interest Level */}
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Interesse</label>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setInterestLevel('high')}
                                            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                                                interestLevel === 'high'
                                                    ? 'bg-blue-600 text-white'
                                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                            }`}
                                        >
                                            Hoch
                                        </button>
                                        <button
                                            onClick={() => setInterestLevel('low')}
                                            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                                                interestLevel === 'low'
                                                    ? 'bg-blue-600 text-white'
                                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                            }`}
                                        >
                                            Niedrig
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Quadrant Preview */}
                            <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm">
                                <span className="font-medium">Quadrant: </span>
                                {powerLevel === 'high' && interestLevel === 'high' && 'Key Players (Eng einbinden)'}
                                {powerLevel === 'high' && interestLevel === 'low' && 'Keep Satisfied (Zufrieden halten)'}
                                {powerLevel === 'low' && interestLevel === 'high' && 'Keep Informed (Informiert halten)'}
                                {powerLevel === 'low' && interestLevel === 'low' && 'Monitor (Beobachten)'}
                            </div>
                        </div>
                    )}

                    {/* Step 4: Notes (optional) */}
                    {selectedType && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                4. Notizen (optional)
                            </label>
                            <textarea
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                placeholder="Zusaetzliche Informationen zur Gruppe..."
                                rows={3}
                                className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
                            />
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-3 p-4 border-t border-gray-200 shrink-0">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        Abbrechen
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={!selectedType || isSubmitting}
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSubmitting ? 'Wird erstellt...' : 'Hinzufuegen'}
                    </button>
                </div>
            </div>
        </div>
    );
}
