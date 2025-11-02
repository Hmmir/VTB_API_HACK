import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import toast from 'react-hot-toast';
import type { Goal as GoalType } from '../types';

const formatCurrency = (value: number, fractionDigits = 0) =>
  value.toLocaleString('ru-RU', { maximumFractionDigits: fractionDigits });

type GoalView = GoalType & {
  progress: number;
  remaining: number;
  daysLeft: number | null;
};

type StatusConfig = {
  badge: string;
  gradient: string;
  tone: string;
  description: string;
};

const STATUS_CONFIG: Record<string, StatusConfig> = {
  COMPLETED: {
    badge: 'bg-primary-100/70 text-primary-700',
    gradient: 'from-primary-100/60 via-white/75 to-white/60',
    tone: 'text-primary-700',
    description: 'Цель достигнута. Пора отпраздновать и поставить следующую вершину.'
  },
  CANCELLED: {
    badge: 'bg-roseflare/15 text-roseflare',
    gradient: 'from-roseflare/15 via-white/70 to-white/60',
    tone: 'text-roseflare',
    description: 'Цель приостановлена. Пересоберите параметры - и мы поможем снова.'
  },
  IN_PROGRESS: {
    badge: 'bg-glow/20 text-ink',
    gradient: 'from-glow/20 via-white/70 to-white/55',
    tone: 'text-ink',
    description: 'Прогресс идет по плану. Ускорить можно через перераспределение бюджета.'
  },
  ACTIVE: {
    badge: 'bg-glow/20 text-ink',
    gradient: 'from-glow/20 via-white/70 to-white/55',
    tone: 'text-ink',
    description: 'Прогресс идет по плану. Ускорить можно через перераспределение бюджета.'
  }
};

