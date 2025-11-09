import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import toast from 'react-hot-toast';

interface RecommendationView {
  id: string;
  type: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  action: string;
  estimated_benefit: string;
  details: Record<string, any>;
}

const PRIORITY_CONFIG: Record<RecommendationView['priority'], { label: string; badge: string; gradient: string; tone: string }> = {
  high: {
    label: 'Высокий приоритет',
    badge: 'bg-roseflare/20 text-roseflare border-roseflare/30',
    gradient: 'from-roseflare/18 via-white/70 to-white/55',
    tone: 'text-roseflare'
  },
  medium: {
    label: 'Средний приоритет',
    badge: 'bg-glow/20 text-ink border-glow/30',
    gradient: 'from-glow/20 via-white/70 to-white/55',
    tone: 'text-ink'
  },
  low: {
    label: 'Низкий приоритет',
    badge: 'bg-primary-100/70 text-primary-700 border-primary-200',
    gradient: 'from-primary-100/50 via-white/70 to-white/55',
    tone: 'text-primary-700'
  }
};

const RecommendationsPage = () => {
  const [recommendations, setRecommendations] = useState<RecommendationView[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    try {
      const data = await api.getRecommendations();
      console.log('Recommendations data:', data);
      const mapped: RecommendationView[] = (data || []).map((rec: any, index: number) => {
        const priorityValue = typeof rec.priority === 'number' ? rec.priority : 0;
        const priority: RecommendationView['priority'] = priorityValue >= 2 ? 'high' : priorityValue === 1 ? 'medium' : 'low';
        return {
          id: String(rec.id ?? rec.uuid ?? `rec-${index}`),
          type: rec.recommendation_type || rec.type || 'general',
          priority,
          title: rec.title || 'Рекомендация',
          description: rec.description || 'Соберите данные, чтобы увидеть подробности.',
          action: rec.action || 'Открыть',
          estimated_benefit: rec.estimated_savings || rec.estimated_benefit || '-',
          details: rec.details || {}
        };
      });
      if (mapped.length > 0) {
        setRecommendations(mapped);
        return;
      }

      // Создаем fallback-рекомендации на основе аналитики, если бэкенд ничего не вернул
      const summary = await api.getAnalyticsSummary(90).catch(() => null);
      const categories = await api.getExpensesByCategory(90).catch(() => []);

      const fallback: RecommendationView[] = [];

      if (summary) {
        const expenseShare = summary.total_income > 0 ? (summary.total_expenses / summary.total_income) * 100 : 0;
        if (expenseShare >= 80) {
          fallback.push({
            id: 'fallback-budget-control',
            type: 'budget_control',
            priority: 'high',
            title: '⚠️ Расходы достигают 80% от доходов',
            description: 'Создайте семейный бюджет и лимиты на категории, чтобы держать траты под контролем.',
            action: 'Открыть бюджеты',
            estimated_benefit: `Экономия до ${(summary.total_expenses * 0.15).toFixed(0)} ₽/мес`,
            details: {
              monthly_income: summary.total_income.toFixed(0),
              monthly_expenses: summary.total_expenses.toFixed(0),
              expense_share: `${expenseShare.toFixed(1)}%`
            }
          });
        }

        if (summary.net_balance > 20000) {
          fallback.push({
            id: 'fallback-goal-savings',
            type: 'family_goal',
            priority: 'medium',
            title: '💰 Направьте свободные средства в цели',
            description: `Свободный остаток за 3 месяца составил ${summary.net_balance.toFixed(0)} ₽. Настройте семейную цель и переводите в MyBank автоматом.`,
            action: 'Создать цель',
            estimated_benefit: `${(summary.net_balance * 0.05).toFixed(0)} ₽/мес`,
            details: {
              net_balance: summary.net_balance.toFixed(0),
              goals_created: summary.goal_progress?.length ?? 0
            }
          });
        }
      }

      if (Array.isArray(categories) && categories.length > 0) {
        const [topCategory] = categories;
        if (topCategory) {
          fallback.push({
            id: 'fallback-category-focus',
            type: 'category_focus',
            priority: 'medium',
            title: `🎯 Категория “${topCategory.category}” лидирует по расходам`,
            description: 'Установите семейный бюджет и лимиты на эту категорию, чтобы сократить лишние траты.',
            action: 'Настроить лимит',
            estimated_benefit: `${(Number(topCategory.amount) * 0.1).toFixed(0)} ₽ в месяц`,
            details: {
              category_spending: Number(topCategory.amount).toFixed(0),
              transactions: topCategory.count ?? 0
            }
          });
        }
      }

      setRecommendations(fallback);
    } catch (error) {
      console.error('Recommendations error:', error);
      setRecommendations([]);
      toast.error('Не удалось загрузить рекомендации');
    } finally {
      setLoading(false);
    }
  };

  const highPriorityCount = useMemo(() => recommendations.filter((rec) => rec.priority === 'high').length, [recommendations]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <span className="rounded-full border border-white/30 bg-white/60 px-4 py-2 text-sm uppercase tracking-[0.32em] text-ink/50">
          Анализируем транзакции...
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(260px,0.9fr)]">
        <Card className="relative overflow-hidden bg-gradient-to-br from-primary-100/70 via-white/75 to-white/55 p-8">
          <span className="pointer-events-none absolute -right-24 -top-20 h-64 w-64 rounded-full bg-primary-300/30 blur-3xl" />
          <div className="relative z-10 space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div className="max-w-xl space-y-3">
                <p className="text-xs uppercase tracking-[0.35em] text-ink/45">Персональный AI-коуч</p>
                <h1 className="text-4xl font-display text-ink">Рекомендации, которые превращают данные в экономию</h1>
                <p className="text-sm text-ink/60">
                  Мы синхронизируем расходы, банки и цели, чтобы предложить точечные действия.{' '}
                  <span className="font-semibold text-primary-700">{highPriorityCount}</span> рекомендаций требуют внимания прямо сейчас.
                </p>
              </div>
            </div>

            <Card className="bg-white/80 p-6 shadow-none">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.32em] text-ink/45">Выгода года</p>
                  <h2 className="text-2xl font-display text-ink">Средняя экономия пользователей - 18 000 ₽</h2>
                </div>
                <Link to="/analytics">
                  <Button variant="ghost" className="border border-white/40 bg-white/60 text-ink">
                    Смотреть аналитику
                  </Button>
                </Link>
              </div>
            </Card>
          </div>
        </Card>

        <Card className="relative overflow-hidden bg-gradient-to-br from-glow/18 via-white/70 to-white/55 p-7">
          <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.22),transparent_70%)]" />
          <div className="relative z-10 space-y-4 text-ink">
            <p className="text-xs uppercase tracking-[0.32em] text-ink/45">Монетизация рекомендаций</p>
            <h2 className="font-display text-xl">Превращайте советы в выручку: партнёрские продукты, retention</h2>
            <ul className="space-y-2 text-sm text-ink/70">
              <li>• Интегрируйте офферы банков напрямую в карточку рекомендации</li>
              <li>• Отслеживайте, сколько экономии принесла каждая подсказка</li>
              <li>• Включите автоматическую отправку и контроль исполнения</li>
            </ul>
            <Button variant="ghost" className="border border-white/40 bg-white/60 text-ink">
              Узнать о сценариях монетизации
            </Button>
          </div>
        </Card>
      </section>

      <section className="space-y-6">
        {recommendations.length === 0 ? (
          <Card className="relative overflow-hidden bg-white/70 p-12 text-center">
            <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,rgba(36,176,154,0.15),transparent_65%)]" />
            <div className="relative z-10 space-y-4">
              <span className="text-6xl">✨</span>
              <h4 className="text-2xl font-display text-ink">Рекомендации появятся после анализа первых транзакций</h4>
              <p className="text-sm text-ink/60">
                Подключите банки и совершите несколько операций - AI подготовит персональные подсказки.
              </p>
              <Link to="/accounts">
                <Button variant="primary">Подключить банк</Button>
              </Link>
            </div>
          </Card>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            {recommendations.map((rec) => {
              const config = PRIORITY_CONFIG[rec.priority];
              return (
                <Card key={rec.id} className={`relative overflow-hidden bg-gradient-to-br ${config.gradient} p-6`}>
                  <span className="pointer-events-none absolute -left-14 -top-20 h-48 w-48 rounded-full bg-white/25 blur-3xl" />
                  <div className="relative z-10 space-y-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-2">
                        <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Рекомендация</p>
                        <h3 className="text-xl font-semibold text-ink">{rec.title}</h3>
                        <p className="text-sm text-ink/60 min-h-[60px]">{rec.description}</p>
                      </div>
                      <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${config.badge}`}>
                        {config.label}
                      </span>
                    </div>

                    <div className="rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-3 text-xs text-ink/60">
                      Потенциальная выгода: <span className={`font-semibold ${config.tone}`}>{rec.estimated_benefit}</span>
                    </div>

                    {rec.details && Object.keys(rec.details).length > 0 && (
                      <div className="grid gap-3 rounded-[1.1rem] border border-dashed border-white/40 bg-white/40 px-4 py-3 text-xs text-ink/55 sm:grid-cols-2">
                        {Object.entries(rec.details).map(([key, value]) => (
                          <div key={key}>
                            <p className="uppercase tracking-[0.22em] text-ink/40">{key.replace(/_/g, ' ')}</p>
                            <p className="mt-1 font-semibold text-ink">
                              {typeof value === 'number' ? value.toLocaleString('ru-RU') : String(value)}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/40 pt-4">
                      <Button 
                        variant="primary" 
                        className="text-xs uppercase tracking-[0.22em]"
                        onClick={() => {
                          // Перенаправляем на соответствующую страницу в зависимости от типа рекомендации
                          if (rec.type === 'budget_control' || rec.type === 'category_focus') {
                            window.location.href = '/budgets';
                          } else if (rec.type === 'family_goal' || rec.type === 'savings') {
                            window.location.href = '/goals';
                          } else if (rec.type === 'deposit' || rec.type === 'investment' || rec.type === 'cashback') {
                            window.location.href = '/products';
                          } else {
                            toast('Функция в разработке', { icon: 'ℹ️' });
                          }
                        }}
                      >
                        {rec.action}
                      </Button>
                      <div className="flex items-center gap-2">
                        <Button 
                          variant="ghost" 
                          className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.22em] text-ink"
                          onClick={() => {
                            setRecommendations(prev => prev.filter(r => r.id !== rec.id));
                            toast.success('Рекомендация отмечена выполненной');
                          }}
                        >
                          Отметить выполненным
                        </Button>
                        <Button 
                          variant="ghost" 
                          className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.22em] text-ink/60"
                          onClick={() => {
                            setRecommendations(prev => prev.filter(r => r.id !== rec.id));
                            toast('Рекомендация отложена', { icon: '⏸️' });
                          }}
                        >
                          Отложить
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
};

export default RecommendationsPage;
