import { useEffect, useState } from 'react';
import Card from './common/Card';
import Button from './common/Button';

interface GOSTResponse {
  timestamp: string;
  handshake_status: 'success' | 'failed' | 'pending';
  cipher: string;
  server_certificate: {
    subject: string;
    issuer: string;
    valid_from: string;
    valid_to: string;
    ogrn?: string;
    inn?: string;
  } | null;
  session_id: string | null;
  error: string | null;
}

export default function GOSTResponsePanel() {
  const [response, setResponse] = useState<GOSTResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const testGOSTConnection = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/gost/test-connection', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      const data = await res.json();
      setResponse(data);
    } catch (error) {
      console.error('GOST test failed:', error);
      setResponse({
        timestamp: new Date().toISOString(),
        handshake_status: 'failed',
        cipher: '',
        server_certificate: null,
        session_id: null,
        error: String(error)
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load last response from localStorage if exists
    const lastResponse = localStorage.getItem('last_gost_response');
    if (lastResponse) {
      try {
        setResponse(JSON.parse(lastResponse));
      } catch (e) {
        // Ignore parse errors
      }
    }
  }, []);

  useEffect(() => {
    if (response) {
      localStorage.setItem('last_gost_response', JSON.stringify(response));
    }
  }, [response]);

  return (
    <Card className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-display text-xl text-ink">GOST Connection Test</h3>
          <p className="text-sm text-ink/60">Real response from api.gost.bankingapi.ru:8443</p>
        </div>
        <Button 
          onClick={testGOSTConnection} 
          disabled={loading}
          className="bg-primary-600 text-white hover:bg-primary-700"
        >
          {loading ? 'Testing...' : 'Test Connection'}
        </Button>
      </div>

      {response && (
        <div className="space-y-4 rounded-lg border border-white/30 bg-white/50 p-4">
          {/* Status */}
          <div className="flex items-center gap-2">
            <span className="text-2xl">
              {response.handshake_status === 'success' ? '✅' : 
               response.handshake_status === 'failed' ? '❌' : '⏳'}
            </span>
            <div>
              <p className="text-xs uppercase tracking-wide text-ink/50">Status</p>
              <p className={`font-semibold ${
                response.handshake_status === 'success' ? 'text-green-600' : 
                response.handshake_status === 'failed' ? 'text-red-600' : 'text-yellow-600'
              }`}>
                {response.handshake_status.toUpperCase()}
              </p>
            </div>
          </div>

          {/* Timestamp */}
          <div>
            <p className="text-xs uppercase tracking-wide text-ink/50">Timestamp</p>
            <p className="font-mono text-sm text-ink">
              {new Date(response.timestamp).toLocaleString('ru-RU')}
            </p>
          </div>

          {/* Cipher */}
          {response.cipher && (
            <div>
              <p className="text-xs uppercase tracking-wide text-ink/50">Cipher Suite</p>
              <p className="font-mono text-sm text-ink break-all">
                {response.cipher}
              </p>
            </div>
          )}

          {/* Session ID */}
          {response.session_id && (
            <div>
              <p className="text-xs uppercase tracking-wide text-ink/50">Session ID</p>
              <p className="font-mono text-xs text-ink break-all">
                {response.session_id}
              </p>
            </div>
          )}

          {/* Server Certificate */}
          {response.server_certificate && (
            <div className="space-y-2 rounded border border-primary-200/50 bg-primary-50/30 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-primary-700">
                Server Certificate
              </p>
              <div className="space-y-1 text-sm">
                <div>
                  <span className="text-xs text-ink/50">Subject:</span>
                  <p className="font-mono text-xs text-ink">{response.server_certificate.subject}</p>
                </div>
                {response.server_certificate.ogrn && (
                  <div>
                    <span className="text-xs text-ink/50">ОГРН:</span>
                    <p className="font-mono text-xs text-ink">{response.server_certificate.ogrn}</p>
                  </div>
                )}
                {response.server_certificate.inn && (
                  <div>
                    <span className="text-xs text-ink/50">ИНН:</span>
                    <p className="font-mono text-xs text-ink">{response.server_certificate.inn}</p>
                  </div>
                )}
                <div>
                  <span className="text-xs text-ink/50">Valid:</span>
                  <p className="font-mono text-xs text-ink">
                    {new Date(response.server_certificate.valid_from).toLocaleDateString()} - {' '}
                    {new Date(response.server_certificate.valid_to).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-ink/50">Issuer:</span>
                  <p className="font-mono text-xs text-ink">{response.server_certificate.issuer}</p>
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {response.error && (
            <div className="rounded border border-red-200 bg-red-50/50 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-red-700">Error</p>
              <p className="mt-1 font-mono text-xs text-red-900">{response.error}</p>
            </div>
          )}
        </div>
      )}

      {!response && (
        <div className="rounded-lg border border-dashed border-ink/20 p-8 text-center">
          <p className="text-sm text-ink/60">
            Click "Test Connection" to see real GOST TLS handshake response
          </p>
        </div>
      )}
    </Card>
  );
}