const GoalsPage = () => {
  const [goals, setGoals] = useState<GoalType[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [contributionGoal, setContributionGoal] = useState<GoalType | null>(null);
  const [contributionAmount, setContributionAmount] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    target_amount: '',
    current_amount: '0',
    target_date: ''
  });

  useEffect(() => {
    void loadGoals();
  }, []);

  const loadGoals = async () => {
    try {
      setLoading(true);
      const data = await api.getGoals();
      setGoals(data);
    } catch (error) {
      toast.error('Не удалось загрузить цели');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createGoal({
        name: formData.name,
        description: formData.description || undefined,
        target_amount: Number(formData.target_amount),
        current_amount: Number(formData.current_amount),
        target_date: formData.target_date || undefined,
        status: 'IN_PROGRESS'
      });
      toast.success('Цель создана!');
      setShowCreateModal(false);
      setFormData({
        name: '',
        description: '',
        target_amount: '',
        current_amount: '0',
        target_date: ''
      });
      loadGoals();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Ошибка создания цели');
    }
  };

  const handleDelete = async (goalId: number) => {
    if (!window.confirm('Удалить эту цель?')) return;
    try {
      await api.deleteGoal(goalId);
      toast.success('Цель удалена');
      loadGoals();
    } catch (error) {
      toast.error('Ошибка удаления');
    }
  };

  const handleContribute = (goal: GoalType) => {
    setContributionGoal(goal);
    setContributionAmount('');
  };

  const submitContribution = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contributionGoal || !contributionAmount) {
      toast.error('Укажите сумму взноса');
      return;
    }

    try {
      await api.contributeToGoal(contributionGoal.id, Number(contributionAmount));
      toast.success('Взнос добавлен!');
      setContributionGoal(null);
      setContributionAmount('');
      loadGoals();
    } catch (error) {
      toast.error('Ошибка добавления взноса');
    }
  };

  const enrichedGoals = useMemo<GoalView[]>(
    () =>
      goals.map((goal) => {
        const progress = goal.target_amount > 0 ? Math.min((goal.current_amount / goal.target_amount) * 100, 100) : 0;
        const remaining = Math.max(goal.target_amount - goal.current_amount, 0);
        const daysLeft = goal.target_date
          ? Math.ceil((new Date(goal.target_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
          : null;

        return {
          ...goal,
          progress,
          remaining,
          daysLeft
        };
      }),
    [goals]
  );

  const goalsSummary = useMemo(() => {
    const totalTarget = enrichedGoals.reduce((sum, goal) => sum + goal.target_amount, 0);
    const totalCurrent = enrichedGoals.reduce((sum, goal) => sum + goal.current_amount, 0);
    const completedCount = enrichedGoals.filter((goal) => goal.status === 'COMPLETED').length;
    const upcomingGoal = [...enrichedGoals]
      .filter((goal) => goal.status !== 'COMPLETED' && goal.target_date)
      .sort((a, b) => new Date(a.target_date ?? '').getTime() - new Date(b.target_date ?? '').getTime())[0];

    return {
      totalTarget,
      totalCurrent,
      completionRate: totalTarget > 0 ? Math.min((totalCurrent / totalTarget) * 100, 100) : 0,
      completedCount,
      upcomingGoal
    };
  }, [enrichedGoals]);

  const getStatusConfig = (status: string): StatusConfig => {
    if (STATUS_CONFIG[status]) {
      return STATUS_CONFIG[status];
    }
    return STATUS_CONFIG.IN_PROGRESS;
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <span className="rounded-full border border-white/30 bg-white/60 px-4 py-2 text-sm uppercase tracking-[0.32em] text-ink/50">
          Загружаем орбиту целей...
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(260px,0.9fr)]">
        <Card className="relative overflow-hidden bg-gradient-to-br from-primary-100/70 via-white/75 to-white/55 p-8">
          <span className="pointer-events-none absolute -right-20 -top-16 h-64 w-64 rounded-full bg-primary-300/25 blur-3xl" />
          <div className="relative z-10 space-y-8">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div className="max-w-xl space-y-3">
                <p className="text-xs uppercase tracking-[0.35em] text-ink/45">Навигация по мечтам</p>
                <h1 className="text-4xl font-display text-ink">Каждая финансовая цель получает орбиту</h1>
                <p className="text-sm text-ink/60">
                  Уже накоплено{' '}
                  <span className="font-semibold text-primary-700">{formatCurrency(goalsSummary.totalCurrent)} ₽</span>{' '}
                  из запланированных{' '}
                  <span className="font-semibold text-ink">{formatCurrency(goalsSummary.totalTarget)} ₽</span>. Прогресс{' '}
                  <span className="font-semibold text-primary-700">{goalsSummary.completionRate.toFixed(0)}%</span> - теперь направим
                  аналитические подсказки на ускорение.
                </p>
              </div>
              <div className="flex flex-col items-stretch gap-3 rounded-[1.4rem] border border-white/30 bg-white/70 p-5 shadow-[0_20px_45px_rgba(14,23,40,0.12)]">
                <div className="text-xs uppercase tracking-[0.32em] text-ink/40">Быстрые действия</div>
                <Button variant="primary" size="lg" onClick={() => setShowCreateModal(true)}>
                  <span className="text-lg">+</span>
                  <span className="ml-2">Создать цель</span>
                </Button>
                <div className="rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-3 text-xs text-ink/55">
                  Premium ускоряет цели через автоматическое распределение бюджета и персональные сценарии накоплений.
                </div>
              </div>
      </div>

            <div className="grid gap-4 md:grid-cols-3">
              <Card className="bg-white/80 p-5 shadow-none">
                <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Целевой капитал</p>
                <p className="mt-3 font-display text-3xl text-ink">{formatCurrency(goalsSummary.totalTarget)} ₽</p>
                <p className="mt-2 text-xs text-ink/50">{goalsSummary.completedCount} целей закрыто</p>
              </Card>
              <Card className="bg-white/80 p-5 shadow-none">
                <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Прогресс</p>
                <p className="mt-3 font-display text-3xl text-primary-700">{goalsSummary.completionRate.toFixed(0)}%</p>
                <p className="mt-2 text-xs text-ink/50">Используйте рекомендации ниже, чтобы ускориться</p>
              </Card>
              <Card className="bg-white/80 p-5 shadow-none">
                <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Ближайшая точка</p>
                <p className="mt-3 font-display text-xl text-ink">
                  {goalsSummary.upcomingGoal?.name ?? 'Добавьте дату цели'}
                </p>
                <p className="mt-2 text-xs text-ink/50">
                  {goalsSummary.upcomingGoal?.target_date
                    ? `Дедлайн ${new Date(goalsSummary.upcomingGoal.target_date).toLocaleDateString('ru-RU')}`
                    : 'Планирование доступно в один клик'}
                </p>
              </Card>
            </div>
          </div>
        </Card>

        <Card className="relative overflow-hidden bg-gradient-to-br from-primary-500 to-primary-700 p-7 text-white">
          <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.22),transparent_70%)]" />
          <div className="relative z-10 space-y-4">
            <p className="text-xs uppercase tracking-[0.32em] text-white/70">Premium «Акселератор целей»</p>
            <h2 className="font-display text-2xl">Прогнозируйте, ускоряйте, делитесь прогрессом</h2>
            <ul className="space-y-2 text-sm text-white/80">
              <li>• Авторасчёт еженедельных взносов и уведомления о кассовых разрывах</li>
              <li>• Совместные цели с семьёй или партнёрами, настройка доступов</li>
              <li>• Интеллектуальные сценарии «что если» для ускоренного достижения</li>
            </ul>
            <Button variant="ghost" className="bg-white/20 text-white hover:bg-white/30">
              Попробовать Premium 14 дней бесплатно
            </Button>
            <p className="text-xs text-white/60">Средний клиент достигает цели на 3 месяца раньше</p>
          </div>
        </Card>
      </section>

      <section className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-ink/40">Ваши орбиты</p>
            <h3 className="mt-2 font-display text-2xl text-ink">Карточки целей и рекомендуемые действия</h3>
          </div>
          <Button variant="ghost" size="sm" className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.26em] text-ink/60">
            План ускорения
          </Button>
        </div>

        {enrichedGoals.length === 0 ? (
          <Card className="relative overflow-hidden bg-white/70 p-12 text-center">
            <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,rgba(36,176,154,0.15),transparent_65%)]" />
            <div className="relative z-10 space-y-4">
              <span className="text-6xl">🚀</span>
              <h4 className="text-2xl font-display text-ink">Первый шаг к мечте</h4>
              <p className="text-sm text-ink/60">Опишите цель - и мы подберем стратегию накоплений, прогнозы и нотификации.</p>
              <Button size="lg" variant="primary" onClick={() => setShowCreateModal(true)}>
                Задать цель
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            {enrichedGoals.map((goal) => {
              const config = getStatusConfig(goal.status);
            return (
                <Card key={goal.id} className={`relative overflow-hidden bg-gradient-to-br ${config.gradient} p-6`}>
                  <span className="pointer-events-none absolute -left-16 -top-24 h-48 w-48 rounded-full bg-white/25 blur-3xl" />
                  <div className="relative z-10 space-y-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-2">
                        <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Цель</p>
                        <h4 className="text-xl font-semibold text-ink">{goal.name}</h4>
                      {goal.description && (
                          <p className="text-sm text-ink/60 max-w-prose">{goal.description}</p>
                        )}
                        {goal.daysLeft !== null && (
                          <p className="text-xs text-ink/45">
                            Осталось {goal.daysLeft >= 0 ? `${goal.daysLeft} дней` : 'время вышло - пересмотрите стратегию'}
                          </p>
                        )}
                    </div>
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${config.badge}`}>
                        {goal.status === 'COMPLETED' ? 'Достигнута' : goal.status === 'CANCELLED' ? 'Пауза' : 'В процессе'}
                    </span>
                  </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-xs text-ink/50">
                        <span>Прогресс</span>
                        <span className={`font-semibold ${config.tone}`}>{goal.progress.toFixed(1)}%</span>
                    </div>
                      <div className="h-3 w-full overflow-hidden rounded-full bg-ink/10">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            goal.progress >= 100
                              ? 'bg-gradient-to-r from-primary-300 via-primary-500 to-primary-700'
                              : 'bg-gradient-to-r from-primary-200 via-primary-400 to-primary-600'
                          }`}
                          style={{ width: `${Math.min(goal.progress, 120)}%` }}
                      />
                    </div>
                      <div className="grid grid-cols-3 gap-3 text-xs text-ink/55">
                        <div>
                          <p>Накоплено</p>
                          <p className="mt-1 font-semibold text-ink">{formatCurrency(goal.current_amount)} ₽</p>
                        </div>
                        <div>
                          <p>Цель</p>
                          <p className="mt-1 font-semibold text-ink">{formatCurrency(goal.target_amount)} ₽</p>
                  </div>
                    <div>
                          <p>Осталось</p>
                          <p className={`mt-1 font-semibold ${goal.remaining <= 0 ? 'text-primary-700' : 'text-ink'}`}>
                            {formatCurrency(goal.remaining)} ₽
                      </p>
                    </div>
                      </div>
                  </div>

                    <div className="space-y-3 rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-3 text-xs text-ink/60">
                      {config.description}
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-2 border-t border-white/40 pt-4">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleContribute(goal)}
                        className="border border-primary-200 bg-white/70 text-xs uppercase tracking-[0.22em] text-primary-700"
                      >
                        Внести взнос
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(goal.id)}
                        className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.22em] text-ink"
                      >
                        Удалить
                      </Button>
                    </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
      </section>

      <Modal title="Создать цель" open={showCreateModal} onClose={() => setShowCreateModal(false)}>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Название</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input-field"
                required
              />
            </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Описание (необязательно)</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="input-field min-h-[120px]"
              placeholder="Например: отпуск на Сахалине или финансовая подушка на 6 месяцев"
              />
            </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Цель (₽)</label>
                <input
                  type="number"
                  value={formData.target_amount}
                  onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                  className="input-field"
                min="0"
                  required
                />
              </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Уже накоплено (₽)</label>
                <input
                  type="number"
                  value={formData.current_amount}
                  onChange={(e) => setFormData({ ...formData, current_amount: e.target.value })}
                  className="input-field"
                  min="0"
                />
              </div>
            </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Дата достижения (необязательно)</label>
              <input
                type="date"
                value={formData.target_date}
                onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
                className="input-field"
              />
            </div>

          <div className="rounded-[1.1rem] border border-primary-100 bg-primary-50/70 px-4 py-3 text-xs text-ink/55">
            Premium добавит сценарии ускорения и напомнит о еженедельно оптимальной сумме взноса.
          </div>

          <div className="flex justify-end gap-2">
              <Button
                type="button"
              variant="ghost"
              onClick={() => setShowCreateModal(false)}
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

      <Modal
        title={contributionGoal ? `Внести взнос в цель «${contributionGoal.name}»` : 'Внести взнос'}
        open={Boolean(contributionGoal)}
        onClose={() => setContributionGoal(null)}
      >
        <form onSubmit={submitContribution} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Сумма (₽)</label>
            <input
              type="number"
              value={contributionAmount}
              onChange={(e) => setContributionAmount(e.target.value)}
              className="input-field"
              min="1"
              required
            />
          </div>

          {contributionGoal && (
            <div className="rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-3 text-xs text-ink/55">
              После взноса прогресс составит{' '}
              <span className="font-semibold text-primary-700">
                {formatCurrency(contributionGoal.current_amount + Number(contributionAmount || 0))} ₽
              </span>
              из {formatCurrency(contributionGoal.target_amount)} ₽.
            </div>
          )}

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setContributionGoal(null)}
              className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.26em] text-ink/70"
            >
              Отмена
            </Button>
            <Button type="submit" variant="primary">
              Внести
            </Button>
            </div>
          </form>
      </Modal>
    </div>
  );
};

export default GoalsPage;
