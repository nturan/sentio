import { useState, useRef, useCallback } from 'react';
import { X, ChevronRight, FileText, Upload, Trash2, CheckCircle, Loader2 } from 'lucide-react';
import { Button } from '../common/Button';
import { useProjects } from '../../context/ProjectContext';
import { API_CONFIG, post } from '../../services/api';

interface UploadedFile {
    file: File;
    status: 'pending' | 'uploading' | 'success' | 'error';
    error?: string;
}

interface OnboardingModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function OnboardingModal({ isOpen, onClose }: OnboardingModalProps) {
    const { addProject } = useProjects();
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        name: '',
        icon: '🚀',
        goal: ''
    });
    const [files, setFiles] = useState<UploadedFile[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // All hooks must be called before any early return!
    const handleFileSelect = useCallback((selectedFiles: FileList | null) => {
        if (!selectedFiles) return;

        const newFiles: UploadedFile[] = Array.from(selectedFiles).map(file => ({
            file,
            status: 'pending'
        }));

        setFiles(prev => [...prev, ...newFiles]);
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        handleFileSelect(e.dataTransfer.files);
    }, [handleFileSelect]);

    const removeFile = useCallback((index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    }, []);

    // Early return AFTER all hooks
    if (!isOpen) return null;

    const handleNext = () => {
        if (step < 3) {
            setStep(step + 1);
        } else {
            handleAddProject();
        }
    };

    const handleAddProject = async () => {
        setIsUploading(true);

        try {
            const newProject = await addProject({
                name: formData.name || 'Unbenanntes Projekt',
                icon: formData.icon,
                goal: formData.goal || undefined,
            });

            const projectId = newProject.id;

            // Upload files if any
            if (files.length > 0) {
                for (let i = 0; i < files.length; i++) {
                    const uploadedFile = files[i];
                    if (uploadedFile.status === 'success') continue;

                    setFiles(prev => prev.map((f, idx) =>
                        idx === i ? { ...f, status: 'uploading' } : f
                    ));

                    try {
                        const formDataUpload = new FormData();
                        formDataUpload.append('file', uploadedFile.file);
                        formDataUpload.append('projectId', projectId);

                        await post(API_CONFIG.ingest, { body: formDataUpload });

                        setFiles(prev => prev.map((f, idx) =>
                            idx === i ? { ...f, status: 'success' } : f
                        ));
                    } catch (error) {
                        setFiles(prev => prev.map((f, idx) =>
                            idx === i ? { ...f, status: 'error', error: 'Upload fehlgeschlagen' } : f
                        ));
                    }
                }
            }

            // Reset and close
            setStep(1);
            setFormData({ name: '', icon: '🚀', goal: '' });
            setFiles([]);
            onClose();
        } catch (error) {
            console.error('Failed to create project:', error);
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
            <div className="bg-white w-[600px] max-w-[95vw] min-h-[500px] rounded-3xl shadow-2xl relative flex flex-col overflow-hidden">
                <div className="p-8 flex-1 flex flex-col">
                    {/* Header */}
                    <div className="flex justify-between items-center mb-8 shrink-0">
                        <div className="flex gap-2">
                            {[1, 2, 3].map(s => (
                                <div
                                    key={s}
                                    className={`h-1.5 w-8 rounded-full transition-all ${step >= s ? 'bg-blue-600' : 'bg-gray-100'}`}
                                />
                            ))}
                        </div>
                        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                            <X size={20} />
                        </button>
                    </div>

                    {/* Step 1: Name & Icon */}
                    {step === 1 && (
                        <div className="space-y-6 flex-1">
                            <h3 className="text-2xl font-black">Neues Projekt starten</h3>
                            <p className="text-sm text-gray-500 leading-relaxed">Geben Sie Ihrem Change-Vorhaben einen Namen und wählen Sie ein passendes Icon aus.</p>
                            <div className="space-y-4">
                                <input
                                    autoFocus
                                    className="w-full bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm outline-none focus:ring-2 focus:ring-blue-500 transition-all font-bold"
                                    placeholder="z.B. Digitalisierung Vertrieb"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                />
                                <div className="flex gap-3">
                                    {['🚀', '🏢', '⚡', '💡', '🌱'].map(emoji => (
                                        <button
                                            key={emoji}
                                            onClick={() => setFormData({ ...formData, icon: emoji })}
                                            className={`w-12 h-12 text-xl rounded-xl flex items-center justify-center transition-all ${formData.icon === emoji ? 'bg-blue-600 shadow-lg scale-110 shadow-blue-200' : 'bg-gray-50 hover:bg-gray-100'}`}
                                            type="button"
                                        >
                                            {emoji}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Step 2: Goal Definition */}
                    {step === 2 && (
                        <div className="space-y-6 flex-1">
                            <h3 className="text-2xl font-black">Was ist Ihr Ziel?</h3>
                            <p className="text-sm text-gray-500">Beschreiben Sie, was Sie mit diesem Projekt erreichen möchten. Je klarer Ihr Ziel, desto besser kann ich Sie unterstützen.</p>
                            <textarea
                                autoFocus
                                className="w-full h-40 bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm outline-none focus:ring-2 focus:ring-blue-500 transition-all resize-none"
                                placeholder="z.B. Wir möchten die Mitarbeiterzufriedenheit während der Umstrukturierung verstehen und gezielte Maßnahmen zur Verbesserung der Akzeptanz entwickeln..."
                                value={formData.goal}
                                onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
                            />
                            <p className="text-xs text-gray-400">Tipp: Beschreiben Sie sowohl das gewünschte Ergebnis als auch den aktuellen Kontext.</p>
                        </div>
                    )}

                    {/* Step 3: Upload */}
                    {step === 3 && (
                        <div className="space-y-6 flex-1 flex flex-col">
                            <h3 className="text-2xl font-black">Daten-Input (Optional)</h3>
                            <p className="text-sm text-gray-500">Haben Sie bereits Dokumente? Laden Sie diese hoch, um erste Insights zu generieren.</p>

                            {/* Hidden file input */}
                            <input
                                ref={fileInputRef}
                                type="file"
                                multiple
                                className="hidden"
                                accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.xls"
                                onChange={(e) => handleFileSelect(e.target.files)}
                            />

                            {/* Drop zone */}
                            <div
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                onDrop={handleDrop}
                                onClick={() => fileInputRef.current?.click()}
                                className={`
                                    border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center
                                    cursor-pointer transition-all gap-3
                                    ${isDragging
                                        ? 'border-blue-500 bg-blue-50 text-blue-600'
                                        : 'border-gray-200 bg-gray-50 text-gray-400 hover:border-gray-300 hover:bg-gray-100'
                                    }
                                `}
                            >
                                <Upload size={36} className={isDragging ? 'text-blue-500' : ''} />
                                <span className="text-[10px] font-black uppercase tracking-widest">
                                    {isDragging ? 'Dateien hier ablegen' : 'Dateien hierher ziehen'}
                                </span>
                                <button
                                    className="bg-white text-blue-600 border border-blue-100 px-4 py-2 rounded-lg text-[10px] font-bold shadow-sm hover:bg-blue-50 transition-colors"
                                    type="button"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        fileInputRef.current?.click();
                                    }}
                                >
                                    Durchsuchen
                                </button>
                                <span className="text-[9px] text-gray-400">PDF, Word, Excel, CSV, TXT</span>
                            </div>

                            {/* File list */}
                            {files.length > 0 && (
                                <div className="flex-1 overflow-y-auto space-y-2 max-h-32">
                                    {files.map((uploadedFile, index) => (
                                        <div
                                            key={index}
                                            className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                                        >
                                            <FileText size={18} className="text-gray-400 shrink-0" />
                                            <span className="text-sm text-gray-700 truncate flex-1">
                                                {uploadedFile.file.name}
                                            </span>
                                            <span className="text-xs text-gray-400">
                                                {(uploadedFile.file.size / 1024).toFixed(0)} KB
                                            </span>
                                            {uploadedFile.status === 'uploading' && (
                                                <Loader2 size={16} className="text-blue-500 animate-spin" />
                                            )}
                                            {uploadedFile.status === 'success' && (
                                                <CheckCircle size={16} className="text-green-500" />
                                            )}
                                            {uploadedFile.status === 'pending' && (
                                                <button
                                                    onClick={() => removeFile(index)}
                                                    className="p-1 hover:bg-gray-200 rounded text-gray-400 hover:text-red-500 transition-colors"
                                                    type="button"
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            )}
                                            {uploadedFile.status === 'error' && (
                                                <span className="text-xs text-red-500">{uploadedFile.error}</span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Footer Navigation */}
                    <div className="mt-auto pt-8 flex justify-between items-center shrink-0">
                        <button
                            disabled={step === 1}
                            onClick={() => setStep(step - 1)}
                            className={`text-xs font-bold ${step === 1 ? 'text-gray-200' : 'text-gray-400 hover:text-gray-600'}`}
                            type="button"
                        >
                            Zurück
                        </button>
                        <Button
                            onClick={handleNext}
                            disabled={isUploading}
                            className="px-8 py-3 rounded-xl gap-2 shadow-lg shadow-blue-100 disabled:opacity-50"
                        >
                            {isUploading ? (
                                <>
                                    <Loader2 size={16} className="animate-spin" />
                                    Wird erstellt...
                                </>
                            ) : (
                                <>
                                    {step < 3 ? 'Weiter' : 'Projekt erstellen'} <ChevronRight size={16} />
                                </>
                            )}
                        </Button>
                    </div>

                </div>
            </div>
        </div>
    );
}
