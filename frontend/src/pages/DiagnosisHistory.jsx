import { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { getDiagnosisHistory } from '../services/diagnosisApi';
import {
  History,
  AlertTriangle,
  ChevronRight,
  Loader2,
  Leaf,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const CONFIDENCE_COLORS = {
  high: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-red-100 text-red-800',
};

function ProgressionBadge({ status }) {
  if (!status) return null;
  const config = {
    new: { icon: Leaf, color: 'text-blue-500 bg-blue-50 border-blue-200' },
    improving: { icon: TrendingDown, color: 'text-green-600 bg-green-50 border-green-200' },
    stable: { icon: Minus, color: 'text-gray-500 bg-gray-50 border-gray-200' },
    worsening: { icon: TrendingUp, color: 'text-red-600 bg-red-50 border-red-200' },
  }[status] || { icon: Minus, color: 'text-gray-500 bg-gray-50 border-gray-200' };

  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.color}`}>
      <Icon className="h-3 w-3" />
      <span className="capitalize">{status}</span>
    </span>
  );
}

export default function DiagnosisHistory() {
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user) return;

    const fetchHistory = async () => {
      try {
        setLoading(true);
        const data = await getDiagnosisHistory(user.uid, { limit: 50 });
        setHistory(data.diagnoses || []);
      } catch (err) {
        console.error(err);
        setError('Failed to load diagnosis history.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [user]);

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-text-secondary">
        <History className="h-12 w-12 mb-4 opacity-50" />
        <p>Please log in to view your diagnosis history.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="flex items-center gap-3 mb-8">
        <History className="h-8 w-8 text-primary" />
        <h1 className="text-3xl font-bold text-text-primary">Diagnosis History</h1>
      </div>

      {error && (
        <div className="p-4 mb-6 bg-red-50 text-error border border-red-200 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 text-primary animate-spin" />
        </div>
      ) : history.length === 0 ? (
        <div className="text-center py-12 bg-card rounded-xl border border-border shadow-sm">
          <p className="text-text-secondary mb-4">You have no previous diagnoses.</p>
          <Link
            to="/disease-detection"
            className="inline-flex items-center text-primary font-medium hover:underline"
          >
            Start a new analysis
            <ChevronRight className="h-4 w-4 ml-1" />
          </Link>
        </div>
      ) : (
        <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
          <ul className="divide-y divide-border">
            {history.map((record) => (
              <li key={record.diagnosis_id} className="hover:bg-background-app transition-colors">
                <div className="p-4 sm:p-6">
                  <div className="flex items-start justify-between flex-wrap gap-4">
                    <div>
                      <h3 className="text-lg font-bold text-text-primary capitalize mb-1">
                        {record.predicted_disease.replace(/_/g, ' ')}
                      </h3>
                      <div className="flex items-center gap-3 text-sm text-text-secondary mb-3">
                        <span>{new Date(record.timestamp).toLocaleDateString(undefined, {
                          year: 'numeric', month: 'short', day: 'numeric',
                          hour: '2-digit', minute: '2-digit'
                        })}</span>
                        {record.plant_id && (
                          <>
                            <span>&bull;</span>
                            <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">
                              {record.plant_id}
                            </span>
                          </>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${CONFIDENCE_COLORS[record.confidence_level] || 'bg-gray-100'}`}>
                          {Math.round(record.confidence * 100)}% Confidence
                        </span>
                        {record.severity_detections?.length > 0 && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-100 text-orange-800">
                            {record.severity_detections.length} Severity Regions
                          </span>
                        )}
                        {record.progression && (
                          <ProgressionBadge status={record.progression.latest_status} />
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      {record.progression?.area_delta_pct != null && (
                        <div className="text-sm">
                          <span className="text-text-secondary">Area Delta: </span>
                          <span className={`font-semibold ${
                            record.progression.area_delta_pct > 0 ? 'text-red-600' : 
                            record.progression.area_delta_pct < 0 ? 'text-green-600' : 'text-text-primary'
                          }`}>
                            {record.progression.area_delta_pct > 0 ? '+' : ''}{record.progression.area_delta_pct}%
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {record.progression?.message && (
                    <div className="mt-4 p-3 bg-blue-50/50 rounded-lg text-sm text-text-primary border border-blue-100/50">
                      {record.progression.message}
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
