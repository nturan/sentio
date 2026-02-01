import { useState, useCallback, useMemo } from 'react';
import { X, Sparkles, FileText, Plus, Trash2, Save, Loader2 } from 'lucide-react';
import type { StakeholderGroupWithAssessments } from '../../types/stakeholder';
import type { ImpulseHistory, Survey, SurveyQuestion, SurveyQuestionType } from '../../types/impulse';
import { GROUP_TYPE_INFO } from '../../types/stakeholder';
import { generateSurvey, saveSurvey } from '../../services/api';
import { useGeneratorChat } from '../../hooks/useGeneratorChat';
import { GeneratorChatPanel } from '../GeneratorChat';
import type { SurveyCanvasData } from '../../types/generatorChat';

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

    // Canvas data for chat
    const canvasData = useMemo<SurveyCanvasData>(() => ({
        title: survey?.title || '',
        description: survey?.description || '',
        questions: survey?.questions || [],
        estimated_duration: survey?.estimated_duration
    }), [survey]);

    // Handle canvas updates from chat
    const handleCanvasUpdate = useCallback((updates: Partial<SurveyCanvasData>) => {
        if (!survey) return;

        setSurvey(prev => {
            if (!prev) return prev;
            return {
                ...prev,
                title: updates.title !== undefined ? updates.title : prev.title,
                description: updates.description !== undefined ? updates.description : prev.description,
                questions: updates.questions !== undefined ? updates.questions as SurveyQuestion[] : prev.questions,
                estimated_duration: updates.estimated_duration !== undefined ? updates.estimated_duration : prev.estimated_duration
            };
        });
    }, [survey]);

    // Generator chat hook
    const { messages, sendMessage, isTyping } = useGeneratorChat<SurveyCanvasData>(
        canvasData,
        {
            projectId,
            generatorType: 'survey',
            onCanvasUpdate: handleCanvasUpdate
        }
    );

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

    // Show chat after survey is generated and not yet saved
    const showChat = survey !== null && !savedPath;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
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
            >
                {/* Header */}
                <div style={{ flexShrink: 0 }} className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
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
                        disabled={isTyping}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
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
                        {/* Context Info - Compact */}
                        <div className="bg-gray-50 rounded-lg px-3 py-2 text-xs text-gray-600 flex flex-wrap gap-x-4 gap-y-1">
                            <span><strong>Gruppe:</strong> {group.name || typeInfo?.name}</span>
                            <span><strong>Position:</strong> {group.mendelow_quadrant}</span>
                            {avgRating && <span><strong>Impulse:</strong> {impulses.length}x, Ø {avgRating}</span>}
                            {weakestIndicator && <span><strong>Schwach:</strong> {weakestIndicator.key} ({weakestIndicator.avg.toFixed(1)})</span>}
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

                    {/* Chat Panel (Right side - only shown after generation and before save) */}
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
                                    placeholder="Fragen zur Umfrage oder Aenderungswuensche..."
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div style={{ flexShrink: 0 }} className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        disabled={isTyping}
                        className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                    >
                        {savedPath ? 'Schliessen' : 'Abbrechen'}
                    </button>
                    {survey && !savedPath && (
                        <button
                            onClick={handleSave}
                            disabled={isSaving || isTyping}
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
