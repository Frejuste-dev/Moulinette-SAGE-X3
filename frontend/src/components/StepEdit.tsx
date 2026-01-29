
import { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, AlertTriangle, Save } from 'lucide-react';

interface StepEditProps {
    sessionId: number;
    onSuccess: () => void;
}

interface InventoryLine {
    session_id: string;
    inventaire: string;
    article: string;
    quantite_theorique: number;
    quantite_reelle: number | string; // Helper for input handling
    depot: string;
    emplacement: string;
    unite: string;
}

export function StepEdit({ sessionId, onSuccess }: StepEditProps) {
    const [data, setData] = useState<InventoryLine[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Fetch data on mount
    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await axios.get(`http://localhost:8000/inventory/preview/${sessionId}`);
                setData(res.data);
            } catch (err) {
                setError("Erreur lors du chargement des données.");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [sessionId]);

    // Handle Input Change
    const handleQuantityChange = (index: number, value: string) => {
        const newData = [...data];
        // Allow empty string for better typing experience, but validate later
        newData[index].quantite_reelle = value;
        setData(newData);
    };

    // Validation Logic
    // Returns count of errors
    const validate = () => {
        let errs = 0;
        for (const row of data) {
            const val = row.quantite_reelle;
            if (val === '' || val === null || val === undefined) continue; // treated as 0
            const num = Number(val);
            if (isNaN(num)) errs++;
            if (num < 0) errs++;
        }
        return errs;
    };

    const errorCount = validate();

    const handleSubmit = async () => {
        if (errorCount > 0) return;
        setSubmitting(true);
        setError(null);

        // Prepare payload: convert empty/strings to floats
        const cleanData = data.map(d => ({
            ...d,
            quantite_reelle: (d.quantite_reelle === '' || d.quantite_reelle === null) ? 0 : Number(d.quantite_reelle)
        }));

        try {
            await axios.post(`http://localhost:8000/inventory/process-data/${sessionId}`, cleanData);
            onSuccess();
        } catch (err: any) {
            setError(err.response?.data?.detail || "Erreur lors de la sauvegarde.");
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-20 text-slate-500">
                <Loader2 className="animate-spin mb-4" size={32} />
                <p>Chargement des données...</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">Saisie des quantités</h2>
                <div className="text-sm text-slate-500">
                    {data.length} lignes à traiter
                </div>
            </div>

            {error && (
                <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg">
                    {error}
                </div>
            )}

            {/* Table Container with Scroll */}
            <div className="border border-slate-200 rounded-lg overflow-x-auto max-h-[60vh] overflow-y-auto shadow-sm">
                <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 text-slate-700 font-semibold sticky top-0 z-10 shadow-sm">
                        <tr>
                            <th className="px-4 py-3 border-b">Article</th>
                            <th className="px-4 py-3 border-b">Emplacement</th>
                            <th className="px-4 py-3 border-b text-right">Théorique</th>
                            <th className="px-4 py-3 border-b w-40 text-right">Réel (Saisie)</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {data.map((row, idx) => {
                            const val = row.quantite_reelle;
                            const num = Number(val);
                            const isInvalid = (val !== '' && isNaN(num)) || num < 0;

                            return (
                                <tr key={idx} className="hover:bg-slate-50 transition-colors">
                                    <td className="px-4 py-2 font-medium">{row.article}</td>
                                    <td className="px-4 py-2 text-slate-500">{row.emplacement} {row.depot}</td>
                                    <td className="px-4 py-2 text-right text-slate-600">{row.quantite_theorique}</td>
                                    <td className="px-4 py-2 text-right">
                                        <input
                                            type="number"
                                            value={row.quantite_reelle}
                                            onChange={(e) => handleQuantityChange(idx, e.target.value)}
                                            placeholder="0"
                                            className={`
                                        w-24 px-2 py-1 text-right border rounded focus:ring-2 focus:outline-none transition-all
                                        ${isInvalid
                                                    ? 'border-red-300 focus:border-red-500 focus:ring-red-200 bg-red-50'
                                                    : 'border-slate-300 focus:border-brand-500 focus:ring-brand-100'}
                                     `}
                                        />
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Footer Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                <div className="text-sm">
                    {errorCount > 0 ? (
                        <span className="text-red-600 font-medium flex items-center gap-2">
                            <AlertTriangle size={16} />
                            {errorCount} erreur(s) à corriger
                        </span>
                    ) : (
                        <span className="text-emerald-600 font-medium flex items-center gap-2">
                            <CheckCircle size={16} className="text-emerald-500" />
                            Prêt à valider
                        </span>
                    )}
                </div>

                <button
                    onClick={handleSubmit}
                    disabled={errorCount > 0 || submitting}
                    className="bg-brand-600 text-white px-6 py-2.5 rounded-lg font-semibold hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                    {submitting ? <Loader2 className="animate-spin" /> : <Save size={18} />}
                    Générer Fichier Final
                </button>
            </div>
        </div>
    );
}
// Helper import needed inside function scope or top level?
// CheckCircle was used but check existing imports
import { CheckCircle } from 'lucide-react';
