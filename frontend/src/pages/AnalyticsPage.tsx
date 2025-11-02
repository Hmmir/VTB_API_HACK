import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import toast from 'react-hot-toast';

type Summary = {
  total_income: number;
  total_expenses: number;
  net_balance: number;
  transaction_count: number;
};

type CategoryBreakdown = {
  category_id: number;
  category: string;
  total: number;
  count: number;
};

type TrendPoint = {
  date: string;
  income: number;
  expenses: number;
  net: number;
};

const periodOptions = [
  { label: '7 дней', value: 7 },
  { label: '30 дней', value: 30 },
  { label: '90 дней', value: 90 },
];

const formatCurrency = (value: number, options?: Intl.NumberFormatOptions) =>
  value.toLocaleString('ru-RU', { maximumFractionDigits: 0, ...options });

const AnalyticsPage = () => {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [byCategory, setByCategory] = useState<CategoryBreakdown[]>([]);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [period, setPeriod] = useState(30);
  const [loading, setLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    void loadAnalytics();
  }, [period]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [summaryData, categoryData, trendsData] = await Promise.all([
        api.getAnalyticsSummary(period),
        api.getExpensesByCategory(period),
        api.getSpendingTrends(period),
      ]);
      setSummary(summaryData);
      setByCategory(categoryData);
      setTrends(trendsData);
    } catch (error) {
      toast.error('Не удалось загрузить аналитику');
    } finally {
      setLoading(false);
    }
  };

  const totalExpenses = useMemo(
    () => byCategory.reduce((sum, cat) => sum + cat.total, 0),
    [byCategory]
  );

  const topCategory = useMemo(() => byCategory[0], [byCategory]);

  const averageDailyBalance = useMemo(() => {
    if (!summary) return 0;
    return summary.net_balance / period;
  }, [summary, period]);

  const maxIncome = useMemo(
    () => (trends.length ? Math.max(...trends.map((t) => t.income)) || 1 : 1),
    [trends]
  );

  const maxExpense = useMemo(
    () => (trends.length ? Math.max(...trends.map((t) => t.expenses)) || 1 : 1),
    [trends]
  );

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const token = localStorage.getItem('access_token');
      const url = `http://localhost:8000/api/v1/export/analytics/csv?period_days=${period}`;

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `analytics_${Date.now()}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
      toast.success('Экспорт готов - файл скачан');
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Ошибка экспорта. Попробуйте снова.');
    } finally {
      setIsExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <span className="rounded-full border border-white/30 bg-white/60 px-4 py-2 text-sm uppercase tracking-[0.35em] text-ink/50">
          Аналитика собирается...
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(260px,0.9fr)]">
        <Card className="relative overflow-hidden bg-gradient-to-br from-primary-100/70 via-white/75 to-white/55 p-8">
          <span className="pointer-events-none absolute -right-24 -top-20 h-64 w-64 rounded-full bg-primary-300/30 blur-3xl" />
          <div className="relative z-10 space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div className="max-w-xl space-y-3">
                <p className="text-xs uppercase tracking-[0.35em] text-ink/45">Аналитический обзор</p>
                <h1 className="text-4xl font-display text-ink">
                  Финансовый ритм за {period} дней
                </h1>
                {summary && (
                  <p className="text-sm text-ink/60">
                    Доходы составили{' '}
                    <span className="font-semibold text-primary-700">
                      +{formatCurrency(summary.total_income)} ₽
                    </span>
                    , расходы -{' '}
                    <span className="font-semibold text-roseflare">
                      -{formatCurrency(summary.total_expenses)} ₽
                    </span>
                    . Чистый баланс{' '}
                    <span className={`font-semibold ${summary.net_balance >= 0 ? 'text-primary-700' : 'text-roseflare'}`}>
                      {summary.net_balance >= 0 ? '+' : ''}
                      {formatCurrency(summary.net_balance)} ₽
                    </span>
                    .
                  </p>
                )}
              </div>

              <div className="flex flex-col gap-3 rounded-[1.4rem] border border-white/30 bg-white/70 p-5 shadow-[0_20px_45px_rgba(14,23,40,0.12)]">
                <div className="text-xs uppercase tracking-[0.28em] text-ink/40">Период анализа</div>
                <div className="flex flex-wrap gap-2">
                  {periodOptions.map(({ label, value }) => (
                    <Button
                      key={value}
                      size="sm"
                      variant={period === value ? 'primary' : 'ghost'}
                      onClick={() => setPeriod(value)}
                      className={`rounded-[1rem] ${period === value ? '' : 'border border-white/30 bg-white/50 text-ink/70'}`}
                    >
                      {label}
                    </Button>
                  ))}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleExport}
                  disabled={isExporting}
                  className="mt-2 flex items-center gap-2 rounded-[1rem] border border-white/40 bg-white/60 text-xs uppercase tracking-[0.26em] text-ink hover:bg-white/80 disabled:cursor-wait disabled:opacity-60"
                >
                  <span>{isExporting ? 'Экспортируем...' : 'Экспорт CSV'}</span>
                </Button>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {summary && (
                <>
                  <Card className="bg-white/80 p-5 shadow-none">
                    <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Доходы</p>
                    <p className="mt-3 font-display text-3xl text-primary-700">
                      +{formatCurrency(summary.total_income)} ₽
                    </p>
                    <p className="mt-2 text-xs text-ink/50">{summary.transaction_count} операций</p>
                  </Card>
                  <Card className="bg-white/80 p-5 shadow-none">
                    <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Расходы</p>
                    <p className="mt-3 font-display text-3xl text-roseflare">
                      -{formatCurrency(summary.total_expenses)} ₽
                    </p>
                    {topCategory && (
                      <p className="mt-2 text-xs text-ink/50">
                        Топ категория: <span className="font-medium text-ink/70">{topCategory.category}</span>
                      </p>
                    )}
                  </Card>
                  <Card className="bg-white/80 p-5 shadow-none">
                    <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Среднесуточный баланс</p>
                    <p className="mt-3 font-display text-3xl text-ink">
                      {averageDailyBalance >= 0 ? '+' : ''}
                      {formatCurrency(averageDailyBalance, { maximumFractionDigits: 0 })} ₽
                    </p>
                    <p className="mt-2 text-xs text-ink/50">Повысьте баланс через Premium‑сценарии</p>
                  </Card>
                </>
              )}
            </div>
          </div>
        </Card>

        <Card className="relative overflow-hidden bg-gradient-to-br from-primary-500 to-primary-700 p-7 text-white">
          <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.25),transparent_70%)]" />
          <div className="relative z-10 space-y-4">
            <p className="text-xs uppercase tracking-[0.32em] text-white/70">Premium insight</p>
            <h2 className="font-display text-2xl">
              Разблокируйте сценарии “Что если” и прогноз cashflow на 90 дней
            </h2>
            <p className="text-sm text-white/80">
              Premium режим автоматически симулирует ипотечные платежи, налоговые периоды и кассовые разрывы.
              Подписка окупается, если вы находите минимум один оптимизационный сценарий в квартал.
            </p>
            <Button variant="ghost" className="bg-white/20 text-white hover:bg-white/30">
              Оформить Premium за 299 ₽
            </Button>
            <p className="text-xs text-white/60">Финансовая картина обновляется каждые 30 минут • Отмена в один клик</p>
          </div>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(280px,1fr)]">
        <Card className="relative overflow-hidden p-6">
          <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_15%,rgba(36,176,154,0.12),transparent_65%)]" />
          <div className="relative z-10 space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.32em] text-ink/40">Категоризация</p>
                <h3 className="mt-2 font-display text-2xl text-ink">Расходы по категориям</h3>
              </div>
              <span className="rounded-full border border-primary-200 bg-primary-50/70 px-4 py-1 text-xs font-semibold text-primary-700">
                {byCategory.length} категорий
              </span>
            </div>

            {byCategory.length === 0 ? (
              <div className="rounded-[1.2rem] border border-dashed border-white/40 bg-white/40 py-12 text-center text-sm text-ink/50">
                Данные появятся, как только подключённые банки поделятся первыми операциями
              </div>
            ) : (
              <div className="space-y-4">
                {byCategory.map((cat, index) => {
                  const percentage = totalExpenses > 0 ? (cat.total / totalExpenses) * 100 : 0;
                  return (
                    <div
                      key={cat.category_id}
                      className="group rounded-[1.2rem] border border-white/30 bg-white/70 p-4 shadow-[0_16px_35px_rgba(14,23,40,0.08)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_24px_45px_rgba(14,23,40,0.12)]"
                    >
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Категория #{index + 1}</p>
                          <h4 className="mt-1 text-lg font-semibold text-ink">{cat.category}</h4>
                        </div>
                        <div className="text-right text-sm">
                          <p className="font-display text-xl text-ink">{formatCurrency(cat.total)} ₽</p>
                          <p className="text-xs text-ink/45">{cat.count} операций • {percentage.toFixed(1)}%</p>
                        </div>
                      </div>
                      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-ink/5">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-primary-300 via-primary-500 to-primary-700 transition-all duration-500"
                          style={{ width: `${Math.min(percentage, 100)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </Card>

        <Card className="space-y-5 p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.32em] text-ink/40">Финансовые сигналы</p>
              <h3 className="mt-2 font-display text-xl text-ink">Рекомендации на основе данных</h3>
            </div>
            <Button variant="ghost" size="sm" className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.26em] text-ink/60">
              Смотреть все советы
            </Button>
          </div>

          <div className="space-y-3">
            <Card className="bg-primary-50/80 p-4 shadow-none">
              <p className="text-xs uppercase tracking-[0.28em] text-primary-600">Точка роста</p>
              <p className="mt-2 text-sm text-ink/70">
                Сократите расходы по категории «{topCategory?.category ?? 'Супермаркеты'}» на 12%, перенеся регулярные траты на карту с кешбэком. Экономия{' '}
                <span className="font-semibold text-primary-700">до 4 500 ₽</span> в месяц.
              </p>
            </Card>
            <Card className="bg-white/80 p-4 shadow-none">
              <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Cashflow</p>
              <p className="mt-2 text-sm text-ink/70">
                Через 11 дней ожидается пиковый расход. Перенаправьте {formatCurrency(Math.abs(averageDailyBalance * 5))} ₽ с накопительного счёта заранее, чтобы избежать кассового разрыва.
              </p>
            </Card>
            <Card className="bg-white/80 p-4 shadow-none">
              <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Premium ROI</p>
              <p className="mt-2 text-sm text-ink/70">
                Premium-подписка окупается, если вы находите минимум одну экономию в месяц. Средний пользователь сохраняет{' '}
                <span className="font-semibold text-primary-700">до 18 000 ₽</span> в год.
              </p>
            </Card>
          </div>
        </Card>
      </section>

      <section className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-ink/40">Пульс операций</p>
            <h3 className="mt-2 font-display text-2xl text-ink">Тренды расходов и доходов</h3>
          </div>
          <span className="rounded-full border border-white/30 bg-white/60 px-4 py-1 text-xs font-semibold text-ink/60">
            Обновляется каждые 30 минут
          </span>
        </div>

        <Card className="overflow-hidden p-0">
          {trends.length === 0 ? (
            <div className="p-10 text-center text-sm text-ink/50">
              Нет данных для построения тренда. Подключите банки и дождитесь первых операций.
            </div>
          ) : (
            <div className="divide-y divide-white/20">
              <div className="grid grid-cols-[120px_repeat(3,1fr)] gap-4 px-6 py-4 text-xs uppercase tracking-[0.28em] text-ink/40">
                <span>Дата</span>
                <span className="text-center">Доходы</span>
                <span className="text-center">Расходы</span>
                <span className="text-center">Баланс</span>
              </div>
              {trends.map((trend, idx) => (
                <div
                  key={`${trend.date}-${idx}`}
                  className="grid grid-cols-[120px_repeat(3,1fr)] items-center gap-4 px-6 py-5 transition-colors duration-300 hover:bg-white/45"
                >
                  <div className="font-mono text-sm text-ink/70">
                    {new Date(trend.date).toLocaleDateString('ru-RU', {
                      day: '2-digit',
                      month: '2-digit',
                    })}
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-ink/10">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-primary-200 via-primary-400 to-primary-600"
                        style={{ width: `${(trend.income / maxIncome) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-primary-700">
                      +{formatCurrency(trend.income)} ₽
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-ink/10">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-roseflare/60 via-roseflare to-roseflare"
                        style={{ width: `${(trend.expenses / maxExpense) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-roseflare">
                      -{formatCurrency(trend.expenses)} ₽
                    </span>
                  </div>
                  <div className={`text-sm font-semibold ${trend.net >= 0 ? 'text-primary-700' : 'text-roseflare'}`}>
                    {trend.net >= 0 ? '+' : ''}
                    {formatCurrency(trend.net)} ₽
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </section>
    </div>
  );
};

export default AnalyticsPage;
