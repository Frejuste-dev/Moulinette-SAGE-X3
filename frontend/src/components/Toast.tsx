import { useEffect } from 'react';
import { CheckCircle, X } from 'lucide-react';

interface ToastProps {
    message: string;
    onClose: () => void;
    duration?: number;
}

export function Toast({ message, onClose, duration = 3000 }: ToastProps) {
    useEffect(() => {
        const timer = setTimeout(() => {
            onClose();
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, onClose]);

    return (
        <div className="fixed bottom-6 right-6 z-[70] animate-slide-up">
            <div className="bg-white rounded-lg shadow-2xl border border-slate-200 p-4 flex items-center gap-3 min-w-[300px]">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
                <p className="flex-1 text-sm font-medium text-slate-900">{message}</p>
                <button
                    onClick={onClose}
                    className="flex-shrink-0 text-slate-400 hover:text-slate-600 transition-colors"
                >
                    <X size={18} />
                </button>
            </div>
        </div>
    );
}
