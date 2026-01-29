import { useState } from 'react';
import { History, Clock, Loader2, Play, Trash2 } from 'lucide-react';
import { Toast } from './Toast';
import { API_ENDPOINTS } from '../config/api';

interface Session {
    id: number;
    name: string;
    depot_type: string;
    status: string;
    computed_status?: string;
    inventory_number?: string;
    site?: string;
    created_at: string;
}

interface SessionHistoryProps {
    onResume: (sessionId: number) => void;
}

export function SessionHistory({ onResume }: SessionHistoryProps) {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isOpen, setIsOpen] = useState(false);
    const [deletingId, setDeletingId] = useState<number | null>(null);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [sessionToDelete, setSessionToDelete] = useState<Session | null>(null);
    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState('');

    const fetchSessions = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.activeSessions);
            if (response.ok) {
                const data = await response.json();
                setSessions(data);
            }
        } catch (error) {
            console.error("Failed to fetch sessions", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteClick = (session: Session, e: React.MouseEvent) => {
        e.stopPropagation();
        setSessionToDelete(session);
        setShowDeleteModal(true);
    };

    const confirmDelete = async () => {
        if (!sessionToDelete) return;

        setDeletingId(sessionToDelete.id);
        try {
            const response = await fetch(API_ENDPOINTS.deleteSession(sessionToDelete.id), {
                method: 'DELETE'
            });

            if (response.ok) {
                setSessions(prev => prev.filter(s => s.id !== sessionToDelete.id));
                // Show success toast
                setToastMessage(`Session "${sessionToDelete.name}" supprimée avec succès`);
                setShowToast(true);
            }
        } catch (error) {
            console.error("Failed to delete session", error);
        } finally {
            setDeletingId(null);
            setShowDeleteModal(false);
            setSessionToDelete(null);
        }
    };

    const cancelDelete = () => {
        setShowDeleteModal(false);
        setSessionToDelete(null);
    };

    const toggleOpen = () => {
        if (!isOpen) {
            fetchSessions();
        }
        setIsOpen(!isOpen);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('fr-FR', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    };

    const getStatusConfig = (status: string, computed?: string) => {
        if (status === 'ARCHIVE') return { label: 'Archivé', color: 'bg-slate-100 text-slate-500 border-slate-200' };
        if (computed === 'COMPLETED') return { label: 'Terminé', color: 'bg-emerald-50 text-emerald-700 border-emerald-100' };
        if (computed === 'TEMPLATE_READY') return { label: 'Saisie en cours', color: 'bg-blue-50 text-blue-700 border-blue-100' };
        if (computed === 'MASK_IMPORTED') return { label: 'Masque Importé', color: 'bg-indigo-50 text-indigo-700 border-indigo-100' };
        return { label: 'En cours', color: 'bg-slate-50 text-slate-600 border-slate-200' };
    };

    return (
        <div className="relative z-50">
            {/* Toggle Button */}
            <button
                onClick={toggleOpen}
                className={`
                    flex items-center gap-2 px-4 py-2 font-medium rounded-lg transition-all
                    ${isOpen
                        ? 'bg-brand-50 text-brand-700 ring-2 ring-brand-200'
                        : 'bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-900 border border-slate-200 shadow-sm'
                    }
                `}
            >
                <History size={18} />
                <span>Historique</span>
            </button>

            {/* Dropdown / Modal */}
            {isOpen && (
                <div className="absolute top-12 right-0 w-96 bg-white rounded-xl shadow-xl border border-slate-100 z-50 animate-in fade-in slide-in-from-top-2 overflow-hidden">
                    <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
                        <h3 className="font-semibold text-slate-800">Sessions Récentes</h3>
                        <span className="text-xs font-medium bg-slate-200 text-slate-600 px-2 py-0.5 rounded-full">
                            {sessions.length}
                        </span>
                    </div>

                    <div className="max-h-96 overflow-y-auto">
                        {isLoading ? (
                            <div className="p-8 flex justify-center text-slate-400">
                                <Loader2 className="animate-spin" />
                            </div>
                        ) : sessions.length === 0 ? (
                            <div className="p-8 text-center text-slate-500">
                                <p className="text-sm">Aucune session active trouvée.</p>
                            </div>
                        ) : (
                            <ul className="divide-y divide-slate-50">
                                {sessions.map((session) => (
                                    <li key={session.id} className="p-4 hover:bg-slate-50 transition-colors group">
                                        <div className="flex items-start justify-between mb-2">
                                            <div>
                                                <div className="font-medium text-slate-900 group-hover:text-brand-700 transition-colors truncate max-w-[200px]" title={session.name}>
                                                    {session.inventory_number ? (
                                                        <span className="flex flex-col">
                                                            <span className="font-bold text-sm text-slate-800">{session.inventory_number}</span>
                                                            <span className="text-xs font-normal text-slate-500">{session.site}</span>
                                                        </span>
                                                    ) : (
                                                        session.name
                                                    )}
                                                </div>
                                                <div className="text-xs text-slate-400 flex items-center gap-1 mt-1">
                                                    <Clock size={12} />
                                                    {formatDate(session.created_at)}
                                                </div>
                                            </div>
                                            <div className="flex gap-2">
                                                {(() => {
                                                    const config = getStatusConfig(session.status, session.computed_status);
                                                    return (
                                                        <span className={`text-[10px] px-2 py-0.5 rounded border ${config.color}`}>
                                                            {config.label}
                                                        </span>
                                                    );
                                                })()}
                                                <button
                                                    onClick={(e) => handleDeleteClick(session, e)}
                                                    disabled={deletingId === session.id}
                                                    className="text-slate-400 hover:text-red-500 transition-colors p-1 rounded-md hover:bg-red-50 disabled:opacity-50"
                                                    title="Supprimer la session"
                                                >
                                                    {deletingId === session.id ? (
                                                        <Loader2 size={14} className="animate-spin" />
                                                    ) : (
                                                        <Trash2 size={14} />
                                                    )}
                                                </button>
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between mt-3">
                                            <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">
                                                {session.depot_type}
                                            </span>

                                            <button
                                                onClick={() => {
                                                    onResume(session.id);
                                                    setIsOpen(false);
                                                }}
                                                className="text-xs font-semibold bg-brand-600 text-white px-3 py-1.5 rounded-lg hover:bg-brand-700 flex items-center gap-1.5 transition-colors shadow-sm shadow-brand-600/20"
                                            >
                                                Reprendre
                                                <Play size={10} fill="currentColor" />
                                            </button>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>

                    {/* Backgroud Click to Close Overlay (Invisible) */}
                    <div
                        className="fixed inset-0 z-[-1] cursor-default"
                        onClick={() => setIsOpen(false)}
                        aria-hidden="true"
                    />
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {showDeleteModal && sessionToDelete && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                        onClick={cancelDelete}
                    />

                    {/* Modal */}
                    <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 transform transition-all">
                        <div className="flex items-start gap-4">
                            <div className="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                                <Trash2 className="w-6 h-6 text-red-600" />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-lg font-semibold text-slate-900 mb-1">
                                    Supprimer la session ?
                                </h3>
                                <p className="text-sm text-slate-600 mb-4">
                                    Êtes-vous sûr de vouloir archiver la session <span className="font-semibold">{sessionToDelete.name}</span> ?
                                    {sessionToDelete.inventory_number && (
                                        <span className="block mt-1 text-xs text-slate-500">
                                            Inventaire : {sessionToDelete.inventory_number}
                                        </span>
                                    )}
                                </p>
                                <div className="flex gap-3 justify-end">
                                    <button
                                        onClick={cancelDelete}
                                        className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors"
                                    >
                                        Annuler
                                    </button>
                                    <button
                                        onClick={confirmDelete}
                                        disabled={deletingId === sessionToDelete.id}
                                        className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                    >
                                        {deletingId === sessionToDelete.id ? (
                                            <>
                                                <Loader2 size={16} className="animate-spin" />
                                                Suppression...
                                            </>
                                        ) : (
                                            'Supprimer'
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Success Toast */}
            {showToast && (
                <Toast
                    message={toastMessage}
                    onClose={() => setShowToast(false)}
                />
            )}
        </div>
    );
}
