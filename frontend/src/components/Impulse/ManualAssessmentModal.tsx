import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';
import type { StakeholderGroupWithAssessments, IndicatorDefinition, CreateStakeholderAssessmentRequest } from '../../types/stakeholder';

interface ManualAssessmentModalProps {
    group: StakeholderGroupWithAssessments;
    onClose: () => void;
    onSave: (assessments: CreateStakeholderAssessmentRequest[], assessedAt: string) => Promise<void>;
}

interface AssessmentValue {
    rating: number | null;
    notes: string;
}

export function ManualAssessmentModal({ group, onClose, onSave }: ManualAssessmentModalProps) {
    const { t } = useTranslation('impulse');
    const { t: tCommon } = useTranslation('common');
    const today = new Date().toISOString().split('T')[0];
    const [assessedAt, setAssessedAt] = useState(today);
    const [values, setValues] = useState<Record<string, AssessmentValue>>(() => {
        const initial: Record<string, AssessmentValue> = {};
        for (const indicator of group.available_indicators) {
            // Pre-fill with existing assessment if any
            const existing = group.assessments.find(a => a.indicator_key === indicator.key);
            initial[indicator.key] = {
                rating: existing?.rating ?? null,
                notes: existing?.notes ?? ''
            };
        }
        return initial;
    });
    const [isSaving, setIsSaving] = useState(false);

    const handleRatingChange = (indicatorKey: string, rating: number) => {
        setValues(prev => ({
            ...prev,
            [indicatorKey]: { ...prev[indicatorKey], rating }
        }));
    };

    const handleNotesChange = (indicatorKey: string, notes: string) => {
        setValues(prev => ({
            ...prev,
            [indicatorKey]: { ...prev[indicatorKey], notes }
        }));
    };

    const handleSave = async () => {
        // Convert to assessment requests
        const assessments: CreateStakeholderAssessmentRequest[] = [];
        for (const [indicatorKey, value] of Object.entries(values)) {
            if (value.rating !== null) {
                assessments.push({
                    indicator_key: indicatorKey,
                    rating: value.rating,
                    notes: value.notes || undefined
                });
            }
        }

        if (assessments.length === 0) {
            alert(t('modal.rateAtLeastOne'));
            return;
        }

        setIsSaving(true);
        try {
            await onSave(assessments, assessedAt);
            onClose();
        } catch (error) {
            console.error('Failed to save assessments:', error);
            alert(t('modal.saveFailed'));
        } finally {
            setIsSaving(false);
        }
    };

    const completedCount = Object.values(values).filter(v => v.rating !== null).length;
    const totalCount = group.available_indicators.length;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between shrink-0">
                    <div>
                        <h2 className="text-lg font-semibold text-gray-800">
                            {t('modal.title')} - {group.name || group.group_type}
                        </h2>
                        <p className="text-sm text-gray-500">
                            {t('modal.factorsRated', { completed: completedCount, total: totalCount })}
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <X size={20} className="text-gray-500" />
                    </button>
                </div>

                {/* Date Picker */}
                <div className="px-6 py-4 border-b border-gray-100 shrink-0">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        {t('modal.dateLabel')}
                    </label>
                    <input
                        type="date"
                        value={assessedAt}
                        max={today}
                        onChange={(e) => setAssessedAt(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                        {t('modal.dateHint')}
                    </p>
                </div>

                {/* Indicators List */}
                <div className="flex-1 overflow-y-auto px-6 py-4">
                    <div className="space-y-6">
                        {group.available_indicators.map((indicator: IndicatorDefinition) => (
                            <IndicatorRating
                                key={indicator.key}
                                indicator={indicator}
                                value={values[indicator.key]}
                                onChange={(rating) => handleRatingChange(indicator.key, rating)}
                                onNotesChange={(notes) => handleNotesChange(indicator.key, notes)}
                            />
                        ))}
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3 shrink-0">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        {tCommon('buttons.cancel')}
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={isSaving || completedCount === 0}
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSaving ? tCommon('buttons.saving') : tCommon('buttons.save')}
                    </button>
                </div>
            </div>
        </div>
    );
}

interface IndicatorRatingProps {
    indicator: IndicatorDefinition;
    value: AssessmentValue;
    onChange: (rating: number) => void;
    onNotesChange: (notes: string) => void;
}

function IndicatorRating({ indicator, value, onChange, onNotesChange }: IndicatorRatingProps) {
    const { t: tCommon } = useTranslation('common');
    return (
        <div className="border-b border-gray-100 pb-5 last:border-b-0">
            <h4 className="font-medium text-gray-800 mb-1">{indicator.name}</h4>
            <p className="text-sm text-gray-500 mb-3">{indicator.description}</p>

            {/* Rating Scale */}
            <div className="flex items-center gap-1 mb-3">
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((rating) => (
                    <button
                        key={rating}
                        onClick={() => onChange(rating)}
                        className={`w-8 h-8 rounded-lg text-sm font-medium transition-all ${
                            value.rating === rating
                                ? 'bg-blue-600 text-white shadow-md scale-110'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                    >
                        {rating}
                    </button>
                ))}
                {value.rating && (
                    <span className="ml-2 text-sm text-gray-500">
                        ({value.rating}/10)
                    </span>
                )}
            </div>

            {/* Notes */}
            <input
                type="text"
                placeholder={tCommon('labels.notesOptional')}
                value={value.notes}
                onChange={(e) => onNotesChange(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
        </div>
    );
}
