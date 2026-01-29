import { useState, useRef, useEffect } from 'react';
import { Download, Upload, BarChart3, Package, Tag, ArrowRight, CheckCircle, Loader2, AlertTriangle } from 'lucide-react';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';

interface StepSummaryProps {
    sessionId: number;
    stats: {
        total_lines: number;
        total_products: number;
        total_lots: number;
    };
    onSuccess: () => void;
}

export function StepSummary({ sessionId, stats, onSuccess }: StepSummaryProps) {
    const [templateUploaded, setTemplateUploaded] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const isMounted = useRef(true);

    useEffect(() => {
        return () => {
            isMounted.current = false;
        };
    }, []);

    const downloadTemplate = async () => {
        try {
            const response = await axios.get(
                API_ENDPOINTS.downloadTemplate(sessionId),
                { responseType: 'blob' }
            );

            // Extract filename from header
            const contentDisposition = response.headers['content-disposition'];
            let filename = `template_inventaire_${sessionId}.xlsx`; // Fallback
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                if (filenameMatch && filenameMatch.length === 2) {
                    filename = filenameMatch[1];
                }
            }

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Download error:', err);
            setError("Erreur lors du téléchargement du template");
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            await uploadTemplate(e.dataTransfer.files[0]);
        }
    };

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            await uploadTemplate(e.target.files[0]);
        }
    };

    const uploadTemplate = async (file: File) => {
        if (!file.name.toLowerCase().endsWith('.xlsx')) {
            setError("Seuls les fichiers Excel (.xlsx) sont acceptés");
            return;
        }

        setIsUploading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post(
                API_ENDPOINTS.uploadFilledTemplate(sessionId),
                formData
            );

            if (isMounted.current) {
                if (response.data.status === 'success') {
                    setTemplateUploaded(true);
                } else {
                    setError(response.data.message || "Erreur lors de l'upload");
                }
            }
        } catch (err: any) {
            console.error('Upload error:', err);
            if (isMounted.current) {
                if (err.response && err.response.data && err.response.data.detail) {
                    setError(err.response.data.detail);
                } else {
                    setError("Erreur lors de l'upload du template");
                }
            }
        } finally {
            if (isMounted.current) {
                setIsUploading(false);
            }
        }
    };

    return (
        <div className="max-w-4xl mx-auto py-8">
            <div className="text-center mb-10">
                <div className="inline-flex items-center justify-center p-3 bg-emerald-50 rounded-full mb-4">
                    <CheckCircle className="w-8 h-8 text-emerald-600" />
                </div>
                <h2 className="text-3xl font-bold text-slate-900 mb-2">Analyse terminée avec succès</h2>
                <p className="text-slate-600 max-w-lg mx-auto">
                    Le masque a été traité. suivez les étapes ci-dessous pour compléter l'inventaire via le template Excel.
                </p>
            </div>

            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <BarChart3 className="w-24 h-24 text-brand-600" />
                    </div>
                    <div className="relative z-10">
                        <div className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-1">Lignes Totales</div>
                        <div className="text-4xl font-bold text-brand-700">{stats.total_lines.toLocaleString()}</div>
                    </div>
                </div>

                <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Package className="w-24 h-24 text-blue-600" />
                    </div>
                    <div className="relative z-10">
                        <div className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-1">Produits Uniques</div>
                        <div className="text-4xl font-bold text-blue-700">{stats.total_products.toLocaleString()}</div>
                    </div>
                </div>

                <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Tag className="w-24 h-24 text-purple-600" />
                    </div>
                    <div className="relative z-10">
                        <div className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-1">Lots Identifiés</div>
                        <div className="text-4xl font-bold text-purple-700">{stats.total_lots.toLocaleString()}</div>
                    </div>
                </div>
            </div>

            <div className="grid md:grid-cols-2 gap-8 items-start">
                {/* Step 1: Download */}
                <div className="bg-slate-50 rounded-2xl p-8 border border-slate-200 h-full flex flex-col">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-10 h-10 rounded-full bg-white border border-slate-200 flex items-center justify-center font-bold text-slate-700 shadow-sm">1</div>
                        <h3 className="text-xl font-semibold text-slate-800">Télécharger le Template</h3>
                    </div>
                    <p className="text-slate-600 mb-8 flex-grow">
                        Récupérez le fichier Excel pré-rempli avec les données théoriques. La colonne <code className="bg-white px-2 py-1 rounded border border-slate-200 text-sm font-mono text-brand-700">QUANTITE_REELLE</code> est à compléter.
                    </p>
                    <button
                        onClick={downloadTemplate}
                        className="w-full bg-white text-slate-700 border-2 border-slate-200 px-6 py-4 rounded-xl font-semibold hover:border-brand-600 hover:text-brand-700 flex items-center justify-center gap-3 transition-all group"
                    >
                        <Download size={20} className="text-slate-400 group-hover:text-brand-600" />
                        Obtenir le fichier Excel
                    </button>
                </div>

                {/* Step 2: Upload */}
                <div className="bg-slate-50 rounded-2xl p-8 border border-slate-200 h-full flex flex-col">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-10 h-10 rounded-full bg-white border border-slate-200 flex items-center justify-center font-bold text-slate-700 shadow-sm">2</div>
                        <h3 className="text-xl font-semibold text-slate-800">Renvoyer le Fichier</h3>
                    </div>

                    <div
                        className={`
                            flex-grow border-3 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 relative
                            ${isDragging
                                ? 'border-brand-500 bg-brand-50 scale-[1.02]'
                                : 'border-slate-300 hover:border-brand-400 hover:bg-white bg-slate-100/50'
                            }
                            ${templateUploaded ? 'bg-emerald-50 border-emerald-300 ring-4 ring-emerald-50/50' : ''}
                        `}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        onClick={!templateUploaded ? () => document.getElementById('template-upload')?.click() : undefined}
                    >
                        <input
                            id="template-upload"
                            type="file"
                            className="hidden"
                            accept=".xlsx"
                            onChange={handleFileSelect}
                            disabled={templateUploaded || isUploading}
                        />

                        {isUploading ? (
                            <div className="flex flex-col items-center justify-center h-full py-6">
                                <Loader2 className="animate-spin text-brand-600 mb-4" size={40} />
                                <span className="font-medium text-slate-700">Traitement en cours...</span>
                                <span className="text-sm text-slate-500 mt-1">Génération du fichier final</span>
                            </div>
                        ) : templateUploaded ? (
                            <div className="flex flex-col items-center justify-center h-full py-6 animate-in fade-in zoom-in duration-300">
                                <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-4 shadow-sm">
                                    <CheckCircle size={32} />
                                </div>
                                <h3 className="text-lg font-bold text-emerald-800">Fichier Validé !</h3>
                                <p className="text-emerald-600/80 text-sm mt-1">Prêt pour l'étape suivante</p>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full py-6">
                                <div className={`w-14 h-14 rounded-full flex items-center justify-center mb-4 transition-colors ${isDragging ? 'bg-brand-100 text-brand-600' : 'bg-white text-slate-400 shadow-sm'}`}>
                                    <Upload size={28} />
                                </div>
                                <h3 className="font-semibold text-slate-700">
                                    {isDragging ? 'Lâchez le fichier ici' : 'Glissez le fichier rempli'}
                                </h3>
                                <p className="text-slate-500 text-sm mt-2">ou cliquez pour parcourir</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {error && (
                <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 flex items-start gap-3 animate-in fade-in slide-in-from-top-2">
                    <AlertTriangle className="shrink-0 mt-0.5" size={20} />
                    <div>
                        <div className="font-bold">Erreur détectée</div>
                        <div className="text-sm mt-1 opacity-90">{error}</div>
                    </div>
                </div>
            )}

            {/* Continue Button */}
            <div className={`mt-10 flex justify-center transition-all duration-500 ${templateUploaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'}`}>
                <button
                    onClick={onSuccess}
                    disabled={!templateUploaded}
                    className="group bg-brand-600 text-white px-10 py-4 rounded-full font-bold text-lg hover:bg-brand-700 hover:shadow-lg hover:shadow-brand-600/20 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3 transition-all"
                >
                    Voir le Résultat Final
                    <ArrowRight size={22} className="group-hover:translate-x-1 transition-transform" />
                </button>
            </div>
        </div>
    );
}
