import { useState, useEffect } from 'react';
import { Server, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import apiClient from '../services/api';

export default function Settings() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await apiClient.get('/ready');
        const checks = res.data?.checks || {};
        setStatus({
          backend: 'online',
          models: {
            leafVerifier: checks.leaf_verifier === 'ready',
            diseaseModel: checks.ml_models === 'ready',
            yoloLoaded: checks.ml_models === 'ready',
          },
          database: checks.database === 'ready',
          version: '2.0.0',
          overall: res.data?.status,
        });
      } catch {
        setStatus({ backend: 'offline' });
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
  }, []);

  const StatusIcon = ({ isOnline }) =>
    isOnline ? (
      <CheckCircle className="h-5 w-5 text-success" />
    ) : (
      <XCircle className="h-5 w-5 text-error" />
    );

  return (
    <div className="max-w-2xl mx-auto space-y-8 py-6">
      <h1 className="text-3xl font-bold text-text-primary">System Settings</h1>

      <div className="bg-card rounded-xl shadow-sm border border-border overflow-hidden">
        <div className="px-6 py-4 border-b border-border bg-gray-50 flex items-center justify-between">
          <div className="flex items-center">
            <Server className="h-5 w-5 text-text-secondary mr-2" />
            <h2 className="text-lg font-semibold text-text-primary">Backend Status</h2>
          </div>
          {!loading && status?.backend === 'online' && (
            <span className={`text-xs px-2 py-1 rounded-full font-semibold border ${
              status?.overall === 'ready'
                ? 'bg-green-50 text-green-700 border-green-200'
                : 'bg-yellow-50 text-yellow-700 border-yellow-200'
            }`}>
              {status?.overall === 'ready' ? 'All Systems Operational' : 'Degraded'}
            </span>
          )}
        </div>

        <div className="p-6">
          {loading ? (
            <div className="flex justify-center items-center h-20 gap-2 text-text-secondary">
              <Loader2 className="h-5 w-5 animate-spin" />
              Checking status...
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-text-primary font-medium">API Connection</span>
                <div className="flex items-center space-x-2">
                  <span className={status?.backend === 'online' ? 'text-success' : 'text-error'}>
                    {status?.backend === 'online' ? 'Online' : 'Offline'}
                  </span>
                  <StatusIcon isOnline={status?.backend === 'online'} />
                </div>
              </div>

              {status?.backend === 'online' && (
                <>
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-text-primary">Leaf Verifier Model</span>
                    <StatusIcon isOnline={status?.models?.leafVerifier} />
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-text-primary">Disease Classifier Model</span>
                    <StatusIcon isOnline={status?.models?.diseaseModel} />
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-text-primary">YOLO Severity Model</span>
                    <StatusIcon isOnline={status?.models?.yoloLoaded} />
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-text-primary">Database (Firestore)</span>
                    <StatusIcon isOnline={status?.database} />
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-text-primary">API Version</span>
                    <span className="text-text-secondary font-mono bg-gray-100 px-2 py-1 rounded text-sm">
                      v{status?.version || 'Unknown'}
                    </span>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="bg-card rounded-xl shadow-sm border border-border p-6">
        <h3 className="text-sm font-medium text-text-secondary mb-2">API Base URL</h3>
        <code className="block w-full bg-gray-50 border border-gray-200 rounded p-3 text-sm text-gray-700">
          {import.meta.env.VITE_API_URL || 'http://localhost:8002'}
        </code>
      </div>

      <div className="bg-card rounded-xl shadow-sm border border-border p-6">
        <h3 className="text-sm font-semibold text-text-primary mb-3">About This Build</h3>
        <div className="space-y-2 text-sm text-text-secondary">
          <p>FieldMind is a student/demo project demonstrating end-to-end AI integration.</p>
          <p>ML models are frozen. Disease predictions are AI-generated estimates — verify with a local agronomist before taking treatment decisions.</p>
        </div>
      </div>
    </div>
  );
}
