import { useState } from 'react';
import { ChevronLeft, Save, Loader2, Info } from 'lucide-react';
import type { StakeholderGroupWithAssessments, CreateStakeholderAssessmentRequest } from '../../types/stakeholder';
import { GROUP_TYPE_INFO } from '../../types/stakeholder';

interface StakeholderAssessmentProps {
    group: StakeholderGroupWithAssessments;
    onBack: () => void;
    onSave: (assessments: CreateStakeholderAssessmentRequest[]) => Promise<void>;
}

export function StakeholderAssessment({ group, onBack, onSave }: StakeholderAssessmentProps) {
    const [ratings, setRatings] = useState<Record<string, { rating: number; notes: string }>>(() => {
        // Initialize with existing assessments
        const initial: Record<string, { rating: number; notes: string }> = {};
        for (const assessment of group.assessments) {
            initial[assessment.indicator_key] = {
                rating: assessment.rating,
                notes: assessment.notes || ''
            };
        }
        return initial;
    });
    const [isSaving, setIsSaving] = useState(false);

    const typeInfo = GROUP_TYPE_INFO[group.group_type];

    const handleRatingChange = (indicatorKey: string, rating: number) => {
        setRatings(prev => ({
            ...prev,
            [indicatorKey]: {
                ...prev[indicatorKey],
                rating,
                notes: prev[indicatorKey]?.notes || ''
            }
        }));
    };

    const handleNotesChange = (indicatorKey: string, notes: string) => {
        setRatings(prev => ({
            ...prev,
            [indicatorKey]: {
                ...prev[indicatorKey],
                notes,
                rating: prev[indicatorKey]?.rating || 5
            }
        }));
    };

    const handleSubmit = async () => {
        const assessments: CreateStakeholderAssessmentRequest[] = Object.entries(ratings)
            .filter(([_, value]) => value.rating > 0)
            .map(([key, value]) => ({
                indicator_key: key,
                rating: value.rating,
                notes: value.notes || undefined
            }));

        if (assessments.length === 0) {
            alert('Bitte bewerten Sie mindestens einen Indikator.');
            return;
        }

        setIsSaving(true);
        try {
            await onSave(assessments);
            onBack();
        } catch (error) {
            console.error('Failed to save assessments:', error);
            alert('Fehler beim Speichern der Bewertungen.');
        } finally {
            setIsSaving(false);
        }
    };

    const getCompletionCount = () => {
        return Object.values(ratings).filter(r => r.rating > 0).length;
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <button
                    onClick={onBack}
                    className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4"
                >
                    <ChevronLeft size={18} />
                    Zurueck zur Uebersicht
                </button>

                <div className="flex items-center gap-3">
                    <span className="text-3xl">{typeInfo.icon}</span>
                    <div>
                        <h2 className="text-xl font-semibold text-gray-800">
                            {group.name || typeInfo.name} bewerten
                        </h2>
                        <p className="text-sm text-gray-500">
                            {getCompletionCount()} von {group.available_indicators.length} Indikatoren bewertet
                        </p>
                    </div>
                </div>
            </div>

            {/* Rating Scale Legend */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-blue-800 mb-2">Bewertungsskala</h3>
                <div className="flex justify-between text-xs text-blue-700">
                    <span>1 = Sehr schlecht</span>
                    <span>5 = Mittelmaeßig</span>
                    <span>10 = Ausgezeichnet</span>
                </div>
            </div>

            {/* Indicators */}
            <div className="space-y-4">
                {group.available_indicators.map((indicator) => {
                    const currentRating = ratings[indicator.key]?.rating || 0;
                    const currentNotes = ratings[indicator.key]?.notes || '';

                    return (
                        <div
                            key={indicator.key}
                            className="bg-white rounded-xl border border-gray-200 p-4"
                        >
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex-1">
                                    <h4 className="font-medium text-gray-800">{indicator.name}</h4>
                                    <div className="flex items-start gap-1 mt-1">
                                        <Info size={14} className="text-gray-400 shrink-0 mt-0.5" />
                                        <p className="text-xs text-gray-500">{indicator.description}</p>
                                    </div>
                                </div>
                                {currentRating > 0 && (
                                    <span className={`text-lg font-bold ${
                                        currentRating <= 3 ? 'text-red-600' :
                                        currentRating <= 5 ? 'text-orange-500' :
                                        currentRating <= 7 ? 'text-yellow-600' :
                                        'text-green-600'
                                    }`}>
                                        {currentRating * 10}%
                                    </span>
                                )}
                            </div>

                            {/* Rating Slider */}
                            <div className="mb-3">
                                <div className="flex items-center gap-3">
                                    <span className="text-xs text-gray-400 w-4">1</span>
                                    <input
                                        type="range"
                                        min="1"
                                        max="10"
                                        value={currentRating || 5}
                                        onChange={(e) => handleRatingChange(indicator.key, parseInt(e.target.value))}
                                        className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                    />
                                    <span className="text-xs text-gray-400 w-4">10</span>
                                </div>
                                <div className="flex justify-between mt-1 px-4">
                                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => (
                                        <button
                                            key={n}
                                            onClick={() => handleRatingChange(indicator.key, n)}
                                            className={`w-6 h-6 rounded-full text-xs font-medium transition-colors ${
                                                currentRating === n
                                                    ? 'bg-blue-600 text-white'
                                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                            }`}
                                        >
                                            {n}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Notes */}
                            <textarea
                                value={currentNotes}
                                onChange={(e) => handleNotesChange(indicator.key, e.target.value)}
                                placeholder="Optionale Notizen zur Bewertung..."
                                rows={2}
                                className="w-full border border-gray-200 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
                            />
                        </div>
                    );
                })}
            </div>

            {/* Submit Button */}
            <div className="sticky bottom-0 bg-gray-50 py-4 -mx-6 px-6 border-t border-gray-200">
                <button
                    onClick={handleSubmit}
                    disabled={isSaving || getCompletionCount() === 0}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isSaving ? (
                        <>
                            <Loader2 size={18} className="animate-spin" />
                            Wird gespeichert...
                        </>
                    ) : (
                        <>
                            <Save size={18} />
                            Bewertung speichern
                        </>
                    )}
                </button>
            </div>
        </div>
    );
}
