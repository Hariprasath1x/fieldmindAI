import { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { getMLDashboard, getFeedbackDashboard } from '../services/diagnosisApi';
import {
  BarChart3,
  Activity,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  Loader2,
  Database,
  RefreshCw,
  Lock,
} from 'lucide-react';

function MetricCard({ title, value, subtitle, icon: Icon, colorClass }) {
  return (
    <div className="bg-card p-6 rounded-xl border border-border shadow-sm flex items-start gap-4">
      <div className={`p-3 rounded-lg ${colorClass}`}>
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm font-medium text-text-secondary">{title}</p>
        <h4 className="text-2xl font-bold text-text-primary mt-1">{value}</h4>
        {subtitle && <p className="text-xs text-text-secondary mt-1">{subtitle}</p>}
      </div>
    </div>
  );
}

function ModelEvaluationCard({ modelData }) {
  const { model, dataset_available, evaluation_timestamp, dataset_message } = modelData;
  const name = model.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  if (!dataset_available) {
    return (
      <div className="p-4 border border-dashed border-gray-300 rounded-lg bg-gray-50 flex items-start gap-3">
        <Database className="h-5 w-5 text-gray-400 shrink-0" />
        <div>
          <h5 className="font-semibold text-text-primary mb-1">{name}</h5>
          <p className="text-sm text-text-secondary">{dataset_message || 'No dataset available.'}</p>
        </div>
      </div>
    );
  }

  const metrics = [];
  if (modelData.accuracy != null) metrics.push({ label: 'Accuracy', value: `${(modelData.accuracy * 100).toFixed(1)}%` });
  if (modelData.macro_f1 != null) metrics.push({ label: 'Macro F1', value: `${(modelData.macro_f1 * 100).toFixed(1)}%` });
  if (modelData.map_50 != null) metrics.push({ label: 'mAP@50', value: `${(modelData.map_50 * 100).toFixed(1)}%` });
  if (modelData.precision != null) metrics.push({ label: 'Precision', value: `${(modelData.precision * 100).toFixed(1)}%` });
  if (modelData.recall != null) metrics.push({ label: 'Recall', value: `${(modelData.recall * 100).toFixed(1)}%` });

  return (
    <div className="p-5 border border-border rounded-lg bg-background-app">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h5 className="font-bold text-text-primary">{name}</h5>
          <p className="text-xs text-text-secondary">
            Last evaluated: {new Date(evaluation_timestamp).toLocaleDateString()}
          </p>
        </div>
        <span className="px-2.5 py-1 bg-green-50 text-green-700 text-xs font-semibold rounded-full border border-green-200">
          {modelData.sample_count} samples
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {metrics.map((m) => (
          <div key={m.label} className="bg-card px-3 py-2 rounded border border-border">
            <div className="text-xs text-text-secondary mb-0.5">{m.label}</div>
            <div className="font-semibold text-text-primary">{m.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function MLDashboard() {
  const { user } = useAuth();
  const [mlData, setMlData] = useState(null);
  const [feedbackData, setFeedbackData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [accessDenied, setAccessDenied] = useState(false);

  useEffect(() => {
    if (!user) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        // ML Dashboard is public (readonly)
        const mlRes = await getMLDashboard();
        setMlData(mlRes);

        // Feedback dashboard is admin-only
        try {
          const fbRes = await getFeedbackDashboard(user.uid);
          setFeedbackData(fbRes);
        } catch (err) {
          if (err.response?.status === 403) {
            setAccessDenied(true);
          } else {
            console.error('Feedback dashboard error:', err);
          }
        }
      } catch (err) {
        console.error(err);
        setError('Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-text-secondary">
        <Lock className="h-12 w-12 mb-4 opacity-50" />
        <p>Please log in to access dashboards.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 text-primary animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-8">
        <div className="p-4 bg-red-50 text-error border border-red-200 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-8 space-y-8">
      <div className="flex items-center gap-3">
        <Activity className="h-8 w-8 text-primary" />
        <h1 className="text-3xl font-bold text-text-primary">ML Performance Dashboard</h1>
      </div>

      {/* ── Offline Evaluation Metrics ── */}
      <section className="bg-card p-6 md:p-8 rounded-xl border border-border shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-secondary" />
            Offline Evaluation Metrics
          </h2>
          {!mlData?.results_available && (
            <span className="text-sm text-yellow-600 bg-yellow-50 px-3 py-1 rounded-full border border-yellow-200">
              No evaluation runs found
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
          {mlData && Object.values(mlData.models).map((m) => (
            <ModelEvaluationCard key={m.model} modelData={m} />
          ))}
        </div>
      </section>

      {/* ── Real-time User Feedback ── */}
      <section className="bg-card p-6 md:p-8 rounded-xl border border-border shadow-sm">
        <h2 className="text-xl font-bold text-text-primary mb-6 flex items-center gap-2">
          <RefreshCw className="h-5 w-5 text-secondary" />
          Real-time User Feedback
        </h2>

        {accessDenied ? (
          <div className="p-6 text-center border border-dashed border-gray-300 rounded-xl bg-gray-50">
            <Lock className="h-8 w-8 text-gray-400 mx-auto mb-3" />
            <h3 className="font-semibold text-gray-700">Admin Access Required</h3>
            <p className="text-sm text-gray-500 mt-1">
              You do not have permission to view aggregated user feedback metrics.
            </p>
          </div>
        ) : feedbackData ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <MetricCard
                title="Total Predictions"
                value={feedbackData.total_predictions}
                icon={Database}
                colorClass="bg-blue-100 text-blue-700"
              />
              <MetricCard
                title="Feedback Rate"
                value={`${feedbackData.feedback_rate_pct}%`}
                subtitle={`${feedbackData.feedback_received} responses`}
                icon={Activity}
                colorClass="bg-purple-100 text-purple-700"
              />
              <MetricCard
                title="Correct"
                value={feedbackData.correct_count}
                icon={ThumbsUp}
                colorClass="bg-green-100 text-green-700"
              />
              <MetricCard
                title="Incorrect"
                value={feedbackData.incorrect_count}
                icon={ThumbsDown}
                colorClass="bg-red-100 text-red-700"
              />
            </div>

            {feedbackData.confusion_pairs?.length > 0 && (
              <div className="border border-border rounded-lg overflow-hidden">
                <div className="bg-background-app px-4 py-3 border-b border-border">
                  <h3 className="font-semibold text-text-primary">Top Confusion Pairs</h3>
                </div>
                <ul className="divide-y divide-border">
                  {feedbackData.confusion_pairs.slice(0, 5).map((pair, idx) => (
                    <li key={idx} className="px-4 py-3 flex justify-between items-center bg-card">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-red-600 line-through">
                          {pair.predicted}
                        </span>
                        <span className="text-gray-400">→</span>
                        <span className="text-sm font-medium text-green-600">
                          {pair.actual === 'not_specified' ? 'Unknown' : pair.actual}
                        </span>
                      </div>
                      <span className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded font-semibold">
                        {pair.count} reports
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-8 text-text-secondary">
            No feedback data available.
          </div>
        )}
      </section>
    </div>
  );
}
