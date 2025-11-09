import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import { api } from '../services/api';
import { formatCurrency } from '../utils/formatters';
import toast from 'react-hot-toast';

interface ConsentItem {
  id: string;
  user_id: number;
  partner_bank_name: string;
  scopes: string[];
  status: string;
  valid_until: string;
  granted_at: string;
}

interface AgreementItem {
  id: string;
  user_id: number;
  product_type: string;
  status: string;
  amount: number;
  interest_rate: number;
  term_months: number;
  created_at: string;
}

interface ClientInfo {
  id: number;
  email: string;
  full_name: string;
  created_at: string;
  total_accounts: number;
  total_balance: number;
  active_connections: number;
}

interface ProductInfo {
  id?: number;
  productId?: string;
  name?: string;
  productName?: string;
  type?: string;
  productType?: string;
  min_amount?: number;
  minAmount?: number;
  max_amount?: number;
  maxAmount?: number;
  interest_rate?: number;
  interestRate?: number;
  term_months?: number;
  termMonths?: number;
  is_active?: boolean;
  bank_name?: string;
  bank_code?: string;
}

interface BankStats {
  total_clients: number;
  total_accounts: number;
  total_balance: number;
  total_transactions: number;
  active_consents: number;
  active_agreements: number;
}

export default function BankerConsolePage() {
  const [activeTab, setActiveTab] = useState<'stats' | 'consents' | 'agreements' | 'products' | 'clients'>('stats');
  const [consents, setConsents] = useState<ConsentItem[]>([]);
  const [agreements, setAgreements] = useState<AgreementItem[]>([]);
  const [clients, setClients] = useState<ClientInfo[]>([]);
  const [products, setProducts] = useState<ProductInfo[]>([]);
  const [stats, setStats] = useState<BankStats | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    switch (activeTab) {
      case 'stats':
        loadStats();
        break;
      case 'consents':
        loadConsents();
        break;
      case 'agreements':
        loadAgreements();
        break;
      case 'products':
        loadProducts();
        break;
      case 'clients':
        loadClients();
        break;
    }
  }, [activeTab]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await api.get('/banker/statistics');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadConsents = async () => {
    setLoading(true);
    try {
      const response = await api.get('/banker/consents');
      setConsents(response.data.consents || []);
    } catch (error) {
      console.error('Failed to load consents:', error);
      setConsents([]);
    } finally {
      setLoading(false);
    }
  };

  const loadAgreements = async () => {
    setLoading(true);
    try {
      const response = await api.get('/products/agreements');
      const agreementsData = response.data.agreements || response.data || [];
      setAgreements(Array.isArray(agreementsData) ? agreementsData : []);
    } catch (error) {
      console.error('Failed to load agreements:', error);
      setAgreements([]);
    } finally {
      setLoading(false);
    }
  };

  const loadProducts = async () => {
    setLoading(true);
    try {
      const response = await api.get('/products');
      // API возвращает { products: [...], total: N }
      const productsData = response.data.products || response.data || [];
      setProducts(Array.isArray(productsData) ? productsData : []);
    } catch (error) {
      console.error('Failed to load products:', error);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const loadClients = async () => {
    setLoading(true);
    try {
      const response = await api.get('/banker/clients');
      setClients(response.data.clients || []);
    } catch (error) {
      console.error('Failed to load clients:', error);
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  // Removed: createProduct and toggleProductStatus functions (not needed for viewing bank products)

  const revokeConsent = async (consentId: string) => {
    if (!confirm('Отозвать согласие?')) return;
    try {
      await api.delete(`/consents/${consentId}`);
      toast.success('✅ Согласие отозвано');
      loadConsents();
    } catch (error: any) {
      console.error('Failed to revoke consent:', error);
      toast.error(error?.response?.data?.detail || 'Ошибка отзыва согласия');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-white/20 bg-gradient-to-br from-primary-100/30 via-background to-background">
        <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16 py-12">
          <div className="flex items-center gap-4 mb-4">
            <Link
              to="/"
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/30 bg-white/60 hover:bg-white/80 transition-all text-ink"
            >
              ←
            </Link>
            <h1 className="text-4xl font-display text-ink">
              🏦 Banker Console
            </h1>
          </div>
          <p className="text-ink/60 text-lg">
            Управление клиентами, продуктами и аналитикой банка
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border/40 bg-surface/30">
        <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16">
          <div className="flex gap-1 overflow-x-auto">
            {[
              { id: 'stats', label: '📊 Статистика' },
              { id: 'clients', label: '👥 Клиенты' },
              { id: 'products', label: '💳 Продукты' },
              { id: 'agreements', label: '📋 Договоры' },
              { id: 'consents', label: '🔒 Согласия' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-6 py-4 font-medium transition-all duration-300 border-b-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-accent text-accent'
                    : 'border-transparent text-text-secondary hover:text-text hover:border-border'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16 py-8">
        {loading && (
          <div className="flex justify-center py-12">
            <div className="text-text-secondary">Загрузка...</div>
          </div>
        )}

        {/* Statistics Tab */}
        {activeTab === 'stats' && !loading && (
          <div className="space-y-6">
            {!stats ? (
              <Card>
                <div className="p-12 text-center text-text-secondary">
                  Нет данных для отображения
                </div>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Card>
                  <div className="p-6">
                    <div className="text-sm text-text-secondary mb-2">Всего клиентов</div>
                    <div className="text-3xl font-bold text-ink">{stats.total_clients || 0}</div>
                  </div>
                </Card>

                <Card>
                  <div className="p-6">
                    <div className="text-sm text-text-secondary mb-2">Счетов открыто</div>
                    <div className="text-3xl font-bold text-ink">{stats.total_accounts || 0}</div>
                  </div>
                </Card>

                <Card>
                  <div className="p-6">
                    <div className="text-sm text-text-secondary mb-2">Общий баланс</div>
                    <div className="text-3xl font-bold text-ink">{formatCurrency(stats.total_balance || 0)}</div>
                  </div>
                </Card>

                <Card>
                  <div className="p-6">
                    <div className="text-sm text-text-secondary mb-2">Транзакций</div>
                    <div className="text-3xl font-bold text-ink">{stats.total_transactions || 0}</div>
                  </div>
                </Card>

                <Card>
                  <div className="p-6">
                    <div className="text-sm text-text-secondary mb-2">Активных согласий</div>
                    <div className="text-3xl font-bold text-ink">{stats.active_consents || 0}</div>
                  </div>
                </Card>

                <Card>
                  <div className="p-6">
                    <div className="text-sm text-text-secondary mb-2">Договоров</div>
                    <div className="text-3xl font-bold text-ink">{stats.active_agreements || 0}</div>
                  </div>
                </Card>
              </div>
            )}
          </div>
        )}

        {/* Clients Tab */}
        {activeTab === 'clients' && !loading && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-ink">Клиенты банка</h2>
              <div className="text-sm text-text-secondary">Всего: {clients.length}</div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">ID</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Email</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Имя</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Счетов</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Баланс</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Подключений</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Дата регистрации</th>
                  </tr>
                </thead>
                <tbody>
                  {clients.map((client) => (
                    <tr key={client.id} className="border-b border-border/30 hover:bg-surface/30 transition">
                      <td className="px-4 py-3 text-sm text-text">{client.id}</td>
                      <td className="px-4 py-3 text-sm text-text">{client.email}</td>
                      <td className="px-4 py-3 text-sm text-text">{client.full_name || '—'}</td>
                      <td className="px-4 py-3 text-sm text-text">{client.total_accounts}</td>
                      <td className="px-4 py-3 text-sm text-text font-mono">{formatCurrency(client.total_balance)}</td>
                      <td className="px-4 py-3 text-sm text-text">{client.active_connections}</td>
                      <td className="px-4 py-3 text-sm text-text-secondary">
                        {new Date(client.created_at).toLocaleDateString('ru-RU')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {clients.length === 0 && (
              <div className="text-center py-12 text-text-secondary">
                Нет данных о клиентах
              </div>
            )}
          </div>
        )}

        {/* Products Tab */}
        {activeTab === 'products' && !loading && (
          <div className="space-y-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-ink">Банковские продукты</h2>
              <div className="text-sm text-text-secondary">Всего: {products.length}</div>
            </div>

            {products.length === 0 ? (
              <Card>
                <div className="p-12 text-center">
                  <p className="text-text-secondary">
                    Продукты не найдены. Подключите банки для просмотра их продуктов.
                  </p>
                </div>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {products.map((product, idx) => {
                  const productName = product.productName || product.name || 'Продукт';
                  const productType = product.productType || product.type || '—';
                  const interestRate = product.interestRate || product.interest_rate;
                  const minAmount = product.minAmount || product.min_amount;
                  const maxAmount = product.maxAmount || product.max_amount;
                  const termMonths = product.termMonths || product.term_months;
                  const productId = product.productId || product.id || idx;

                  return (
                    <Card key={productId}>
                      <div className="p-6">
                        <div className="mb-4">
                          <h3 className="text-lg font-semibold text-ink">{productName}</h3>
                          <p className="text-sm text-text-secondary">{productType}</p>
                          {product.bank_name && (
                            <p className="text-xs text-text-secondary mt-1">
                              🏦 {product.bank_name}
                            </p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-text-secondary">Ставка:</span>
                            <span className="text-text font-semibold">
                              {interestRate != null ? `${Number(interestRate).toFixed(2)}%` : '—'}
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-text-secondary">Сумма:</span>
                            <span className="text-text">
                              {formatCurrency(Number(minAmount) || 0)} - {formatCurrency(Number(maxAmount) || 0)}
                            </span>
                          </div>
                          {termMonths != null && (
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Срок:</span>
                              <span className="text-text">{termMonths} мес.</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Agreements Tab */}
        {activeTab === 'agreements' && !loading && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-ink">Договоры</h2>
              <div className="text-sm text-text-secondary">Всего: {agreements.length}</div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {agreements.map((agreement) => (
                <Card key={agreement.id}>
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-ink">{agreement.product_type}</h3>
                        <p className="text-sm text-text-secondary">ID: {agreement.id}</p>
                      </div>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          agreement.status === 'ACTIVE'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {agreement.status}
                      </span>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-text-secondary">Сумма:</span>
                        <span className="text-text font-mono">{formatCurrency(agreement.amount)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-text-secondary">Ставка:</span>
                        <span className="text-text">{agreement.interest_rate}%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-text-secondary">Срок:</span>
                        <span className="text-text">{agreement.term_months} мес.</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-text-secondary">Создан:</span>
                        <span className="text-text-secondary">
                          {new Date(agreement.created_at).toLocaleDateString('ru-RU')}
                        </span>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {agreements.length === 0 && (
              <div className="text-center py-12 text-text-secondary">
                Нет договоров
              </div>
            )}
          </div>
        )}

        {/* Consents Tab */}
        {activeTab === 'consents' && !loading && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-ink">Согласия клиентов</h2>
              <div className="text-sm text-text-secondary">Всего: {consents.length}</div>
            </div>

            <div className="space-y-4">
              {consents.map((consent) => (
                <Card key={consent.id}>
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-ink">
                          {consent.partner_bank_name}
                        </h3>
                        <p className="text-sm text-text-secondary">ID: {consent.id}</p>
                      </div>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          consent.status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {consent.status}
                      </span>
                    </div>

                    <div className="space-y-2 mb-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-text-secondary">Области доступа:</span>
                        <span className="text-text">{consent.scopes.join(', ')}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-text-secondary">Действует до:</span>
                        <span className="text-text">
                          {new Date(consent.valid_until).toLocaleDateString('ru-RU')}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-text-secondary">Выдано:</span>
                        <span className="text-text-secondary">
                          {new Date(consent.granted_at).toLocaleDateString('ru-RU')}
                        </span>
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => revokeConsent(consent.id)}
                      className="w-full text-red-600 hover:bg-red-50"
                    >
                      Отозвать согласие
                    </Button>
                  </div>
                </Card>
              ))}
            </div>

            {consents.length === 0 && (
              <div className="text-center py-12 text-text-secondary">
                Нет активных согласий
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
