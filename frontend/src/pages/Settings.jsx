import { useState, useEffect } from 'react';
import { getSystemStatus } from '../services/api';
import { Server, CheckCircle, XCircle } from 'lucide-react';

export default function Settings() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        // Simulating API call for now if backend isn't ready
        // const data = await getSystemStatus();
        
        // Mock data
        setTimeout(() => {
          setStatus({
            backend: 'online',
            models: {
              leafVerifier: true,
              diseaseModel: true,
              yoloLoaded: true,
            },
            version: '1.0.0'
          });
          setLoading(false);
        }, 1000);
      } catch (error) {
        setStatus({ backend: 'offline' });
        setLoading(false);
      }
    };
    fetchStatus();
  }, []);

  const StatusIcon = ({ isOnline }) => {
    return isOnline ? (
      <CheckCircle className="h-5 w-5 text-success" />
    ) : (
      <XCircle className="h-5 w-5 text-error" />
    );
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 py-6">
      <h1 className="text-3xl font-bold text-text-primary">System Settings</h1>
      
      <div className="bg-card rounded-xl shadow-sm border border-border overflow-hidden">
        <div className="px-6 py-4 border-b border-border bg-gray-50 flex items-center">
          <Server className="h-5 w-5 text-text-secondary mr-2" />
          <h2 className="text-lg font-semibold text-text-primary">Backend Status</h2>
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="flex justify-center items-center h-20 text-text-secondary">
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
                  <div className="flex justify-between items-center py-2">
                    <span className="text-text-primary">API Version</span>
                    <span className="text-text-secondary font-mono bg-gray-100 px-2 py-1 rounded">
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
           {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
         </code>
      </div>
    </div>
  );
}
