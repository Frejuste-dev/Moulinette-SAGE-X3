
import { useState, useRef, useEffect } from 'react';
import { UploadCloud, FileType, AlertTriangle, ArrowRight, Loader2 } from 'lucide-react';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';

interface Stats {
    total_lines: number;
    total_products: number;
    total_lots: number;
}

interface StepUploadProps {
    depotType: string;
    onSuccess: (sessionId: number, stats: Stats) => void;
}

export function StepUpload({ depotType, onSuccess }: StepUploadProps) {
    const [file, setFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            validateAndSetFile(e.dataTransfer.files[0]);
        }
    };

    const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            validateAndSetFile(e.target.files[0]);
        }
    };

    const validateAndSetFile = (f: File) => {
        setError(null);
        if (!f.name.toLowerCase().endsWith('.csv')) {
            setError("Seuls les fichiers CSV sont acceptés.");
            setFile(null);
            return;
        }
        setFile(f);
    };

    const isMounted = useRef(true);

    useEffect(() => {
        return () => { isMounted.current = false; };
    }, []);

    const handleAnalysis = async () => {
        if (!file) return;
        setIsLoading(true);
        setError(null);

        const formData = new FormData();
        const sessionName = `INV_${new Date().toISOString().slice(0, 10)}`;
        formData.append('name', sessionName);
        formData.append('depot_type', depotType);
        formData.append('file', file);

        try {
            const response = await axios.post(API_ENDPOINTS.uploadMask, formData);
            if (response.data.status === 'success') {
                if (isMounted.current) {
                    // New API returns sessionID directly (not nested in data)
                    onSuccess(response.data.sessionID, response.data.stats);
                    // Do NOT set isLoading(false) here, as component will unmount
                }
            } else {
                if (isMounted.current) {
                    setError(response.data.message || "Erreur inconnue");
                    setIsLoading(false);
                }
            }
        } catch (err: any) {
            console.error("Upload Error Details:", err);
            if (isMounted.current) {
                if (err.response && err.response.data && err.response.data.detail) {
                    setError(err.response.data.detail);
                } else if (err.message) {
                    setError(err.message);
                } else {
                    setError("Impossible de contacter le serveur.");
                }
                setIsLoading(false);
            }
        }
    };


    return (
        <div className="max-w-2xl mx-auto py-6">
            <h2 className="text-2xl font-bold text-center mb-2">Import du masque Sage X3</h2>
            <p className="text-center text-slate-500 mb-8">
                Dépôt cible : <span className="font-semibold text-brand-600">{depotType}</span>
            </p>

            {/* Dropzone */}
            <div
                className={`
          border-3 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
          ${isDragging ? 'border-brand-500 bg-brand-50' : 'border-slate-200 hover:border-brand-400 hover:bg-slate-50'}
          ${file ? 'bg-brand-50/50 border-brand-200' : ''}
        `}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept=".csv"
                    onChange={handleSelect}
                />

                {!file ? (
                    <div className="flex flex-col items-center">
                        <div className="w-16 h-16 bg-brand-100 text-brand-600 rounded-full flex items-center justify-center mb-4">
                            <UploadCloud size={32} />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-700">Glissez votre fichier ici</h3>
                        <p className="text-slate-500 mt-2">ou cliquez pour parcourir</p>
                        <p className="text-xs text-slate-400 mt-4">Format supporté : CSV uniquement</p>
                    </div>
                ) : (
                    <div className="flex items-center justify-center gap-4">
                        <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center">
                            <FileType size={24} />
                        </div>
                        <div className="text-left">
                            <div className="font-medium text-slate-900">{file.name}</div>
                            <div className="text-sm text-slate-500">{(file.size / 1024).toFixed(1)} KB</div>
                        </div>
                        <button
                            onClick={(e) => { e.stopPropagation(); setFile(null); setError(null); }}
                            className="ml-4 text-sm text-red-500 hover:underline"
                        >
                            Changer
                        </button>
                    </div>
                )}
            </div>

            {error && (
                <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3 text-red-700">
                    <AlertTriangle className="shrink-0 mt-0.5" size={18} />
                    <div>
                        <div className="font-semibold">Erreur de validation</div>
                        <div className="text-sm mt-1">{error}</div>
                    </div>
                </div>
            )}

            <div className="mt-8 flex justify-center">
                <button
                    onClick={handleAnalysis}
                    disabled={!file || isLoading}
                    className="bg-brand-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 min-w-[200px] justify-center"
                >
                    {isLoading ? (
                        <span className="flex items-center gap-2">
                            <Loader2 className="animate-spin" size={20} />
                            Analyse en cours...
                        </span>
                    ) : (
                        <span className="flex items-center gap-2">
                            Analyser le fichier
                            <ArrowRight size={20} />
                        </span>
                    )}
                </button>
            </div>
        </div>
    );
}
