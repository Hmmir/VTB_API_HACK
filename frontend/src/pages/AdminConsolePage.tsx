import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Card from '../components/common/Card';
import Button from '../components/common/Button';

interface SystemStat {
  users: number;
  banks: number;
  accounts: number;
  transactions: number;
}

interface Transfer {
  id: string;
  from_account_id: string;
  to_account_id: string;
  amount: number;
  status: string;
  created_at: string;
  description?: string;
  type?: 'internal' | 'interbank';
  payment_id?: string;
}

export default function AdminConsolePage() {
  const [activeTab, setActiveTab] = useState<'stats' | 'transfers' | 'users' | 'settings'>('stats');
  const [stats, setStats] = useState<SystemStat | null>(null);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [keyRate, setKeyRate] = useState('16.0');
  const [saving, setSaving] = useState(false);
  const [loadingTransfers, setLoadingTransfers] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    if (activeTab === 'transfers') {
      loadTransfers();
    }
  }, [activeTab]);

  const loadStats = async () => {
    try {
      // Загружаем реальную статистику из БД
      const response = await fetch('/api/v1/system/admin-stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setStats({
          users: data.users || 0,
          banks: data.banks || 3,
          accounts: data.accounts || 0,
          transactions: data.transactions || 0,
        });
      } else {
        // Fallback to defaults
        setStats({ users: 0, banks: 3, accounts: 0, transactions: 0 });
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
      setStats({ users: 0, banks: 3, accounts: 0, transactions: 0 });
    }
  };

  const loadTransfers = async () => {
    setLoadingTransfers(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      // Загружаем оба типа переводов: internal и interbank
      const [internalRes, interbankRes] = await Promise.all([
        fetch('/api/v1/payments/transfers/internal', { headers }).catch(() => ({ ok: false })),
        fetch('/api/v1/payments/transfers/interbank', { headers }).catch(() => ({ ok: false }))
      ]);
      
      const allTransfers: Transfer[] = [];
      
      if (internalRes.ok) {
        const internalData = await internalRes.json();
        const internalTransfers = (Array.isArray(internalData) ? internalData : []).map((t: any) => ({
          ...t,
          type: 'internal',
          id: t.payment_id || t.id
        }));
        allTransfers.push(...internalTransfers);
      }
      
      if (interbankRes.ok) {
        const interbankData = await interbankRes.json();
        const interbankTransfers = (Array.isArray(interbankData) ? interbankData : []).map((t: any) => ({
          ...t,
          type: 'interbank'
        }));
        allTransfers.push(...interbankTransfers);
      }
      
      // Сортируем по дате (новые первые)
      allTransfers.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      
      setTransfers(allTransfers);
    } catch (error) {
      console.error('Failed to load transfers:', error);
      setTransfers([]);
    } finally {
      setLoadingTransfers(false);
    }
  };

  const saveKeyRate = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/v1/key-rate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rate: parseFloat(keyRate) })
      });
      if (response.ok) {
        alert('✅ Ключевая ставка сохранена!');
      }
    } catch (error) {
      console.error('Failed to save key rate:', error);
      alert('❌ Ошибка сохранения ставки');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-white/20 bg-gradient-to-br from-roseflare/5 via-background to-background">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex items-center gap-4 mb-4">
            <Link
              to="/"
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/30 bg-white/60 hover:bg-white/80 transition-all text-ink"
            >
              ←
            </Link>
            <h1 className="text-4xl font-display text-ink">
              Admin Console
            </h1>
          </div>
          <p className="text-ink/60 text-lg">
            Системная статистика и управление платформой
          </p>
        </div>
      </div>

        {/* Tabs */}
        <div className="border-b border-border/40 bg-surface/30">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex gap-1">
              {['stats', 'transfers', 'users', 'settings'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab as any)}
                  className={`px-6 py-4 font-medium transition-all duration-300 border-b-2 ${
                    activeTab === tab
                      ? 'border-accent text-accent'
                      : 'border-transparent text-text-secondary hover:text-text hover:border-border'
                  }`}
                >
                  {tab === 'stats' && '📊 Статистика'}
                  {tab === 'transfers' && '💸 Переводы'}
                  {tab === 'users' && '👥 Пользователи'}
                  {tab === 'settings' && '⚙️ Настройки'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto px-6 py-8">
          {activeTab === 'stats' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold mb-6">Системная статистика</h2>

              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="p-6 bg-gradient-to-br from-primary-100/30 via-white/70 to-white/60 border-primary-200/30">
                  <div className="text-4xl mb-3">👥</div>
                  <div className="text-3xl font-bold mb-1">{stats?.users || 0}</div>
                  <div className="text-sm text-ink/60">Пользователей</div>
                </Card>

                <Card className="p-6 bg-gradient-to-br from-primary-200/30 via-white/70 to-white/60 border-primary-300/30">
                  <div className="text-4xl mb-3">🏦</div>
                  <div className="text-3xl font-bold mb-1">{stats?.banks || 0}</div>
                  <div className="text-sm text-ink/60">Партнёрских банков</div>
                </Card>

                <Card className="p-6 bg-gradient-to-br from-glow/20 via-white/70 to-white/60 border-glow/30">
                  <div className="text-4xl mb-3">💰</div>
                  <div className="text-3xl font-bold mb-1">{stats?.accounts || 0}</div>
                  <div className="text-sm text-ink/60">Подключённых счетов</div>
                </Card>

                <Card className="p-6 bg-gradient-to-br from-roseflare/15 via-white/70 to-white/60 border-roseflare/30">
                  <div className="text-4xl mb-3">💸</div>
                  <div className="text-3xl font-bold mb-1">{stats?.transactions || 0}</div>
                  <div className="text-sm text-ink/60">Транзакций</div>
                </Card>
              </div>

              {/* Bank Capital Section */}
              <Card className="p-8">
                <h3 className="text-xl font-bold mb-6">Капитал партнёрских банков</h3>
                <div className="text-sm text-ink/60 mb-4">
                  Финансовые показатели и нормативы достаточности капитала банков-партнёров
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    { bank: 'Virtual Bank', capital: '15 млрд ₽', ratio: '15.00%', status: 'Отличный' },
                    { bank: 'Awesome Bank', capital: '12 млрд ₽', ratio: '15.00%', status: 'Отличный' },
                    { bank: 'Smart Bank', capital: '10 млрд ₽', ratio: '15.38%', status: 'Отличный' },
                  ].map((item) => (
                    <div key={item.bank} className="rounded-lg border border-white/30 bg-white/60 p-4">
                      <div className="text-sm font-semibold text-ink mb-2">🏦 {item.bank}</div>
                      <div className="space-y-1 text-xs text-ink/70">
                        <div className="flex justify-between">
                          <span>Капитал:</span>
                          <span className="font-medium text-ink">{item.capital}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>CAR:</span>
                          <span className="font-medium text-primary-600">{item.ratio}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Статус:</span>
                          <span className="font-medium text-primary-700">{item.status}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* System Health */}
              <Card className="p-6">
                <h3 className="text-xl font-bold mb-4">Состояние системы</h3>
                <div className="space-y-3">
                  {[
                    { name: 'API Backend', status: 'online', uptime: '99.9%' },
                    { name: 'Database', status: 'online', uptime: '99.8%' },
                    { name: 'Redis Cache', status: 'online', uptime: '100%' },
                    { name: 'GOST Gateway', status: 'ready', uptime: 'N/A' },
                  ].map((service) => (
                    <div key={service.name} className="flex items-center justify-between p-3 rounded-lg bg-surface/50">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${
                          service.status === 'online' ? 'bg-success animate-pulse' : 'bg-warning'
                        }`} />
                        <span className="font-medium">{service.name}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-text-secondary">Uptime: {service.uptime}</span>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          service.status === 'online'
                            ? 'bg-success/10 text-success'
                            : 'bg-warning/10 text-warning'
                        }`}>
                          {service.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}

          {activeTab === 'transfers' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Межбанковские переводы</h2>
                <Button onClick={loadTransfers} disabled={loadingTransfers}>
                  {loadingTransfers ? 'Загрузка...' : 'Обновить'}
                </Button>
              </div>

              {loadingTransfers ? (
                <div className="text-center py-12 text-text-secondary">
                  Загрузка переводов...
                </div>
              ) : transfers.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">ID</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Тип</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">От</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Кому</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Сумма</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Статус</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Дата</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transfers.map((transfer) => (
                        <tr key={transfer.id} className="border-b border-border/30 hover:bg-surface/30 transition">
                          <td className="px-4 py-3 text-sm text-text font-mono">{transfer.id.slice(0, 8)}</td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              transfer.type === 'internal' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
                            }`}>
                              {transfer.type === 'internal' ? 'Внутренний' : 'Межбанк'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-text">{transfer.from_account_id}</td>
                          <td className="px-4 py-3 text-sm text-text">{transfer.to_account_id}</td>
                          <td className="px-4 py-3 text-sm text-text font-mono">
                            {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(transfer.amount)}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              transfer.status === 'completed' ? 'bg-green-100 text-green-800' :
                              transfer.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {transfer.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-text-secondary">
                            {new Date(transfer.created_at).toLocaleString('ru-RU')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <Card className="text-center py-16">
                  <div className="text-6xl mb-4">💸</div>
                  <p className="text-text-secondary mb-4">Нет переводов</p>
                  <p className="text-sm text-text-secondary max-w-md mx-auto">
                    Здесь будет отображаться история всех межбанковских переводов
                  </p>
                </Card>
              )}
            </div>
          )}

          {activeTab === 'users' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Управление пользователями</h2>
                <Button>+ Создать пользователя</Button>
              </div>

              <Card className="text-center py-16">
                <div className="text-6xl mb-4">👥</div>
                <p className="text-text-secondary mb-4">Функция в разработке</p>
                <p className="text-sm text-text-secondary max-w-md mx-auto">
                  Здесь будет интерфейс для управления пользователями
                </p>
              </Card>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold mb-6">Системные настройки</h2>

              <Card className="p-6">
                <h3 className="text-lg font-bold mb-4">Ключевая ставка ЦБ</h3>
                <div className="flex items-center gap-4">
                  <input
                    type="number"
                    step="0.1"
                    value={keyRate}
                    onChange={(e) => setKeyRate(e.target.value)}
                    className="px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                    placeholder="Ставка %"
                  />
                  <Button onClick={saveKeyRate} disabled={saving}>
                    {saving ? 'Сохранение...' : 'Сохранить'}
                  </Button>
                </div>
                <p className="text-sm text-text-secondary mt-2">
                  Текущая ключевая ставка: {keyRate}%
                </p>
              </Card>

              <Card className="p-6">
                <h3 className="text-lg font-bold mb-4">Банковский капитал</h3>
                <div className="flex items-center gap-4">
                  <input
                    type="text"
                    defaultValue="1000000000"
                    className="px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent flex-1"
                    placeholder="Капитал в рублях"
                  />
                  <Button>Обновить</Button>
                </div>
                <p className="text-sm text-text-secondary mt-2">
                  Текущий капитал: 1 000 000 000 ₽
                </p>
              </Card>

              <Card className="p-6">
                <h3 className="text-lg font-bold mb-4">ГОСТ-шлюз</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-surface/50">
                    <span>Статус ГОСТ-режима</span>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" defaultChecked />
                      <div className="w-11 h-6 bg-surface peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-accent rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                    </label>
                  </div>
                  <p className="text-sm text-text-secondary">
                    Включите для активации криптографического шлюза ГОСТ Р 34.10-2012
                  </p>
                </div>
              </Card>
            </div>
          )}
        </div>
    </div>
  );
}

