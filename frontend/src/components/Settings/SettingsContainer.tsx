import { useState, useRef, useCallback, useEffect } from 'react';
import { Save, Upload, FileText, Trash2, Loader2, CheckCircle, Settings, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useProjects } from '../../context/ProjectContext';
import { useRefresh, useRefreshSignal } from '../../context/RefreshContext';
import { listDocuments, uploadDocument, deleteDocument, type DocumentData } from '../../services/api';
import { formatDateTime } from '../../utils/formatting';

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


export function SettingsContainer({ projectId: _projectId }: SettingsContainerProps) {
    const { selectedProject, refreshProjects } = useProjects();
    const { triggerRefresh } = useRefresh();
    const documentsRefreshSignal = useRefreshSignal('documents');
    const { t } = useTranslation(['settings', 'common']);
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

    // Load documents when project changes or refresh signal triggered
    useEffect(() => {
        if (selectedProject) {
            loadDocuments();
        }
    }, [selectedProject?.id, documentsRefreshSignal]);

    const loadDocuments = async () => {
        if (!selectedProject) return;

        setIsLoadingDocs(true);
        setDocsError(null);

        try {
            const docs = await listDocuments(selectedProject.id);
            setDocuments(docs);
        } catch (err) {
            console.error('Failed to load documents:', err);
            setDocsError(t('settings:documents.loadFailed'));
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
                    idx === i ? { ...f, status: 'error', error: t('common:errors.uploadFailed') } : f
                ));
            }
        }

        setIsUploading(false);

        // Refresh document list
        await loadDocuments();

        // Trigger refresh for other components that might use documents
        triggerRefresh('documents');

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
                <p className="text-gray-400">{t('common:noProjectSelected')}</p>
            </div>
        );
    }

    return (
        <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-3xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex items-center gap-3">
                    <Settings className="text-gray-400" size={24} />
                    <h1 className="text-2xl font-bold text-gray-800">{t('settings:title')}</h1>
                </div>

                {/* Project Info Card */}
                <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-gray-700">{t('settings:projectDetails')}</h2>
                        {!isEditing ? (
                            <button
                                onClick={() => setIsEditing(true)}
                                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                            >
                                {t('common:buttons.edit')}
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
                                    {t('common:buttons.cancel')}
                                </button>
                                <button
                                    onClick={handleSave}
                                    disabled={isSaving}
                                    className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50"
                                >
                                    {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                                    {t('common:buttons.save')}
                                </button>
                            </div>
                        )}
                    </div>

                    {isEditing ? (
                        <div className="space-y-4">
                            {/* Name */}
                            <div>
                                <label className="block text-sm font-medium text-gray-600 mb-1">
                                    {t('settings:projectName')}
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
                                    {t('settings:icon')}
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
                                    {t('settings:projectGoal')}
                                </label>
                                <textarea
                                    value={editForm.goal}
                                    onChange={(e) => setEditForm({ ...editForm, goal: e.target.value })}
                                    rows={4}
                                    className="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                                    placeholder={t('settings:goalPlaceholder')}
                                />
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="flex items-center gap-4">
                                <span className="text-4xl">{selectedProject.icon}</span>
                                <div>
                                    <h3 className="text-xl font-bold text-gray-800">{selectedProject.name}</h3>
                                    <p className="text-sm text-gray-500">{t('settings:projectId')} {selectedProject.id.slice(0, 8)}...</p>
                                </div>
                            </div>
                            {selectedProject.goal && (
                                <div className="bg-gray-50 rounded-xl p-4">
                                    <p className="text-sm text-gray-600 font-medium mb-1">{t('settings:projectGoal')}:</p>
                                    <p className="text-sm text-gray-700">{selectedProject.goal}</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Existing Documents Card */}
                <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-gray-700">{t('settings:documents.title')}</h2>
                        <span className="text-sm text-gray-500">{documents.length !== 1 ? t('settings:documents.countPlural', { count: documents.length }) : t('settings:documents.count', { count: documents.length })}</span>
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
                            <p className="text-sm">{t('settings:documents.empty')}</p>
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
                                            {formatFileSize(doc.file_size)} • {formatDateTime(doc.created_at)}
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
                    <h2 className="text-lg font-semibold text-gray-700">{t('settings:upload.title')}</h2>
                    <p className="text-sm text-gray-500">
                        {t('settings:upload.description')}
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
                            {isDragging ? t('common:dropFiles') : t('common:dragFilesOrClick')}
                        </span>
                        <span className="text-xs text-gray-400">{t('common:fileTypes')}</span>
                    </div>

                    {/* Pending file list */}
                    {files.length > 0 && (
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-600">
                                    {t('common:filesSelected', { count: files.length })}
                                </span>
                                {files.some(f => f.status === 'success') && (
                                    <button
                                        onClick={clearCompletedFiles}
                                        className="text-xs text-gray-500 hover:text-gray-700"
                                    >
                                        {t('common:removeCompleted')}
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
                                            {t('common:buttons.uploading')}
                                        </>
                                    ) : (
                                        <>
                                            <Upload size={16} />
                                            {t('common:buttons.upload')}
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
