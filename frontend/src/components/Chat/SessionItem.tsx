import { useState, useRef, useEffect } from 'react';
import { Pencil, Trash2 } from 'lucide-react';
import type { ChatSession } from '../../types/session';
import { ContextMenu, type ContextMenuItem } from '../common/ContextMenu';

interface SessionItemProps {
    session: ChatSession;
    isActive: boolean;
    onSelect: () => void;
    onDelete: () => void;
    onRename: (newTitle: string) => void;
}

export function SessionItem({ session, isActive, onSelect, onDelete, onRename }: SessionItemProps) {
    const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);
    const [isRenaming, setIsRenaming] = useState(false);
    const [renameValue, setRenameValue] = useState(session.title);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isRenaming && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [isRenaming]);

    const handleContextMenu = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setContextMenu({ x: e.clientX, y: e.clientY });
    };

    const handleRenameSubmit = () => {
        if (renameValue.trim() && renameValue !== session.title) {
            onRename(renameValue.trim());
        } else {
            setRenameValue(session.title);
        }
        setIsRenaming(false);
    };

    const handleRenameKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleRenameSubmit();
        } else if (e.key === 'Escape') {
            setRenameValue(session.title);
            setIsRenaming(false);
        }
    };

    const contextMenuItems: ContextMenuItem[] = [
        {
            label: 'Umbenennen',
            icon: <Pencil size={14} />,
            onClick: () => {
                setRenameValue(session.title);
                setIsRenaming(true);
            }
        },
        {
            label: 'Löschen',
            icon: <Trash2 size={14} />,
            onClick: onDelete,
            danger: true
        }
    ];

    return (
        <>
            <div
                onClick={onSelect}
                onContextMenu={handleContextMenu}
                className={`
                    group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer
                    transition-colors duration-150
                    ${isActive
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'hover:bg-gray-100 text-gray-700'
                    }
                `}
            >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                    <span className="text-sm">💬</span>
                    {isRenaming ? (
                        <input
                            ref={inputRef}
                            type="text"
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            onBlur={handleRenameSubmit}
                            onKeyDown={handleRenameKeyDown}
                            onClick={(e) => e.stopPropagation()}
                            className="text-sm bg-white border border-blue-300 rounded px-1 py-0.5 outline-none focus:ring-1 focus:ring-blue-500 w-full"
                        />
                    ) : (
                        <span className="text-sm truncate">{session.title}</span>
                    )}
                </div>

                {!isRenaming && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onDelete();
                        }}
                        className={`
                            p-1 rounded opacity-0 group-hover:opacity-100
                            hover:bg-red-100 text-gray-400 hover:text-red-500
                            transition-all duration-150
                        `}
                        title="Löschen"
                    >
                        <Trash2 size={14} />
                    </button>
                )}
            </div>

            {contextMenu && (
                <ContextMenu
                    x={contextMenu.x}
                    y={contextMenu.y}
                    items={contextMenuItems}
                    onClose={() => setContextMenu(null)}
                />
            )}
        </>
    );
}
