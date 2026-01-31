import { useState } from 'react';
import { X, Sparkles, FileText, Plus, Trash2, Save, Loader2 } from 'lucide-react';
import type { StakeholderGroupWithAssessments } from '../../types/stakeholder';
import type { ImpulseHistory, Survey, SurveyQuestion, SurveyQuestionType } from '../../types/impulse';
import { GROUP_TYPE_INFO } from '../../types/stakeholder';
import { generateSurvey, saveSurvey } from '../../services/api';

interface SurveyGeneratorModalProps {
    group: StakeholderGroupWithAssessments;
    projectId: string;
    impulseHistory?: ImpulseHistory;
    onClose: () => void;
}

export function SurveyGeneratorModal({ group, projectId, impulseHistory, onClose }: SurveyGeneratorModalProps) {
    const [isGenerating, setIsGenerating] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [survey, setSurvey] = useState<Survey | null>(null);
    const [savedPath, setSavedPath] = useState<string | null>(null);

    const typeInfo = GROUP_TYPE_INFO[group.group_type];

    // Calculate context info for display
    const impulses = impulseHistory?.impulses || [];
    const avgRating = impulses.length > 0
        ? (impulses.reduce((sum, i) => sum + i.average_rating, 0) / impulses.length).toFixed(1)
        : null;

    // Find weakest indicator
    let weakestIndicator: { key: string; avg: number } | null = null;
    if (impulses.length > 0) {
        const indicatorSums: Record<string, { sum: number; count: number }> = {};
        for (const impulse of impulses) {
            for (const [key, rating] of Object.entries(impulse.ratings)) {
                if (!indicatorSums[key]) {
                    indicatorSums[key] = { sum: 0, count: 0 };
                }
                indicatorSums[key].sum += rating;
                indicatorSums[key].count += 1;
            }
        }
        let minAvg = 11;
        for (const [key, data] of Object.entries(indicatorSums)) {
            const avg = data.sum / data.count;
            if (avg < minAvg) {
                minAvg = avg;
                weakestIndicator = { key, avg };
            }
        }
    }

    const handleGenerate = async () => {
        setIsGenerating(true);
        try {
            const response = await generateSurvey(group.id);
            setSurvey(response.survey);
        } catch (err) {
            console.error('Failed to generate survey:', err);
            alert('Fehler beim Generieren der Umfrage.');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSave = async () => {
        if (!survey) return;
        setIsSaving(true);
        try {
            const response = await saveSurvey(group.id, survey);
            setSavedPath(response.file_path);
        } catch (err) {
            console.error('Failed to save survey:', err);
            alert('Fehler beim Speichern der Umfrage.');
        } finally {
            setIsSaving(false);
        }
    };

    const updateSurveyField = (field: keyof Survey, value: string) => {
        if (!survey) return;
        setSurvey({ ...survey, [field]: value });
    };

    const updateQuestion = (index: number, field: keyof SurveyQuestion, value: string | boolean) => {
        if (!survey) return;
        const newQuestions = [...survey.questions];
        newQuestions[index] = { ...newQuestions[index], [field]: value };
        setSurvey({ ...survey, questions: newQuestions });
    };

    const addQuestion = () => {
        if (!survey) return;
        const newQuestion: SurveyQuestion = {
            id: `q-${Date.now()}`,
            type: 'scale',
            question: '',
            includeJustification: false
        };
        setSurvey({ ...survey, questions: [...survey.questions, newQuestion] });
    };

    const removeQuestion = (index: number) => {
        if (!survey) return;
        const newQuestions = survey.questions.filter((_, i) => i !== index);
        setSurvey({ ...survey, questions: newQuestions });
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between shrink-0">
                    <div>
                        <h2 className="text-lg font-semibold text-gray-800">
                            Umfrage erstellen - {group.name || typeInfo?.name}
                        </h2>
                        <p className="text-sm text-gray-500">
                            {typeInfo?.subtitle}
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <X size={20} className="text-gray-500" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto px-6 py-4">
                    {/* Context Info */}
                    <div className="bg-gray-50 rounded-lg p-4 mb-6">
                        <h3 className="text-sm font-medium text-gray-700 mb-2">Kontext fuer den Agenten:</h3>
                        <ul className="text-sm text-gray-600 space-y-1">
                            <li>
                                <span className="text-gray-400">•</span> Gruppe: {group.name || typeInfo?.name}
                            </li>
                            <li>
                                <span className="text-gray-400">•</span> Position: {group.mendelow_quadrant} ({group.mendelow_strategy})
                            </li>
                            {avgRating && (
                                <li>
                                    <span className="text-gray-400">•</span> Letzte {impulses.length} Impulse: Durchschnitt {avgRating}
                                </li>
                            )}
                            {weakestIndicator && (
                                <li>
                                    <span className="text-gray-400">•</span> Schwachstelle: {weakestIndicator.key} (Durchschnitt {weakestIndicator.avg.toFixed(1)})
                                </li>
                            )}
                        </ul>
                    </div>

                    {/* Generate Button or Survey Editor */}
                    {!survey ? (
                        <div className="text-center py-8">
                            <button
                                onClick={handleGenerate}
                                disabled={isGenerating}
                                className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:opacity-50"
                            >
                                {isGenerating ? (
                                    <>
                                        <Loader2 size={20} className="animate-spin" />
                                        Generiere Umfrage...
                                    </>
                                ) : (
                                    <>
                                        <Sparkles size={20} />
                                        Umfrage generieren
                                    </>
                                )}
                            </button>
                        </div>
                    ) : savedPath ? (
                        <div className="text-center py-8">
                            <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-lg mb-4">
                                <FileText size={20} />
                                Umfrage gespeichert!
                            </div>
                            <p className="text-sm text-gray-600">
                                Gespeichert unter: <code className="bg-gray-100 px-2 py-1 rounded">{savedPath}</code>
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Survey Title & Description */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Titel
                                </label>
                                <input
                                    type="text"
                                    value={survey.title}
                                    onChange={(e) => updateSurveyField('title', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Beschreibung
                                </label>
                                <textarea
                                    value={survey.description}
                                    onChange={(e) => updateSurveyField('description', e.target.value)}
                                    rows={2}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                                />
                            </div>

                            {/* Questions */}
                            <div>
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="text-sm font-medium text-gray-700">Fragen</h3>
                                    <button
                                        onClick={addQuestion}
                                        className="inline-flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700"
                                    >
                                        <Plus size={16} />
                                        Frage hinzufuegen
                                    </button>
                                </div>

                                <div className="space-y-4">
                                    {survey.questions.map((question, index) => (
                                        <QuestionEditor
                                            key={question.id}
                                            index={index}
                                            question={question}
                                            onUpdate={(field, value) => updateQuestion(index, field, value)}
                                            onRemove={() => removeQuestion(index)}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3 shrink-0">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        {savedPath ? 'Schliessen' : 'Abbrechen'}
                    </button>
                    {survey && !savedPath && (
                        <button
                            onClick={handleSave}
                            disabled={isSaving}
                            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                        >
                            {isSaving ? (
                                <>
                                    <Loader2 size={16} className="animate-spin" />
                                    Speichere...
                                </>
                            ) : (
                                <>
                                    <Save size={16} />
                                    Als Markdown speichern
                                </>
                            )}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

interface QuestionEditorProps {
    index: number;
    question: SurveyQuestion;
    onUpdate: (field: keyof SurveyQuestion, value: string | boolean) => void;
    onRemove: () => void;
}

function QuestionEditor({ index, question, onUpdate, onRemove }: QuestionEditorProps) {
    return (
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
            <div className="flex items-start justify-between gap-4 mb-3">
                <span className="text-sm font-medium text-gray-500">Frage {index + 1}</span>
                <div className="flex items-center gap-2">
                    <select
                        value={question.type}
                        onChange={(e) => onUpdate('type', e.target.value as SurveyQuestionType)}
                        className="text-sm border border-gray-300 rounded px-2 py-1"
                    >
                        <option value="scale">Skala (1-10)</option>
                        <option value="freetext">Freitext</option>
                    </select>
                    <button
                        onClick={onRemove}
                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                    >
                        <Trash2 size={16} />
                    </button>
                </div>
            </div>

            <input
                type="text"
                value={question.question}
                onChange={(e) => onUpdate('question', e.target.value)}
                placeholder="Fragetext eingeben..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-sm"
            />

            {question.type === 'scale' && (
                <label className="flex items-center gap-2 mt-2 text-sm text-gray-600">
                    <input
                        type="checkbox"
                        checked={question.includeJustification || false}
                        onChange={(e) => onUpdate('includeJustification', e.target.checked)}
                        className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                    />
                    Begruendung optional
                </label>
            )}
        </div>
    );
}
