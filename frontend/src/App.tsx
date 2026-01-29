
import { useState } from 'react';
import { Layout } from './components/Layout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ArrowRight, AlertTriangle, RotateCcw, Download, FileCheck } from 'lucide-react';
import { API_ENDPOINTS } from './config/api';

// --- Types ---
type DepotType = 'Conforme' | 'Non-Conforme' | null;

interface Stats {
  total_lines: number;
  total_products: number;
  total_lots: number;
}

// --- Step 1: Depot Selection ---
function StepDepot({ onNext }: { onNext: (depot: DepotType) => void }) {
  const [selected, setSelected] = useState<DepotType>(null);

  const options = [
    { value: 'Conforme', label: 'Dépôt Conforme', desc: 'Lots A / AM uniquement', color: 'border-emerald-200 bg-emerald-50 hover:border-emerald-500' },
    { value: 'Non-Conforme', label: 'Dépôt Non Conforme', desc: 'Lots R / RM uniquement', color: 'border-amber-200 bg-amber-50 hover:border-amber-500' },
  ];

  return (
    <div className="max-w-lg mx-auto py-8">
      <h2 className="text-2xl font-bold text-center mb-2">Sélection du contexte</h2>
      <p className="text-center text-slate-500 mb-8">Choisissez le type de dépôt pour initialiser les règles de validation.</p>

      <div className="space-y-4">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setSelected(opt.value as DepotType)}
            className={`w-full text-left p-4 rounded-lg border-2 transition-all ${selected === opt.value ? 'border-brand-600 ring-1 ring-brand-600' : 'border-slate-200 hover:border-brand-300'
              }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-lg">{opt.label}</div>
                <div className="text-sm text-slate-500">{opt.desc}</div>
              </div>
              <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${selected === opt.value ? 'border-brand-600' : 'border-slate-300'
                }`}>
                {selected === opt.value && <div className="w-3 h-3 rounded-full bg-brand-600" />}
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="mt-8 flex justify-center">
        <button
          onClick={() => onNext(selected)}
          disabled={!selected}
          className="bg-brand-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          Continuer
          <ArrowRight size={20} />
        </button>
      </div>

      {selected === 'Non-Conforme' && (
        <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3 text-amber-800 text-sm">
          <AlertTriangle className="shrink-0 mt-0.5" size={16} />
          <p>Attention : Ce mode rejettera tout fichier contenant des lots A ou AM standard.</p>
        </div>
      )}
    </div>
  );
}

// --- Main App ---
import { StepUpload } from './components/StepUpload';
import { StepSummary } from './components/StepSummary';
import { SessionHistory } from './components/SessionHistory';

function App() {
  const [step, setStep] = useState(1);
  const [depot, setDepot] = useState<DepotType>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);

  const handleDepotSelect = (fullDepot: DepotType) => {
    setDepot(fullDepot);
    setStep(2);
  };

  const handleUploadSuccess = (sid: number, uploadStats: Stats) => {
    setSessionId(sid);
    setStats(uploadStats);
    setStep(3);
  };

  const handleTemplateSuccess = () => {
    setStep(4);
  };

  const handleResume = async (resumeSessionId: number) => {
    try {
      const response = await fetch(API_ENDPOINTS.resumeSession(resumeSessionId));
      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        setDepot(data.depot_type);

        if (data.stats) {
          setStats(data.stats);
        }

        setStep(data.step);
      }
    } catch (error) {
      console.error("Failed to resume session", error);
    }
  };

  return (
    <ErrorBoundary>
      <Layout currentStep={step} headerContent={<SessionHistory onResume={handleResume} />}>
        {step === 1 && <StepDepot onNext={handleDepotSelect} />}
        {step === 2 && depot && <StepUpload depotType={depot} onSuccess={handleUploadSuccess} />}
        {step === 3 && sessionId && stats && <StepSummary sessionId={sessionId} stats={stats} onSuccess={handleTemplateSuccess} />}
        {step === 4 && (
          <div className="max-w-2xl mx-auto py-12 text-center animate-in fade-in zoom-in duration-500">
            <div className="w-24 h-24 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-8 shadow-sm">
              <FileCheck size={48} />
            </div>

            <h2 className="text-3xl font-bold text-slate-900 mb-4">Traitement terminé !</h2>
            <p className="text-lg text-slate-600 mb-12 max-w-md mx-auto">
              Votre fichier d'import Sage X3 a été généré et est prêt à être intégré.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
              <a
                href={API_ENDPOINTS.downloadFile(sessionId!, 'final')}
                className="w-full sm:w-auto bg-brand-600 text-white px-8 py-4 rounded-xl font-bold shadow-lg shadow-brand-600/20 hover:bg-brand-700 hover:shadow-brand-600/30 hover:-translate-y-1 transition-all flex items-center justify-center gap-3"
              >
                <Download size={24} />
                Télécharger le fichier final
              </a>

              <button
                onClick={() => window.location.reload()}
                className="w-full sm:w-auto bg-white text-slate-600 border-2 border-slate-200 px-8 py-4 rounded-xl font-semibold hover:border-slate-300 hover:bg-slate-50 hover:text-slate-800 transition-all flex items-center justify-center gap-2"
              >
                <RotateCcw size={20} />
                Nouveau traitement
              </button>
            </div>
          </div>
        )}
      </Layout>
    </ErrorBoundary>
  );
}

export default App;
