import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import toast from 'react-hot-toast';
import type { Budget as BudgetType } from '../types';
import { formatCurrency, formatCompactCurrency } from '../utils/formatters';

type BudgetStatusDetails = {
  budget_id: number;
  category: string;
  limit: number;
  spent: number;
  remaining: number;
  percentage: number;
  is_exceeded: boolean;
  is_warning: boolean;
  period: {
    start: string;
    end: string;
  };
};

type BudgetCategoryOption = {
  id: number;
  name: string;
};

type BudgetRecord = BudgetType & {
  category?: { name: string };
  end_date: string;
};

const BudgetsPage = () => {
  const [budgets, setBudgets] = useState<BudgetRecord[]>([]);
  const [budgetStatuses, setBudgetStatuses] = useState<Record<number, BudgetStatusDetails>>({});
  const [categories, setCategories] = useState<BudgetCategoryOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    category_id: '',
    amount: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load categories
      const expensesData = await api.getExpensesByCategory(30);
      setCategories(expensesData.map((c) => ({ id: c.category_id, name: c.category })));

      const budgetsData = await api.getBudgets();
      const mappedBudgets = budgetsData.map((budget) => ({
        ...budget,
        end_date: budget.end_date || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
      })) as BudgetRecord[];
      setBudgets(mappedBudgets);

      const statusesEntries = await Promise.all(
        budgetsData.map(async (budget) => {
          try {
            const statusData = await api.getBudgetStatus(budget.id);
            return [budget.id, statusData as BudgetStatusDetails] as const;
        } catch (error) {
          console.error(`Failed to load status for budget ${budget.id}:`, error);
            return [budget.id, undefined] as const;
          }
        })
      );

      const statuses: Record<number, BudgetStatusDetails> = {};
      for (const [budgetId, status] of statusesEntries) {
        if (status) {
          statuses[budgetId] = status;
        }
      }
      setBudgetStatuses(statuses);
    } catch (error) {
      console.error('Budgets error:', error);
      setCategories([]);
      setBudgets([]);
      toast.error('Не удалось загрузить бюджеты');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Преобразуем даты в ISO формат с временем
      const startDateTime = new Date(formData.start_date + 'T00:00:00').toISOString();
      const endDateTime = new Date(formData.end_date + 'T23:59:59').toISOString();
      
      await api.createBudget({
        name: formData.name,
        category_id: Number(formData.category_id),
        amount: Number(formData.amount),
        start_date: startDateTime,
        end_date: endDateTime,
      });
      toast.success('Бюджет создан!');
      setShowModal(false);
      loadData();
      
      // Reset form
      setFormData({
        name: '',
        category_id: '',
        amount: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      });
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Ошибка создания бюджета');
    }
  };

  const handleDelete = async (budgetId: number) => {
    if (!window.confirm('Удалить этот бюджет?')) return;
    try {
      await api.deleteBudget(budgetId);
      toast.success('Бюджет удален');
      loadData();
    } catch (error) {
      toast.error('Ошибка удаления');
    }
  };

  const enrichedBudgets = useMemo(() =>
    budgets
      .map((budget) => ({
        ...budget,
        status: budgetStatuses[budget.id],
      }))
      .sort((a, b) => (b.status?.percentage ?? 0) - (a.status?.percentage ?? 0)),
  [budgets, budgetStatuses]);

  const budgetsSummary = useMemo(() => {
    const totalLimit = enrichedBudgets.reduce((sum, budget) => sum + (budget.status?.limit ?? budget.amount ?? 0), 0);
    const totalSpent = enrichedBudgets.reduce((sum, budget) => sum + (budget.status?.spent ?? 0), 0);
    const exceededCount = enrichedBudgets.filter((budget) => budget.status?.is_exceeded).length;
    const warningCount = enrichedBudgets.filter((budget) => budget.status?.is_warning && !budget.status?.is_exceeded).length;
    const upcomingRenewal = [...enrichedBudgets]
      .filter((budget) => budget.status)
      .sort((a, b) => new Date(a.status!.period.end).getTime() - new Date(b.status!.period.end).getTime())[0]?.status;

    return {
      totalLimit,
      totalSpent,
      exceededCount,
      warningCount,
      upcomingRenewal,
    };
  }, [enrichedBudgets]);

  const premiumLimitReached = enrichedBudgets.length >= 3;

  const formatDateRange = (start: string, end: string) =>
    `${new Date(start).toLocaleDateString('ru-RU')} - ${new Date(end).toLocaleDateString('ru-RU')}`;

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <span className="rounded-full border border-white/30 bg-white/60 px-4 py-2 text-sm uppercase tracking-[0.32em] text-ink/50">
          Сводим ваши конверты...
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(260px,0.9fr)]">
        <Card className="relative overflow-hidden bg-gradient-to-br from-primary-100/70 via-white/75 to-white/55 p-8">
          <span className="pointer-events-none absolute -right-24 -top-20 h-64 w-64 rounded-full bg-primary-300/30 blur-3xl" />
          <div className="relative z-10 space-y-8">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div className="max-w-xl space-y-3">
                <p className="text-xs uppercase tracking-[0.35em] text-ink/45">Интеллектуальные конверты</p>
                <h1 className="text-4xl font-display text-ink">Контролируйте траты, как продвинутый CFO</h1>
                <p className="text-sm text-ink/60">
                  Вы распределили{' '}
                  <span className="font-semibold text-primary-700">{formatCurrency(budgetsSummary.totalLimit)} ₽</span>{' '}
                  по бюджетам. Уже потрачено{' '}
                  <span className="font-semibold text-roseflare">{formatCurrency(budgetsSummary.totalSpent)} ₽</span>. Наш алгоритм подскажет, где притормозить и чем подкрепить ваши финансовые цели.
                </p>
              </div>
              <div className="flex flex-col items-stretch gap-3 rounded-[1.4rem] border border-white/30 bg-white/70 p-5 shadow-[0_20px_45px_rgba(14,23,40,0.12)]">
                <div className="text-xs uppercase tracking-[0.32em] text-ink/40">Быстрые действия</div>
                <Button variant="primary" size="lg" onClick={() => setShowModal(true)} disabled={premiumLimitReached}>
                  <span className="text-lg">+</span>
                  <span className="ml-2">Создать бюджет</span>
                </Button>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <Card className="bg-white/80 p-5 shadow-none">
                <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Активные бюджеты</p>
                <p className="mt-3 font-display text-3xl text-ink">{enrichedBudgets.length}</p>
                <p className="mt-2 text-xs text-ink/50">{budgetsSummary.warningCount} нуждаются во внимании</p>
              </Card>
              <Card className="bg-white/80 p-5 shadow-none">
                <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Превышение</p>
                <p className={`mt-3 font-display text-3xl ${budgetsSummary.exceededCount > 0 ? 'text-roseflare' : 'text-primary-700'}`}>{budgetsSummary.exceededCount}</p>
                <p className="mt-2 text-xs text-ink/50">Используйте рекомендации ниже, чтобы вернуть баланс</p>
              </Card>
              <Card className="bg-white/80 p-5 shadow-none">
                <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Следующее обновление</p>
                <p className="mt-3 font-display text-xl text-ink">
                  {budgetsSummary.upcomingRenewal
                    ? formatDateRange(budgetsSummary.upcomingRenewal.period.start, budgetsSummary.upcomingRenewal.period.end)
                    : 'Задайте график'}
                </p>
                <p className="mt-2 text-xs text-ink/50">Подготовим автоматический перенос лимитов</p>
              </Card>
            </div>
          </div>
        </Card>
      </section>

      <section className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-ink/40">Активные конверты</p>
            <h3 className="mt-2 font-display text-2xl text-ink">Карта ваших бюджетов</h3>
          </div>
          <Button variant="ghost" size="sm" className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.26em] text-ink/60">
            План переноса лимитов
          </Button>
      </div>

        {enrichedBudgets.length === 0 ? (
          <Card className="relative overflow-hidden bg-white/70 p-12 text-center">
            <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,rgba(36,176,154,0.15),transparent_65%)]" />
            <div className="relative z-10 space-y-4">
              <span className="text-6xl">🎯</span>
              <h4 className="text-2xl font-display text-ink">Начните с первого конверта</h4>
              <p className="text-sm text-ink/60">
                Установите лимит для самой «горячей» категории расходов. Алгоритм проанализирует данные и предложит оптимизацию.
              </p>
              <Button size="lg" variant="primary" onClick={() => setShowModal(true)}>
                Создать бюджет
            </Button>
          </div>
        </Card>
      ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            {enrichedBudgets.map((budget) => {
              const status = budget.status;
              const state = status?.is_exceeded ? 'exceeded' : status?.is_warning ? 'warning' : 'ok';
              const gradientClass =
                state === 'exceeded'
                  ? 'from-roseflare/15 via-white/70 to-white/60'
                  : state === 'warning'
                  ? 'from-glow/25 via-white/70 to-white/60'
                  : 'from-primary-100/40 via-white/70 to-white/60';
            
            return (
                <Card key={budget.id} className={`relative overflow-hidden bg-gradient-to-br ${gradientClass} p-6`}>
                  <span className="pointer-events-none absolute -left-16 -top-24 h-48 w-48 rounded-full bg-white/30 blur-3xl" />
                  <div className="relative z-10 space-y-5">
                    <div className="flex items-start justify-between gap-4">
                    <div>
                        <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Категория</p>
                        <h4 className="mt-1 text-xl font-semibold text-ink">{status?.category || budget.category?.name || 'Категория'}</h4>
                      {status && (
                          <p className="mt-1 text-xs text-ink/45">{formatDateRange(status.period.start, status.period.end)}</p>
                      )}
                    </div>
                      {status && (
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            state === 'exceeded'
                              ? 'bg-roseflare/15 text-roseflare'
                              : state === 'warning'
                              ? 'bg-glow/20 text-ink'
                              : 'bg-primary-100/60 text-primary-700'
                          }`}
                        >
                          {state === 'exceeded' ? 'Перерасход' : state === 'warning' ? 'Почти лимит' : 'Стабильно'}
                        </span>
                      )}
                  </div>

                    {status ? (
                      <>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between text-xs text-ink/50">
                            <span>Потрачено</span>
                            <span className="font-semibold text-ink/70">{formatCurrency(status.spent)} ₽</span>
                        </div>
                          <div className="h-3 w-full overflow-hidden rounded-full bg-ink/10">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                state === 'exceeded'
                                  ? 'bg-gradient-to-r from-roseflare via-roseflare to-roseflare/70'
                                  : state === 'warning'
                                  ? 'bg-gradient-to-r from-glow via-glow to-glow/80'
                                  : 'bg-gradient-to-r from-primary-300 via-primary-500 to-primary-700'
                              }`}
                              style={{ width: `${Math.min(status.percentage, 130)}%` }}
                          />
                        </div>
                          <div className="grid grid-cols-3 gap-3 text-xs text-ink/55">
                            <div>
                              <p>Лимит</p>
                              <p className="mt-1 font-semibold text-ink">{formatCurrency(status.limit)} ₽</p>
                          </div>
                            <div>
                              <p>Осталось</p>
                              <p className={`mt-1 font-semibold ${status.remaining < 0 ? 'text-roseflare' : 'text-ink'}`}>
                                {formatCurrency(status.remaining)} ₽
                              </p>
                            </div>
                            <div>
                              <p>Прогресс</p>
                              <p className={`mt-1 font-semibold ${state === 'exceeded' ? 'text-roseflare' : 'text-primary-700'}`}>
                                {status.percentage.toFixed(0)}%
                              </p>
                            </div>
                          </div>
                      </div>

                        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/40 pt-4">
                          <div className="text-xs text-ink/55">
                            {state === 'exceeded'
                              ? 'Перенаправьте часть расходов: предложим автоматический перевод средств.'
                              : state === 'warning'
                              ? 'Рекомендуем включить уведомления о каждой крупной покупке.'
                              : 'Все в зелёной зоне. Можно сконцентрироваться на накоплениях.'}
                        </div>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.22em] text-ink"
                              onClick={() => handleDelete(budget.id)}
                            >
                              Удалить
                            </Button>
                        </div>
                      </div>
                    </>
                    ) : (
                      <div className="rounded-[1.1rem] border border-dashed border-white/40 bg-white/40 px-4 py-6 text-sm text-ink/50">
                        Данные ещё синхронизируются. Попробуйте обновить через пару минут.
                      </div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
      </section>

      <Modal title="Создать бюджет" open={showModal} onClose={() => setShowModal(false)}>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Название бюджета</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input-field"
              placeholder="Например: Продукты на ноябрь"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Категория</label>
              <select
                value={formData.category_id}
                onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                className="input-field"
                required
              >
                <option value="">Выберите категорию</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                  </option>
                ))}
              </select>
            </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Лимит (₽)</label>
              <input
                type="number"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className="input-field"
              min="0"
                required
              />
            </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Начало периода</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="input-field"
                  required
                />
              </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Конец периода</label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="input-field"
                  required
                />
              </div>
            </div>

          <div className="flex justify-end gap-2">
              <Button
                type="button"
              variant="ghost"
                onClick={() => setShowModal(false)}
              className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.26em] text-ink/70"
              >
                Отмена
              </Button>
            <Button type="submit" variant="primary">
              Сохранить
            </Button>
            </div>
          </form>
      </Modal>

      {/* Premium Upgrade Banner */}
      <Card className="relative overflow-hidden bg-gradient-to-br from-blue-100 via-blue-50 to-white/70 p-8 mt-8">
        <span className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-blue-300/30 blur-3xl" />
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2">
            <h3 className="text-2xl font-display text-ink">🤖 Умное управление бюджетом с Premium</h3>
            <p className="text-sm text-ink/70">
              Автоматические уведомления о превышениях, совместные семейные бюджеты, AI-советы по экономии.
              Пользователи Premium экономят в среднем 12 400 ₽ за квартал.
            </p>
          </div>
          <Button 
            variant="primary" 
            onClick={() => window.location.href = '/premium'}
            className="whitespace-nowrap px-8 py-3"
          >
            Узнать больше
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default BudgetsPage;
