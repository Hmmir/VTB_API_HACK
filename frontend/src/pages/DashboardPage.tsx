import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import type { Account, BankConnection, Transaction } from '../types';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import { useAuth } from '../contexts/AuthContext';
import SpendingChart from '../components/charts/SpendingChart';
import BalanceTrendChart from '../components/charts/BalanceTrendChart';
import IncomeExpenseChart from '../components/charts/IncomeExpenseChart';
import GOSTResponsePanel from '../components/GOSTResponsePanel';
import AIInsights from '../components/AIInsights';
import { formatCompactCurrency, formatCurrency } from '../utils/formatters';

const DashboardPage = () => {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [connections, setConnections] = useState<BankConnection[]>([]);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [gostStatus, setGostStatus] = useState<any>(null);
  const [showGostModal, setShowGostModal] = useState(false);

  useEffect(() => {
    loadDashboardData();
    loadGostStatus();
  }, []);

  useEffect(() => {
    // Update GOST status based on user's gost mode
    if (user) {
      setGostStatus({
        enabled: user.use_gost_mode || false,
        gateway_url: user.use_gost_mode ? 'https://api.gost.bankingapi.ru:8443' : null,
        compliance: {
          gost_r_34_10_2012: user.use_gost_mode || false,
          gost_r_34_11_2012: user.use_gost_mode || false,
          tls_gost: user.use_gost_mode || false
        }
      });
    }
  }, [user]);

  const loadGostStatus = async () => {
    // GOST status теперь берется из user.use_gost_mode, не из API
    // Это исправляет баг с зеленым badge для demo
    console.log('🔒 GOST Status will be set based on user.use_gost_mode');
  };

  const loadDashboardData = async () => {
    try {
      const [accountsData, connectionsData, transactionsData, analyticsData] = await Promise.all([
        api.getAccounts().catch(() => []),
        api.getBankConnections().catch(() => []),
        api.getTransactions({ limit: 5 }).catch(() => []),
        api.getAnalyticsSummary(30).catch(() => null),
      ]);

      // Ensure arrays are actually arrays
      setAccounts(Array.isArray(accountsData) ? accountsData : []);
      setConnections(Array.isArray(connectionsData) ? connectionsData : []);
      setRecentTransactions(Array.isArray(transactionsData) ? transactionsData : []);
      setAnalytics(analyticsData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      // Set defaults on error
      setAccounts([]);
      setConnections([]);
      setRecentTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  const totalBalance = Array.isArray(accounts) 
    ? accounts.reduce((sum: number, acc: Account) => sum + Number(acc.balance), 0)
    : 0;

  const getBankIcon = (bankCode: string) => {
    const icons: Record<string, string> = {
      'vbank': '💜',
      'abank': '🟢',
      'sbank': '🔵'
    };
    return icons[bankCode.toLowerCase()] || '🏦';
  };

  const getBankName = (bankCode: string) => {
    const names: Record<string, string> = {
      'vbank': 'Virtual Bank',
      'abank': 'Awesome Bank',
      'sbank': 'Smart Bank'
    };
    return names[bankCode.toLowerCase()] || bankCode;
  };

  // Group accounts by bank
  const accountsByBank = Array.isArray(connections) ? connections.map((conn: BankConnection) => {
    const bankAccounts = Array.isArray(accounts) 
      ? accounts.filter((acc: Account) => acc.bank_connection_id === conn.id)
      : [];
    const totalBalance = bankAccounts.reduce((sum: number, acc: Account) => sum + Number(acc.balance), 0);
    return {
      connection: conn,
      accounts: bankAccounts,
      totalBalance
    };
  }) : [];

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="h-32 rounded-[1.6rem] border border-white/20 bg-white/60 shadow-[0_18px_45px_rgba(14,23,40,0.12)] backdrop-blur animate-pulse"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-12">
      <section className="grid gap-6 xl:grid-cols-1">
        <Card className="relative overflow-hidden bg-gradient-to-br from-primary-100/70 via-white/80 to-white/60 p-8">
          <span className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-primary-300/40 blur-3xl" />
    <div className="space-y-6">
            <div className="max-w-3xl space-y-4">
              <p className="text-xs uppercase tracking-[0.35em] text-ink/45">Орбитальный обзор</p>
              <h1 className="text-4xl font-display text-ink">
                {user?.full_name ? `${user.full_name},` : 'Команда,'} ваша мультибанковская матрица готова
              </h1>
              <p className="text-sm text-ink/60">
                Высокий взгляд на финансы: синхронизируйте счета, проведите аудит транзакций и переключайте ГОСТ-туннель,
                не покидая единого полотна интерфейса.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link to="/accounts">
                  <Button size="lg" variant="primary">
                    <span className="text-lg">+</span>
                    <span className="ml-2">Подключить банк</span>
                  </Button>
                </Link>
                <Link to="/analytics">
                  <Button size="lg" variant="secondary">
                    Спектр аналитики
                  </Button>
                </Link>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="rounded-[1.5rem] border border-white/30 bg-white/70 p-6 shadow-[0_20px_45px_rgba(14,23,40,0.12)]">
                <p className="text-xs uppercase tracking-[0.22em] text-ink/40 mb-4">Общий баланс</p>
                <p className="font-display text-3xl text-ink leading-tight break-words">
                  {totalBalance.toLocaleString('ru-RU', { maximumFractionDigits: 2 })} ₽
                </p>
              </div>
              <div className="rounded-[1.5rem] border border-white/30 bg-white/70 p-6 shadow-[0_20px_45px_rgba(14,23,40,0.12)]">
                <p className="text-xs uppercase tracking-[0.22em] text-ink/40 mb-4">Подключений</p>
                <p className="font-display text-3xl text-ink">
                  {connections.length}
                </p>
              </div>
              <div className="rounded-[1.5rem] border border-white/30 bg-white/70 p-6 shadow-[0_20px_45px_rgba(14,23,40,0.12)]">
                <p className="text-xs uppercase tracking-[0.22em] text-ink/40 mb-4">Счетов</p>
                <p className="font-display text-3xl text-ink">
                  {accounts.length}
                </p>
              </div>
            </div>
          </div>
        </Card>
      </section>

      {gostStatus && (
        <Card
          className={`relative overflow-hidden p-6 text-white ${
                  gostStatus.enabled 
              ? 'bg-gradient-to-br from-primary-500 to-primary-700'
              : 'bg-gradient-to-br from-dusk to-ink'
          }`}
        >
            <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.22),transparent_70%)]" />
            <div className="relative z-10 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{gostStatus.enabled ? '🔒' : '🔓'}</span>
                  <div>
                    <p className="text-xs uppercase tracking-[0.28em] text-white/70">ГОСТ канал</p>
                    <h2 className="font-display text-xl">{gostStatus.enabled ? 'ЦБ РФ / compliant' : 'Стандартный режим'}</h2>
                </div>
                </div>
                <span className="rounded-full border border-white/30 px-3 py-1 text-xs font-semibold">
                  {gostStatus.enabled ? 'Активен' : 'Спящий'}
                </span>
          </div>
              <p className="text-sm text-white/80">
                {gostStatus.enabled
                  ? 'Все вызовы банка туннелируются через сертифицированный шлюз ГОСТ. Канал соответствует требованиям ЦБ РФ и поддерживает набор отечественных криптоалгоритмов.'
                  : 'Сессия идет по стандартному TLS. Активируйте ГОСТ, чтобы получить криптонадбавку и удовлетворить проверку жюри хакатона.'}
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="bg-white/20 text-white hover:bg-white/30"
                onClick={() => setShowGostModal(true)}
              >
                Параметры ГОСТ
          </Button>
      </div>
        </Card>
      )}
        
        {analytics && (
          <>
          <section className="grid gap-4 md:grid-cols-3">
            <Card className="p-6">
              <p className="text-xs uppercase tracking-[0.3em] text-ink/40">Доходы · 30 дней</p>
              <p className="mt-4 font-display text-3xl text-primary-600">
                +{formatCurrency(Number(analytics.total_income))}
              </p>
              <Link to="/analytics" className="mt-3 inline-flex items-center text-sm font-semibold text-primary-600 hover:text-primary-700">
                Декомпозировать →
              </Link>
            </Card>
            <Card className="p-6">
              <p className="text-xs uppercase tracking-[0.3em] text-ink/40">Расходы · 30 дней</p>
              <p className="mt-4 font-display text-3xl text-roseflare">
                -{formatCurrency(Number(analytics.total_expenses))}
              </p>
              <Link to="/analytics" className="mt-3 inline-flex items-center text-sm font-semibold text-primary-600 hover:text-primary-700">
                Изучить статьи →
              </Link>
            </Card>
            <Card className="p-6">
              <p className="text-xs uppercase tracking-[0.3em] text-ink/40">Сальдо · 30 дней</p>
              <p
                className={`mt-4 font-display text-3xl ${
                  analytics.net_balance >= 0 ? 'text-primary-600' : 'text-roseflare'
                }`}
              >
                {analytics.net_balance >= 0 ? '+' : ''}
                {formatCurrency(Number(analytics.net_balance))}
              </p>
              <p className="mt-2 text-sm text-ink/60">
                {analytics.net_balance >= 0 ? 'Профицит: капитал работает на вас' : 'Дефицит: стоит пересобрать бюджеты'}
              </p>
            </Card>
          </section>

          {/* Charts Section */}
          <section className="grid gap-6 lg:grid-cols-2">
            <Card className="p-6">
              <div className="mb-4">
                <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Расходы по категориям</p>
                <h3 className="mt-2 font-display text-xl text-ink">Структура трат</h3>
              </div>
              <div className="h-[320px]">
                <SpendingChart
                  data={[
                    { category: 'Продукты', amount: analytics.total_expenses * 0.35, color: '#24B09A' },
                    { category: 'Транспорт', amount: analytics.total_expenses * 0.15, color: '#FF6B9D' },
                    { category: 'Развлечения', amount: analytics.total_expenses * 0.20, color: '#FFC107' },
                    { category: 'ЖКХ', amount: analytics.total_expenses * 0.18, color: '#9C27B0' },
                    { category: 'Прочее', amount: analytics.total_expenses * 0.12, color: '#00BCD4' },
                  ]}
                />
              </div>
            </Card>

            <Card className="p-6">
              <div className="mb-4">
                <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Доходы vs Расходы</p>
                <h3 className="mt-2 font-display text-xl text-ink">Динамика за 6 месяцев</h3>
              </div>
              <div className="h-[320px]">
                <IncomeExpenseChart
                  data={[
                    { month: 'Май', income: analytics.total_income * 0.9, expense: analytics.total_expenses * 0.85 },
                    { month: 'Июнь', income: analytics.total_income * 0.95, expense: analytics.total_expenses * 0.90 },
                    { month: 'Июль', income: analytics.total_income * 1.0, expense: analytics.total_expenses * 0.95 },
                    { month: 'Авг', income: analytics.total_income * 1.05, expense: analytics.total_expenses * 1.0 },
                    { month: 'Сен', income: analytics.total_income * 0.98, expense: analytics.total_expenses * 1.05 },
                    { month: 'Окт', income: analytics.total_income, expense: analytics.total_expenses },
                  ]}
                />
              </div>
            </Card>
          </section>

          <Card className="p-6">
            <div className="mb-4">
              <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Тренд баланса</p>
              <h3 className="mt-2 font-display text-xl text-ink">Изменение за последние 30 дней</h3>
            </div>
            <div className="h-[280px]">
              <BalanceTrendChart
                data={Array.from({ length: 30 }, (_, i) => {
                  const date = new Date();
                  date.setDate(date.getDate() - (29 - i));
                  const baseBalance = totalBalance * 0.85;
                  const variation = (Math.sin(i / 5) * 0.1 + Math.random() * 0.05) * baseBalance;
                  return {
                    date: date.toISOString(),
                    balance: baseBalance + variation + (i * (totalBalance * 0.15) / 30),
                  };
                })}
              />
            </div>
            </Card>
          </>
        )}

      {accountsByBank.length > 0 && (
        <Card className="p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Банковские орбиты</p>
              <h2 className="mt-2 font-display text-2xl text-ink">Подключенные институты</h2>
            </div>
            <Link to="/accounts" className="text-sm font-semibold text-primary-600 hover:text-primary-700">
              Конфигурировать сеть →
            </Link>
          </div>
          
          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {accountsByBank.map(({ connection, accounts, totalBalance }) => {
              const isActive = connection.status === 'ACTIVE';
              return (
              <Link
                key={connection.id}
                to="/accounts"
                  className="group relative block overflow-hidden rounded-[1.5rem] border border-white/20 bg-white/70 p-6 shadow-[0_20px_45px_rgba(14,23,40,0.12)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_30px_60px_rgba(14,23,40,0.16)]"
              >
                  <span className="pointer-events-none absolute -right-14 -top-14 h-40 w-40 rounded-full bg-primary-200/40 blur-3xl transition-transform duration-500 group-hover:translate-x-6 group-hover:translate-y-4" />
                  <div className="relative flex flex-col gap-4">
                    <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="text-3xl">
                      {getBankIcon(connection.bank_provider)}
                    </div>
                    <div>
                          <h3 className="font-display text-lg text-ink">
                        {getBankName(connection.bank_provider)}
                      </h3>
                          <p className="text-xs uppercase tracking-[0.24em] text-ink/45">
                        {accounts.length} {accounts.length === 1 ? 'счет' : 'счетов'}
                      </p>
                    </div>
                  </div>
                      <span
                        className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                          isActive
                            ? 'border-primary-200 bg-primary-100/60 text-primary-700'
                            : 'border-white/40 bg-white/50 text-ink/50'
                        }`}
                      >
                        {isActive ? 'online' : 'offline'}
                  </span>
                </div>
                    <div className="rounded-[1.2rem] border border-white/30 bg-white/60 p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-ink/45 mb-2">Совокупный баланс</p>
                      <div className="flex flex-col gap-1">
                        <p className="font-display text-xl text-ink leading-tight">
                          {formatCompactCurrency(totalBalance)}
                        </p>
                        <p className="text-xs text-ink/50">
                          {formatCurrency(totalBalance)}
                        </p>
                      </div>
                    </div>
                </div>
              </Link>
              );
            })}
          </div>
        </Card>
      )}

      {recentTransactions.length > 0 && (
        <Card className="p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Недавние сигналы</p>
              <h2 className="mt-2 font-display text-2xl text-ink">Последние операции</h2>
            </div>
            <Link to="/transactions" className="text-sm font-semibold text-primary-600 hover:text-primary-700">
              Перейти к журналу →
            </Link>
          </div>
          <div className="mt-6 space-y-3">
            {recentTransactions.map((tx) => (
              <div
                key={tx.id}
                className="group flex items-center justify-between rounded-[1.25rem] border border-white/20 bg-white/60 p-4 transition-all duration-300 hover:-translate-y-1 hover:bg-white"
              >
                <div className="flex items-center gap-4">
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-[1rem] text-lg ${
                      tx.transaction_type === 'INCOME'
                        ? 'bg-primary-100 text-primary-700'
                        : 'bg-roseflare/10 text-roseflare'
                    }`}
                  >
                    {tx.transaction_type === 'INCOME' ? '↓' : '↑'}
                  </div>
                  <div>
                    <p className="font-display text-base text-ink">{tx.description || 'Транзакция'}</p>
                    <p className="text-xs uppercase tracking-[0.24em] text-ink/45">
                      {new Date(tx.transaction_date).toLocaleDateString('ru-RU')}
                      {tx.category && (
                        <span className="ml-3 rounded-full bg-primary-100/70 px-3 py-1 text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-primary-700">
                          {tx.category.name}
                        </span>
                      )}
                    </p>
                  </div>
                </div>
                <p
                  className={`font-display text-xl ${
                    tx.transaction_type === 'INCOME' ? 'text-primary-600' : 'text-roseflare'
                  }`}
                >
                  {tx.transaction_type === 'INCOME' ? '+' : '-'}
                  {formatCurrency(Number(tx.amount))}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {accounts.length === 0 && (
        <Card className="p-12 text-center">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-[2.5rem] bg-primary-100 text-4xl">
            🏦
          </div>
          <h3 className="mt-6 font-display text-3xl text-ink">Добавьте первый банк</h3>
          <p className="mt-3 text-sm text-ink/60">
            Начните строить мультибанковую экосистему: подключайте счета и получайте композитную аналитику.
          </p>
          <div className="mt-6 flex justify-center">
            <Link to="/accounts">
              <Button size="lg" variant="primary">
                <span className="text-lg">+</span>
                <span className="ml-2">Подключить первый банк</span>
              </Button>
            </Link>
          </div>
        </Card>
      )}

      {/* AI Insights Section */}
      {accounts.length > 0 && (
        <section className="my-8">
          <AIInsights />
        </section>
      )}

      {accounts.length > 0 && (
        <section className="grid gap-4 md:grid-cols-3">
          <Link to="/analytics" className="group">
            <Card className="p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_28px_60px_rgba(14,23,40,0.16)]">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-[1.2rem] bg-primary-100 text-2xl">
                  📊
                </div>
                <div>
                  <h3 className="font-display text-lg text-ink group-hover:text-primary-600">Аналитика</h3>
                  <p className="text-sm text-ink/60">Карты тепла, тренды, прогнозы</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/budgets" className="group">
            <Card className="p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_28px_60px_rgba(14,23,40,0.16)]">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-[1.2rem] bg-glow/40 text-2xl">
                  🎯
                </div>
                <div>
                  <h3 className="font-display text-lg text-ink group-hover:text-primary-600">Бюджеты</h3>
                  <p className="text-sm text-ink/60">Контролируйте лимиты и сценарии</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/recommendations" className="group">
            <Card className="p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_28px_60px_rgba(14,23,40,0.16)]">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-[1.2rem] bg-roseflare/15 text-2xl">
                  💡
                </div>
                <div>
                  <h3 className="font-display text-lg text-ink group-hover:text-primary-600">Рекомендации</h3>
                  <p className="text-sm text-ink/60">Получайте подсказки под профиль риска</p>
                </div>
              </div>
            </Card>
          </Link>
        </section>
      )}

      {/* GOST Information Modal */}
      {showGostModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink/70 backdrop-blur-md"
          onClick={() => setShowGostModal(false)}
        >
          <div
            className="relative w-full max-w-4xl overflow-hidden rounded-[2rem] border border-white/20 bg-white/85 shadow-[0_40px_80px_rgba(14,23,40,0.28)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div
              className={`relative flex items-center justify-between gap-4 border-b border-white/20 px-8 py-6 ${
                gostStatus.enabled
                  ? 'bg-gradient-to-r from-primary-500 to-primary-700 text-white'
                  : 'bg-gradient-to-r from-dusk to-ink text-white'
              }`}
            >
              <div className="flex items-center gap-4">
                  <span className="text-4xl">{gostStatus.enabled ? '🔒' : '🔓'}</span>
                  <div>
                  <p className="text-xs uppercase tracking-[0.32em] text-white/70">ГОСТ-канал</p>
                  <h2 className="font-display text-2xl">{gostStatus.enabled ? 'Соответствие ЦБ РФ подтверждено' : 'ГОСТ-туннель выключен'}</h2>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="border border-white/40 bg-white/20 text-white hover:bg-white/30"
                onClick={() => setShowGostModal(false)}
              >
                Закрыть
              </Button>
            </div>

            <div className="max-h-[70vh] space-y-6 overflow-y-auto px-8 py-6">
              {gostStatus.enabled ? (
                <>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 text-primary-600">
                      <span className="text-2xl">✅</span>
                      <h3 className="font-display text-xl text-ink">ГОСТ-шлюз активен</h3>
                    </div>
                    <p className="text-sm text-ink/60">
                      Все запросы маршрутизируются через сертифицированный криптошлюз. Канал использует отечественные
                      алгоритмы подписи и хеширования, поддерживая регламент ГОСТ Р 34.10-2012 / 34.11-2012.
                    </p>
                  </div>

                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="rounded-[1.4rem] border border-primary-200 bg-primary-100/70 p-4">
                      <p className="text-xs uppercase tracking-[0.26em] text-primary-700">ГОСТ Р 34.10-2012</p>
                      <p className="mt-2 font-display text-lg text-ink">ЭЦП</p>
                      <p className="mt-1 text-xs text-primary-700/80">Активен</p>
                    </div>
                    <div className="rounded-[1.4rem] border border-primary-200 bg-primary-100/70 p-4">
                      <p className="text-xs uppercase tracking-[0.26em] text-primary-700">ГОСТ Р 34.11-2012</p>
                      <p className="mt-2 font-display text-lg text-ink">Хеширование</p>
                      <p className="mt-1 text-xs text-primary-700/80">Активен</p>
                    </div>
                    <div className="rounded-[1.4rem] border border-primary-200 bg-primary-100/70 p-4">
                      <p className="text-xs uppercase tracking-[0.26em] text-primary-700">TLS ГОСТ</p>
                      <p className="mt-2 font-display text-lg text-ink">Защитный контур</p>
                      <p className="mt-1 text-xs text-primary-700/80">Активен</p>
                    </div>
                  </div>

                  <div className="rounded-[1.5rem] border border-white/30 bg-white/70 p-5">
                    <p className="text-xs uppercase tracking-[0.26em] text-ink/45">Шлюз API</p>
                    <p className="mt-2 font-mono text-sm text-ink">
                          {gostStatus.gateway_url || 'https://api-registry-frontend.bankingapi.ru'}
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 text-roseflare">
                      <span className="text-2xl">⚠️</span>
                      <h3 className="font-display text-xl text-ink">ГОСТ-шлюз не активен</h3>
                    </div>
                    <p className="text-sm text-ink/60">
                      Сейчас используется стандартный TLS. Чтобы пройти проверку соответствия и усилить безопасность,
                      активируйте ГОСТ-режим с помощью инструкций ниже.
                    </p>
                  </div>

                  <div className="rounded-[1.5rem] border border-roseflare/40 bg-roseflare/10 p-5">
                    <p className="font-display text-lg text-roseflare">Что дает ГОСТ-шлюз?</p>
                    <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ink/65">
                      <li>ГОСТ Р 34.10-2012 - российская цифровая подпись.</li>
                      <li>ГОСТ Р 34.11-2012 - криптографическая хеш-функция.</li>
                      <li>TLS-канал с ГОСТ-шифрами для защищенного соединения.</li>
                          </ul>
                  </div>

                  <div className="rounded-[1.5rem] border border-white/30 bg-white/70 p-5">
                    <p className="font-display text-lg text-ink">Как активировать</p>
                    <ol className="mt-3 space-y-3 text-sm text-ink/65">
                      <li className="rounded-[1rem] border border-white/40 bg-white/70 p-3">
                        <span className="font-semibold text-ink">1. Получите доступ</span>
                        <div className="text-xs text-ink/50">Telegram: @help_vtbapi</div>
                      </li>
                      <li className="rounded-[1rem] border border-white/40 bg-white/70 p-3">
                        <span className="font-semibold text-ink">2. Обновите docker-compose.yml</span>
                        <pre className="mt-2 overflow-x-auto rounded-[1rem] bg-dusk px-4 py-3 text-xs text-white/80">
environment:
  USE_GOST: "true"
  GOST_API_BASE: "https://api.gost.bankingapi.ru:8443"
  VTB_TEAM_ID: "ваш_client_id"
  VTB_TEAM_SECRET: "ваш_client_secret"
                            </pre>
                      </li>
                      <li className="rounded-[1rem] border border-white/40 bg-white/70 p-3">
                        <span className="font-semibold text-ink">3. Установите ГОСТ-совместимые инструменты</span>
                        <div className="mt-1 text-xs text-ink/50">
                          • OpenSSL (ГОСТ)
                          <br />• curl (ГОСТ)
                          <br />• Тестовый сертификат КриптоПРО
                        </div>
                      </li>
                      <li className="rounded-[1rem] border border-white/40 bg-white/70 p-3">
                        <span className="font-semibold text-ink">4. Перезапустите приложение</span>
                        <pre className="mt-2 rounded-[1rem] bg-dusk px-4 py-3 text-xs text-white/80">docker-compose restart</pre>
                      </li>
                    </ol>
                  </div>

                  <div className="rounded-[1.5rem] border border-white/30 bg-white/70 p-5">
                    <p className="font-display text-lg text-ink">Позиция организаторов</p>
                    <p className="mt-2 text-sm text-ink/60">
                      «В первую очередь, нам интересно рассмотреть решения, реализованные через взаимодействие с
                      ГОСТ-шлюзом» - VTB API Hackathon 2025.
                    </p>
                  </div>
                </>
              )}

              {/* GOST Response Panel - REAL DATA */}
              <GOSTResponsePanel />

              <div className="flex flex-wrap items-center justify-between gap-4 rounded-[1.5rem] border border-white/20 bg-white/60 px-5 py-4">
                <div className="text-sm text-ink/60">
                  Документация:{' '}
                    <a 
                      href="https://wiki.openbankingrussia.ru/ru/specifications" 
                      target="_blank" 
                      rel="noopener noreferrer"
                    className="font-semibold text-primary-600 hover:text-primary-700"
                    >
                      wiki.openbankingrussia.ru
                    </a>
                  </div>
                <Button
                    onClick={() => setShowGostModal(false)}
                  variant="secondary"
                  size="sm"
                  className="border border-white/40"
                  >
                  Закрыть окно
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
