
import type { PropsWithChildren } from 'react';
import { CheckCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface LayoutProps extends PropsWithChildren {
    currentStep: number;
    headerContent?: React.ReactNode;
}

export function cn(...inputs: (string | undefined | null | false)[]) {
    return twMerge(clsx(inputs));
}

const steps = [
    { id: 1, title: 'Contexte', description: 'Choix du dépôt' },
    { id: 2, title: 'Import', description: 'Masque Sage X3' },
    { id: 3, title: 'Saisie', description: 'Validation & Correction' },
    { id: 4, title: 'Résultat', description: 'Export Final' },
];

export function Layout({ children, currentStep, headerContent }: LayoutProps) {
    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
            {/* Header */}
            <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
                <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-white p-1 rounded-lg">
                            <img src="/logo.png" alt="Moulinette Logo" className="w-8 h-8 object-contain" />
                        </div>
                        <h1 className="text-lg font-semibold text-slate-800">Moulinette Inventaire</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        {headerContent}
                        <div className="text-sm text-slate-500">v2.0.0</div>
                    </div>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 py-8">
                {/* Stepper */}
                <div className="mb-12">
                    <div className="flex items-center justify-between relative max-w-4xl mx-auto">
                        {/* ProgressBar Background */}
                        <div className="absolute left-0 top-[20px] w-full h-1 bg-slate-100 rounded-full -z-10" />

                        {/* ProgressBar Fill */}
                        <div
                            className="absolute left-0 top-[20px] h-1 bg-brand-600 rounded-full -z-10 transition-all duration-700 ease-out"
                            style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
                        />

                        {steps.map((step) => {
                            const isActive = step.id === currentStep;
                            const isCompleted = step.id < currentStep;

                            return (
                                <div key={step.id} className="flex flex-col items-center group cursor-default relative">
                                    <div
                                        className={cn(
                                            "w-12 h-12 rounded-full flex items-center justify-center border-4 transition-all duration-500 z-10",
                                            isActive
                                                ? "border-brand-100 bg-brand-600 text-white shadow-lg shadow-brand-600/30 scale-110"
                                                : isCompleted
                                                    ? "border-brand-600 bg-brand-600 text-white"
                                                    : "border-white bg-slate-100 text-slate-400"
                                        )}
                                    >
                                        {isCompleted ? (
                                            <CheckCircle size={20} className="animate-in zoom-in duration-300" />
                                        ) : (
                                            <span className={cn("text-sm font-bold transition-colors", isActive ? "text-white" : "text-slate-500")}>
                                                {step.id}
                                            </span>
                                        )}

                                        {/* Pulse effect for active step */}
                                        {isActive && (
                                            <span className="absolute inset-0 rounded-full bg-brand-600 opacity-20 animate-ping" />
                                        )}
                                    </div>

                                    <div className="mt-3 text-center transition-all duration-500">
                                        <div className={cn(
                                            "text-sm font-semibold tracking-tight",
                                            isActive ? "text-brand-800 translate-y-0" : isCompleted ? "text-brand-700" : "text-slate-400"
                                        )}>
                                            {step.title}
                                        </div>
                                        <div className={cn(
                                            "text-xs mt-0.5 transition-colors duration-300",
                                            isActive ? "text-slate-500" : "text-slate-300"
                                        )}>
                                            {step.description}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Content */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 min-h-[400px]">
                    {children}
                </div>
            </main>
        </div>
    );
}
