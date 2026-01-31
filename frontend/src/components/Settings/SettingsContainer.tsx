import { useState, useRef, useCallback, useEffect } from 'react';
import { Save, Upload, FileText, Trash2, Loader2, CheckCircle, Settings, AlertCircle } from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { listDocuments, uploadDocument, deleteDocument, type DocumentData } from '../../services/api';

interface UploadedFile {
    file: File;
    status: 'pending' | 'uploading' | 'success' | 'error';
    error?: string;
}

interface SettingsContainerProps {
    projectId: string;
}

const EMOJI_OPTIONS = ['🚀', '🏢', '⚡', '💡', '🌱', '🎯', '📊', '🔧', '💼', '🌍', '🤖', '📦'];

function formatFileSize(bytes: number | null): string {
    if (!bytes) return '0 KB';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

export function SettingsContainer({ projectId }: SettingsContainerProps) {
    const { selectedProject, refreshProjects } = useProjects();
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState({
        name: selectedProject?.name || '',
        icon: selectedProject?.icon || '🚀',
        goal: selectedProject?.goal || ''
    });
    const [isSaving, setIsSaving] = useState(false);

    // Document states
    const [documents, setDocuments] = useState<DocumentData[]>([]);
    const [isLoadingDocs, setIsLoadingDocs] = useState(true);
    const [docsError, setDocsError] = useState<string | null>(null);

    // Upload states
    const [files, setFiles] = useState<UploadedFile[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Sync form when project changes
    useEffect(() => {
        if (selectedProject) {
            setEditForm({
                name: selectedProject.name,
                icon: selectedProject.icon,
                goal: selectedProject.goal || ''
            });
        }
    }, [selectedProject]);

    // Load documents when project changes
    useEffect(() => {
        if (selectedProject) {
            loadDocuments();
        }
    }, [selectedProject?.id]);

    const loadDocuments = async () => {
        if (!selectedProject) return;

        setIsLoadingDocs(true);
        setDocsError(null);

        try {
            const docs = await listDocuments(selectedProject.id);
            setDocuments(docs);
        } catch (err) {
            console.error('Failed to load documents:', err);
            setDocsError('Dokumente konnten nicht geladen werden');
        } finally {
            setIsLoadingDocs(false);
        }
    };

    const handleSave = async () => {
        if (!selectedProject) return;

        setIsSaving(true);
        try {
            const response = await fetch(`/api/projects/${selectedProject.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(editForm)
            });

            if (!response.ok) throw new Error('Failed to save');

            await refreshProjects();
            setIsEditing(false);
        } catch (err) {
            console.error('Failed to save project:', err);
        } finally {
            setIsSaving(false);
        }
    };

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

    const uploadFiles = async () => {
        if (!selectedProject || files.length === 0) return;

        setIsUploading(true);

        for (let i = 0; i < files.length; i++) {
            const uploadedFile = files[i];
            if (uploadedFile.status === 'success') continue;

            setFiles(prev => prev.map((f, idx) =>
                idx === i ? { ...f, status: 'uploading' } : f
            ));

            try {
                await uploadDocument(selectedProject.id, uploadedFile.file);

                setFiles(prev => prev.map((f, idx) =>
                    idx === i ? { ...f, status: 'success' } : f
                ));
            } catch (error) {
                setFiles(prev => prev.map((f, idx) =>
                    idx === i ? { ...f, status: 'error', error: 'Upload fehlgeschlagen' } : f
                ));
            }
        }

        setIsUploading(false);

        // Refresh document list
        await loadDocuments();

        // Clear successful uploads
        setFiles(prev => prev.filter(f => f.status !== 'success'));
    };

    const handleDeleteDocument = async (docId: string) => {
        try {
            await deleteDocument(docId);
            setDocuments(prev => prev.filter(d => d.id !== docId));
        } catch (err) {
            console.error('Failed to delete document:', err);
        }
    };

    const clearCompletedFiles = () => {
        setFiles(prev => prev.filter(f => f.status !== 'success'));
    };

    if (!selectedProject) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <p className="text-gray-400">Kein Projekt ausgewaehlt</p>
            </div>
        );
    }

    return (
        <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-3xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex items-center gap-3">
                    <Settings className="text-gray-400" size={24} />
                    <h1 className="text-2xl font-bold text-gray-800">Einstellungen</h1>
                </div>

                {/* Project Info Card */}
                <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-gray-700">Projektdetails</h2>
                        {!isEditing ? (
                            <button
                                onClick={() => setIsEditing(true)}
                                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                            >
                                Bearbeiten
                            </button>
                        ) : (
                            <div className="flex gap-2">
                                <button
                                    onClick={() => {
                                        setIsEditing(false);
                                        setEditForm({
                                            name: selectedProject.name,
                                            icon: selectedProject.icon,
                                            goal: selectedProject.goal || ''
                                        });
                                    }}
                                    className="text-sm text-gray-500 hover:text-gray-700 font-medium"
                                >
                                    Abbrechen
                                </button>
                                <button
                                    onClick={handleSave}
                                    disabled={isSaving}
                                    className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50"
                                >
                                    {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                                    Speichern
                                </button>
                            </div>
                        )}
                    </div>

                    {isEditing ? (
                        <div className="space-y-4">
                            {/* Name */}
                            <div>
                                <label className="block text-sm font-medium text-gray-600 mb-1">
                                    Projektname
                                </label>
                                <input
                                    type="text"
                                    value={editForm.name}
                                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                                    className="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            {/* Icon */}
                            <div>
                                <label className="block text-sm font-medium text-gray-600 mb-2">
                                    Icon
                                </label>
                                <div className="flex flex-wrap gap-2">
                                    {EMOJI_OPTIONS.map(emoji => (
                                        <button
                                            key={emoji}
                                            onClick={() => setEditForm({ ...editForm, icon: emoji })}
                                            className={`w-10 h-10 text-lg rounded-lg flex items-center justify-center transition-all ${editForm.icon === emoji
                                                ? 'bg-blue-600 shadow-lg scale-110'
                                                : 'bg-gray-100 hover:bg-gray-200'
                                                }`}
                                        >
                                            {emoji}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Goal */}
                            <div>
                                <label className="block text-sm font-medium text-gray-600 mb-1">
                                    Projektziel
                                </label>
                                <textarea
                                    value={editForm.goal}
                                    onChange={(e) => setEditForm({ ...editForm, goal: e.target.value })}
                                    rows={4}
                                    className="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                                    placeholder="Beschreiben Sie das Ziel Ihres Projekts..."
                                />
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="flex items-center gap-4">
                                <span className="text-4xl">{selectedProject.icon}</span>
                                <div>
                                    <h3 className="text-xl font-bold text-gray-800">{selectedProject.name}</h3>
                                    <p className="text-sm text-gray-500">Projekt-ID: {selectedProject.id.slice(0, 8)}...</p>
                                </div>
                            </div>
                            {selectedProject.goal && (
                                <div className="bg-gray-50 rounded-xl p-4">
                                    <p className="text-sm text-gray-600 font-medium mb-1">Projektziel:</p>
                                    <p className="text-sm text-gray-700">{selectedProject.goal}</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Existing Documents Card */}
                <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-gray-700">Hochgeladene Dokumente</h2>
                        <span className="text-sm text-gray-500">{documents.length} Dokument{documents.length !== 1 ? 'e' : ''}</span>
                    </div>

                    {isLoadingDocs ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 size={24} className="text-gray-400 animate-spin" />
                        </div>
                    ) : docsError ? (
                        <div className="flex items-center justify-center gap-2 py-8 text-gray-500">
                            <AlertCircle size={18} />
                            <span className="text-sm">{docsError}</span>
                        </div>
                    ) : documents.length === 0 ? (
                        <div className="text-center py-8 text-gray-400">
                            <FileText size={32} className="mx-auto mb-2 opacity-50" />
                            <p className="text-sm">Noch keine Dokumente hochgeladen</p>
                        </div>
                    ) : (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                            {documents.map((doc) => (
                                <div
                                    key={doc.id}
                                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg group"
                                >
                                    <FileText size={18} className="text-blue-500 shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-gray-700 truncate">{doc.filename}</p>
                                        <p className="text-xs text-gray-400">
                                            {formatFileSize(doc.file_size)} • {formatDate(doc.created_at)}
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => handleDeleteDocument(doc.id)}
                                        className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-100 text-gray-400 hover:text-red-500 transition-all"
                                        title="Loeschen"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* File Upload Card */}
                <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
                    <h2 className="text-lg font-semibold text-gray-700">Neue Dokumente hochladen</h2>
                    <p className="text-sm text-gray-500">
                        Laden Sie Dokumente hoch, um die Wissensdatenbank zu erweitern.
                    </p>

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
                            border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center
                            cursor-pointer transition-all gap-3
                            ${isDragging
                                ? 'border-blue-500 bg-blue-50 text-blue-600'
                                : 'border-gray-200 bg-gray-50 text-gray-400 hover:border-gray-300 hover:bg-gray-100'
                            }
                        `}
                    >
                        <Upload size={32} className={isDragging ? 'text-blue-500' : ''} />
                        <span className="text-sm font-medium">
                            {isDragging ? 'Dateien hier ablegen' : 'Dateien hierher ziehen oder klicken'}
                        </span>
                        <span className="text-xs text-gray-400">PDF, Word, Excel, CSV, TXT</span>
                    </div>

                    {/* Pending file list */}
                    {files.length > 0 && (
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-600">
                                    {files.length} Datei{files.length !== 1 ? 'en' : ''} ausgewaehlt
                                </span>
                                {files.some(f => f.status === 'success') && (
                                    <button
                                        onClick={clearCompletedFiles}
                                        className="text-xs text-gray-500 hover:text-gray-700"
                                    >
                                        Fertige entfernen
                                    </button>
                                )}
                            </div>

                            <div className="space-y-2 max-h-48 overflow-y-auto">
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
                                            {formatFileSize(uploadedFile.file.size)}
                                        </span>
                                        {uploadedFile.status === 'uploading' && (
                                            <Loader2 size={16} className="text-blue-500 animate-spin" />
                                        )}
                                        {uploadedFile.status === 'success' && (
                                            <CheckCircle size={16} className="text-green-500" />
                                        )}
                                        {uploadedFile.status === 'pending' && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    removeFile(index);
                                                }}
                                                className="p-1 hover:bg-gray-200 rounded text-gray-400 hover:text-red-500 transition-colors"
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

                            {files.some(f => f.status === 'pending') && (
                                <button
                                    onClick={uploadFiles}
                                    disabled={isUploading}
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50"
                                >
                                    {isUploading ? (
                                        <>
                                            <Loader2 size={16} className="animate-spin" />
                                            Wird hochgeladen...
                                        </>
                                    ) : (
                                        <>
                                            <Upload size={16} />
                                            Hochladen
                                        </>
                                    )}
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
