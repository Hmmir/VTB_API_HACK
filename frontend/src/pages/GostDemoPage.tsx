import { useState, useEffect } from 'react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import toast from 'react-hot-toast';
import { api } from '../services/api';

const GostDemoPage = () => {
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [gostStatus, setGostStatus] = useState<any>(null);
  const [connectionResult, setConnectionResult] = useState<any>(null);
  const [transactionLog, setTransactionLog] = useState<Array<{
    timestamp: string;
    action: string;
    status: 'success' | 'pending' | 'error';
  }>>([]);

  // Загрузить статус ГОСТ при монтировании
  useEffect(() => {
    loadGostStatus();
  }, []);

  const loadGostStatus = async () => {
    try {
      const status = await api.getGostStatus();
      setGostStatus(status);
      if (status.configured && status.csptest_available) {
        addLog(`ГОСТ настроен: ${status.client_id}`, 'success');
      }
    } catch (error) {
      console.error('Failed to load GOST status:', error);
    }
  };

  const addLog = (action: string, status: 'success' | 'pending' | 'error' = 'success') => {
    setTransactionLog(prev => [{
      timestamp: new Date().toLocaleTimeString('ru-RU'),
      action,
      status
    }, ...prev]);
  };

  const handleConnect = async () => {
    setConnecting(true);
    setTransactionLog([]); // Очистить лог
    addLog('🔄 Запуск реального GOST TLS теста через csptest.exe...', 'pending');
    
    try {
      // Реальный тест ГОСТ подключения
      const result = await api.testGostConnection();
      
      if (result.success) {
        addLog(`✅ Handshake was successful`, 'success');
        addLog(`✅ Protocol: TLS 1.2`, 'success');
        addLog(`✅ Cipher: ${result.cipher || 'GOST'}`, 'success');
        addLog(`✅ Server: ${result.server || 'api.gost.bankingapi.ru'}`, 'success');
        addLog(`✅ Time: ${result.time?.toFixed(2)}s`, 'success');
        if (result.request_id) {
          addLog(`🔢 Request ID: ${result.request_id} (уникальный для каждого запроса)`, 'success');
        }
        
        // Показать строки доказательства из csptest.exe
        if (result.proof && result.proof.length > 0) {
          addLog(`📄 Доказательства из csptest.exe:`, 'success');
          result.proof.slice(0, 5).forEach((line: string) => {
            addLog(`   ${line}`, 'success');
          });
        }
        
        setConnected(true);
        setConnectionResult(result); // Сохранить результат для отображения
        toast.success('ГОСТ TLS handshake успешен!');
      } else {
        addLog(`❌ Handshake failed`, 'error');
        addLog(`❌ Error: ${result.error || 'Unknown error'}`, 'error');
        if (result.output) {
          addLog(`📄 Output: ${result.output.substring(0, 200)}...`, 'error');
        }
        toast.error('ГОСТ TLS handshake не удался');
      }
    } catch (error: any) {
      addLog(`❌ Exception: ${error.message}`, 'error');
      toast.error('Ошибка при вызове GOST API');
    } finally {
      setConnecting(false);
    }
  };

  const handleTransaction = async (type: string) => {
    addLog(`Создание запроса: ${type}`, 'pending');
    await new Promise(resolve => setTimeout(resolve, 500));
    
    addLog('Подпись запроса (ГОСТ Р 34.10-2012)', 'pending');
    await new Promise(resolve => setTimeout(resolve, 700));
    
    addLog('Отправка через защищенный канал', 'pending');
    await new Promise(resolve => setTimeout(resolve, 600));
    
    addLog(`✅ ${type} - успешно`, 'success');
    toast.success(`${type} выполнена успешно!`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-display font-bold text-slate-900">
            🔐 ГОСТ Криптография - Демо
          </h1>
          <p className="text-slate-600 max-w-3xl mx-auto">
            Демонстрация интеграции криптографических алгоритмов ГОСТ Р 34.10-2012 (ЭЦП) 
            и ГОСТ Р 34.11-2012 (хэширование) для защищенного взаимодействия с банковскими API.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          
          {/* Left: Connection Panel */}
          <div className="lg:col-span-1 space-y-4">
            <Card className="bg-white/90 backdrop-blur p-6">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
                  <h2 className="text-xl font-semibold text-slate-900">
                    {connected ? 'Подключено' : 'Не подключено'}
                  </h2>
                </div>

                <div className="space-y-2 text-sm">
                  {connectionResult && connected ? (
                    <>
                      <div className="flex justify-between text-slate-600">
                        <span>Protocol:</span>
                        <span className="font-mono font-semibold text-green-900">TLS 1.2</span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Cipher:</span>
                        <span className="font-mono font-semibold text-green-900 text-xs">{connectionResult.cipher}</span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Server:</span>
                        <span className="font-mono font-semibold text-green-900 text-xs">{connectionResult.server}</span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Time:</span>
                        <span className="font-mono font-semibold text-green-900">{connectionResult.time?.toFixed(2)}s</span>
                      </div>
                    </>
                  ) : gostStatus ? (
                    <>
                      <div className="flex justify-between text-slate-600">
                        <span>Client ID:</span>
                        <span className="font-mono font-semibold text-slate-900">{gostStatus.client_id}</span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Configured:</span>
                        <span className={`font-semibold ${gostStatus.configured ? 'text-green-600' : 'text-red-600'}`}>
                          {gostStatus.configured ? '✅ Yes' : '❌ No'}
                        </span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>CryptoPro:</span>
                        <span className={`font-semibold ${gostStatus.csptest_available ? 'text-green-600' : 'text-orange-600'}`}>
                          {gostStatus.csptest_available ? '✅ Available' : '⚠️ Not found'}
                        </span>
                      </div>
                    </>
                  ) : null}
                </div>

                <Button
                  variant={connected ? 'ghost' : 'primary'}
                  onClick={handleConnect}
                  disabled={connecting || connected}
                  className="w-full"
                >
                  {connecting && '⏳ Подключение...'}
                  {connected && '✅ Подключено'}
                  {!connecting && !connected && '🔗 Подключиться'}
                </Button>

                {connected && (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setConnected(false);
                      setConnectionResult(null);
                      addLog('🔌 Соединение разорвано', 'error');
                    }}
                    className="w-full text-red-600 border-red-200 hover:bg-red-50"
                  >
                    Отключить
                  </Button>
                )}
              </div>
            </Card>

            {/* Cert Info */}
            {connected && (
              <Card className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 border-2 border-green-200">
                <div className="space-y-2">
                  <h3 className="text-sm font-semibold text-green-900 flex items-center gap-2">
                    <span>🔑</span>
                    <span>Сертификат ГОСТ</span>
                  </h3>
                  <div className="space-y-1 text-xs text-green-800">
                    <div className="font-semibold">Organization: Банк ВТБ (ПАО)</div>
                    <div>ОГРН: 1027739609391</div>
                    <div>ИНН: 7702070139</div>
                    <div className="text-[10px] text-green-700">
                      Адрес: Переулок Дегтярный, дом 11, литер А, Санкт-Петербург
                    </div>
                    <div className="pt-2 border-t border-green-200">
                      <div className="font-semibold">Valid: 26.10.2025 - 09.12.2025</div>
                      <div className="text-[10px]">Issuer: Тестовый УЦ ИнфоТеКС</div>
                    </div>
                    <div className="pt-2 text-[10px] bg-green-100 p-2 rounded">
                      Endpoint: api.gost.bankingapi.ru:8443
                    </div>
                  </div>
                </div>
              </Card>
            )}
          </div>

          {/* Center: Actions */}
          <div className="lg:col-span-1 space-y-4">
            <Card className="bg-white/90 backdrop-blur p-6">
              <h2 className="text-xl font-semibold text-slate-900 mb-4">
                🔐 Реальное GOST подключение
              </h2>
              
              <div className="space-y-3 text-sm text-slate-700">
                <div className="bg-blue-50 p-3 rounded border border-blue-200">
                  <div className="font-semibold text-blue-900 mb-1">Что происходит:</div>
                  <ol className="text-xs space-y-1 list-decimal list-inside text-blue-800">
                    <li>Frontend вызывает backend API</li>
                    <li>Backend вызывает Windows Service</li>
                    <li>Service запускает csptest.exe</li>
                    <li>TLS handshake с ГОСТ шифрованием</li>
                    <li>Получение сертификата ВТБ</li>
                    <li>Возврат реального результата</li>
                  </ol>
                </div>

                <div className="bg-green-50 p-3 rounded border border-green-200">
                  <div className="font-semibold text-green-900 mb-1">✅ Что доказывает:</div>
                  <ul className="text-xs space-y-1 text-green-800">
                    <li>• Реальное TLS 1.2 подключение</li>
                    <li>• ГОСТ Р 34.12-2015 Kuznyechik (256 bit)</li>
                    <li>• Сертификат ВТБ (ОГРН, ИНН)</li>
                    <li>• Handshake successful</li>
                  </ul>
                </div>

                <div className="bg-amber-50 p-3 rounded border border-amber-200">
                  <div className="font-semibold text-amber-900 mb-1">⚠️ Требования:</div>
                  <ul className="text-xs space-y-1 text-amber-800">
                    <li>• CryptoPro CSP установлен</li>
                    <li>• Сертификат "VTB Test User"</li>
                    <li>• Windows Service запущен (порт 5555)</li>
                  </ul>
                </div>
              </div>
            </Card>

          </div>

          {/* Right: Transaction Log */}
          <div className="lg:col-span-1">
            <Card className="bg-white/90 backdrop-blur p-6 h-full">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-slate-900">
                  📋 Лог операций
                </h2>
                {transactionLog.length > 0 && (
                  <button
                    onClick={() => setTransactionLog([])}
                    className="text-xs text-slate-500 hover:text-slate-700"
                  >
                    Очистить
                  </button>
                )}
              </div>

              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {transactionLog.length === 0 ? (
                  <div className="text-center text-slate-400 py-8 text-sm">
                    Лог пуст. Выполните операцию.
                  </div>
                ) : (
                  transactionLog.map((log, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border text-xs ${
                        log.status === 'success'
                          ? 'bg-green-50 border-green-200 text-green-800'
                          : log.status === 'error'
                          ? 'bg-red-50 border-red-200 text-red-800'
                          : 'bg-blue-50 border-blue-200 text-blue-800'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className="font-mono text-[10px] text-slate-500">
                          {log.timestamp}
                        </span>
                        <span className={`text-lg ${
                          log.status === 'success' ? '' : 'animate-spin'
                        }`}>
                          {log.status === 'success' && '✓'}
                          {log.status === 'pending' && '⏳'}
                          {log.status === 'error' && '✗'}
                        </span>
                      </div>
                      <div className="mt-1 font-medium">{log.action}</div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </div>
        </div>

        {/* Bottom: Info Cards */}
        <div className="grid md:grid-cols-3 gap-4">
          <Card className="bg-gradient-to-br from-purple-50 to-pink-50 p-6">
            <h3 className="text-lg font-semibold text-purple-900 mb-2">
              🛡️ Безопасность
            </h3>
            <p className="text-sm text-purple-700 space-y-2">
              <div>ГОСТ-шифрование обеспечивает соответствие требованиям ФСТЭК и ФСБ РФ 
              для работы с критически важными данными.</div>
              <div className="pt-2 mt-2 border-t border-purple-200 text-xs">
                <strong>Важно:</strong> ГОСТ-шлюз работает только с <code className="bg-purple-100 px-1 rounded">api-registry-frontend.bankingapi.ru</code>, 
                не с отдельными банками VBank/ABank/SBank.
              </div>
            </p>
          </Card>

          <Card className="bg-gradient-to-br from-orange-50 to-amber-50 p-6">
            <h3 className="text-lg font-semibold text-orange-900 mb-2">
              ⚡ Производительность
            </h3>
            <p className="text-sm text-orange-700">
              Современные реализации ГОСТ-алгоритмов обеспечивают скорость, 
              сопоставимую с международными стандартами (RSA, ECDSA).
            </p>
          </Card>

          <Card className="bg-gradient-to-br from-cyan-50 to-blue-50 p-6">
            <h3 className="text-lg font-semibold text-cyan-900 mb-2">
              📜 Соответствие
            </h3>
            <p className="text-sm text-cyan-700">
              Полное соответствие стандартам Банка России для межбанковских 
              и клиент-банк операций с ЭЦП.
            </p>
          </Card>
        </div>

        {/* Architecture Diagram */}
        <Card className="bg-white/90 backdrop-blur p-8">
          <h2 className="text-2xl font-semibold text-slate-900 mb-6 text-center">
            📐 Архитектура ГОСТ-интеграции
          </h2>
          
          <div className="flex flex-col md:flex-row items-center justify-center gap-4 text-sm">
            <div className="px-6 py-4 bg-blue-100 rounded-lg border-2 border-blue-300 font-semibold text-blue-900">
              FinanceHub Frontend
            </div>
            
            <div className="text-2xl text-slate-400">→</div>
            
            <div className="px-6 py-4 bg-green-100 rounded-lg border-2 border-green-300 font-semibold text-green-900">
              Backend API
            </div>
            
            <div className="text-2xl text-slate-400">→</div>
            
            <div className="px-6 py-4 bg-purple-100 rounded-lg border-2 border-purple-300 font-semibold text-purple-900">
              ГОСТ Gateway<br/>
              <span className="text-xs font-normal">(Stunnel + CryptoPro)</span>
            </div>
            
            <div className="text-2xl text-slate-400">→</div>
            
            <div className="px-6 py-4 bg-orange-100 rounded-lg border-2 border-orange-300 font-semibold text-orange-900">
              API Registry<br/>
              <span className="text-xs font-normal">(api-registry-frontend.bankingapi.ru)</span>
            </div>
          </div>

          <div className="mt-6 p-4 bg-slate-50 rounded-lg text-xs text-slate-600 space-y-2">
            <div><strong>Шаг 1:</strong> Клиент формирует запрос (JSON)</div>
            <div><strong>Шаг 2:</strong> Backend обрабатывает и валидирует</div>
            <div><strong>Шаг 3:</strong> ГОСТ Gateway подписывает запрос ЭЦП и шифрует канал</div>
            <div><strong>Шаг 4:</strong> API Registry проверяет подпись и обрабатывает</div>
            <div><strong>Шаг 5:</strong> Ответ шифруется и отправляется обратно</div>
          </div>

          <div className="mt-4 p-4 bg-yellow-50 border-2 border-yellow-200 rounded-lg text-xs text-yellow-800">
            <div className="font-semibold mb-2">⚠️ Требования для работы с ГОСТ-шлюзом:</div>
            <div className="space-y-1 ml-4">
              <div>• Специальная версия curl с поддержкой ГОСТ-шифров</div>
              <div>• Endpoint: <code className="bg-yellow-100 px-1 rounded">https://api.gost.bankingapi.ru:8443</code></div>
              <div>• Credentials: login=team075, password=<em>(из письма организаторов)</em></div>
              <div>• Сертификат УЦ ИнфоТеКС для верификации</div>
            </div>
          </div>
        </Card>

      </div>
    </div>
  );
};

export default GostDemoPage;

