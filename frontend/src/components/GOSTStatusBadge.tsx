/**
 * GOST Status Badge Component
 * Показывает статус GOST-шлюза в интерфейсе
 */

import { useEffect, useState } from 'react';
import { api } from '../services/api';

interface GOSTStatus {
  enabled: boolean;
  mode: string;
  api_endpoint: string;
  description: string;
  requirements?: Record<string, any>;
  recommendation?: string;
}

export function GOSTStatusBadge() {
  const [status, setStatus] = useState<GOSTStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    void fetchGOSTStatus();
  }, []);

  const fetchGOSTStatus = async () => {
    try {
      const response = await api.getGostStatus();
      setStatus(response);
    } catch (error) {
      console.error('Failed to fetch GOST status:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-100 rounded-lg px-3 py-2 text-sm">
        <span className="text-gray-600">Loading GOST status...</span>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  const iconByStatus = status.enabled ? '🔒' : '⚠️';
  const colorByStatus = status.enabled
    ? 'bg-green-100 border-green-300 text-green-800'
    : 'bg-yellow-100 border-yellow-300 text-yellow-800';

  async function testConnection() {
    try {
      const response = await api.testGostConnection();
      alert(
        response.success
          ? '✅ ' + response.message
          : '❌ ' + response.message
      );
    } catch (error) {
      alert('❌ Failed to test connection: ' + error);
    }
  }

  return (
    <div className={`rounded-lg border-2 ${colorByStatus} transition-all duration-200`}>
      {/* Main Badge */}
      <div
        className="px-4 py-3 cursor-pointer flex items-center justify-between"
        onClick={() => setShowDetails(!showDetails)}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{iconByStatus}</span>
          <div>
            <div className="font-semibold text-sm">
              GOST Status: {status.enabled ? 'Active' : 'Not Available'}
            </div>
            <div className="text-xs opacity-75 mt-0.5">
              {status.enabled ? 'Secured with GOST TLS' : 'Using Standard API'}
            </div>
          </div>
        </div>
        <button className="text-xs underline hover:no-underline">
          {showDetails ? 'Hide Details' : 'View Details'}
        </button>
      </div>

      {/* Details Panel */}
      {showDetails && (
        <div className="border-t-2 border-current px-4 py-3 space-y-3">
          {/* Description */}
          <div className="text-sm">
            <strong>Description:</strong>
            <p className="mt-1 opacity-90">{status.description}</p>
          </div>

          {/* API Endpoint */}
          <div className="text-sm">
            <strong>API Endpoint:</strong>
            <code className="mt-1 block bg-white bg-opacity-50 px-2 py-1 rounded text-xs">
              {status.api_endpoint}
            </code>
          </div>

          {/* Requirements (if not enabled) */}
          {!status.enabled && status.requirements && (
            <div className="text-sm">
              <strong>Requirements:</strong>
              <div className="mt-2 space-y-2">
                {Object.entries(status.requirements).map(([key, req]: [string, any]) => (
                  <div key={key} className="flex items-center gap-2 text-xs">
                    <span className="text-lg">{req.installed ? '✅' : '❌'}</span>
                    <span className={req.installed ? 'text-green-700' : 'text-red-700'}>
                      {req.description}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendation */}
          {status.recommendation && !status.enabled && (
            <div className="text-sm">
              <strong>Recommendation:</strong>
              <p className="mt-1 opacity-90 whitespace-pre-line text-xs">
                {status.recommendation}
              </p>
            </div>
          )}

          {/* Test Connection Button */}
          <button
            onClick={testConnection}
            className="w-full mt-2 bg-white bg-opacity-50 hover:bg-opacity-70 px-3 py-2 rounded text-sm font-medium transition-colors"
          >
            Test GOST Connection
          </button>
        </div>
      )}
    </div>
  );
}

