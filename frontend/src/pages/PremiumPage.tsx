import { useState } from 'react';
import { Link } from 'react-router-dom';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import toast from 'react-hot-toast';

const PremiumPage = () => {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');

  const handleSubscribe = () => {
    toast.success('Функция оплаты будет доступна после интеграции платежной системы');
    // В реальном приложении здесь будет интеграция с платежной системой
  };

  const monthlyPrice = 299;
  const yearlyPrice = 2990; // ~249 ₽/мес при оплате за год

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <Card className="relative overflow-hidden bg-gradient-to-br from-primary-100 via-white/90 to-white/70 p-12">
        <span className="pointer-events-none absolute -right-32 -top-32 h-96 w-96 rounded-full bg-primary-300/30 blur-3xl" />
        <div className="relative z-10 space-y-6 text-center">
          <h1 className="text-5xl font-display text-ink">FinanceHub Premium</h1>
          <p className="text-xl text-ink/70 max-w-3xl mx-auto">
            Профессиональные инструменты для управления финансами.
            Прогнозы, автоматизация и персональные рекомендации.
          </p>
          <div className="flex items-center justify-center gap-4 pt-4">
            <div className="text-center">
              <p className="text-4xl font-bold text-primary-600">18 000 ₽</p>
              <p className="text-sm text-ink/50">средняя экономия в год</p>
            </div>
            <div className="w-px h-12 bg-ink/20" />
            <div className="text-center">
              <p className="text-4xl font-bold text-primary-600">3 мес</p>
              <p className="text-sm text-ink/50">быстрее достигаете целей</p>
            </div>
            <div className="w-px h-12 bg-ink/20" />
            <div className="text-center">
              <p className="text-4xl font-bold text-primary-600">90 дней</p>
              <p className="text-sm text-ink/50">прогноз cashflow</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Pricing Toggle */}
      <div className="flex justify-center">
        <div className="inline-flex rounded-xl border border-white/60 bg-white/80 p-1">
          <button
            className={`rounded-lg px-6 py-2 text-sm font-semibold transition-all ${
              billingPeriod === 'monthly'
                ? 'bg-primary-500 text-white shadow-md'
                : 'text-ink/60 hover:text-ink'
            }`}
            onClick={() => setBillingPeriod('monthly')}
          >
            Помесячно
          </button>
          <button
            className={`rounded-lg px-6 py-2 text-sm font-semibold transition-all ${
              billingPeriod === 'yearly'
                ? 'bg-primary-500 text-white shadow-md'
                : 'text-ink/60 hover:text-ink'
            }`}
            onClick={() => setBillingPeriod('yearly')}
          >
            Ежегодно
            <span className="ml-2 rounded-full bg-emerald-500 px-2 py-0.5 text-xs text-white">
              -17%
            </span>
          </button>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Free Plan */}
        <Card className="relative overflow-hidden bg-white/70 p-8">
          <div className="space-y-6">
            <div>
              <h3 className="text-2xl font-display text-ink">Бесплатный</h3>
              <p className="text-sm text-ink/60 mt-2">Для начала работы</p>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-bold text-ink">0 ₽</span>
              <span className="text-ink/50">/мес</span>
            </div>
            <div className="space-y-3">
              <div className="flex items-start gap-2">
                <span className="text-emerald-500">✓</span>
                <span className="text-sm text-ink/70">Подключение до 3 банков</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-emerald-500">✓</span>
                <span className="text-sm text-ink/70">Базовая аналитика (30 дней)</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-emerald-500">✓</span>
                <span className="text-sm text-ink/70">5 личных целей</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-emerald-500">✓</span>
                <span className="text-sm text-ink/70">Базовые бюджеты</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-ink/30">✗</span>
                <span className="text-sm text-ink/40">Прогнозы cashflow</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-ink/30">✗</span>
                <span className="text-sm text-ink/40">Автоматизация бюджетов</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-ink/30">✗</span>
                <span className="text-sm text-ink/40">AI-рекомендации</span>
              </div>
            </div>
            <Link to="/dashboard">
              <Button variant="ghost" className="w-full border border-white/60 bg-white/80">
                Текущий план
              </Button>
            </Link>
          </div>
        </Card>

        {/* Premium Plan */}
        <Card className="relative overflow-hidden bg-gradient-to-br from-primary-200 via-primary-100 to-white/80 p-8 border-2 border-primary-400">
          <div className="absolute top-4 right-4">
            <span className="rounded-full bg-primary-600 px-3 py-1 text-xs font-semibold text-white">
              РЕКОМЕНДУЕМ
            </span>
          </div>
          <div className="space-y-6">
            <div>
              <h3 className="text-2xl font-display text-ink">Premium</h3>
              <p className="text-sm text-ink/60 mt-2">Для профессионалов</p>
            </div>
            <div className="flex items-baseline gap-2">
              {billingPeriod === 'monthly' ? (
                <>
                  <span className="text-5xl font-bold text-ink">{monthlyPrice} ₽</span>
                  <span className="text-ink/50">/мес</span>
                </>
              ) : (
                <>
                  <span className="text-5xl font-bold text-ink">{Math.round(yearlyPrice / 12)} ₽</span>
                  <span className="text-ink/50">/мес</span>
                  <span className="text-sm text-emerald-600 ml-2">
                    ({yearlyPrice} ₽/год)
                  </span>
                </>
              )}
            </div>
            <div className="space-y-3">
              <div className="flex items-start gap-2">
                <span className="text-primary-600 font-bold">✓</span>
                <span className="text-sm text-ink/90 font-medium">Все из бесплатного +</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-primary-600">✓</span>
                <span className="text-sm text-ink/70">Неограниченное количество банков</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-primary-600">✓</span>
                <span className="text-sm text-ink/70">Расширенная аналитика (до 365 дней)</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-primary-600">✓</span>
                <span className="text-sm text-ink/70">Уведомления о превышении бюджета</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-primary-600">✓</span>
                <span className="text-sm text-ink/70">AI-рекомендации по оптимизации</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-primary-600">✓</span>
                <span className="text-sm text-ink/70">Неограниченные семейные цели</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-emerald-500">🚀</span>
                <span className="text-sm text-ink/70">Прогноз cashflow до 180 дней <span className="text-xs text-emerald-600">(скоро)</span></span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-emerald-500">🚀</span>
                <span className="text-sm text-ink/70">Автопилот бюджета <span className="text-xs text-emerald-600">(скоро)</span></span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-emerald-500">🚀</span>
                <span className="text-sm text-ink/70">Сценарии "что если" <span className="text-xs text-emerald-600">(скоро)</span></span>
              </div>
            </div>
            <Button 
              variant="primary" 
              className="w-full text-lg py-4"
              onClick={handleSubscribe}
            >
              Попробовать 14 дней бесплатно
            </Button>
            <p className="text-xs text-center text-ink/50">
              Отмена в любой момент. Без обязательств.
            </p>
          </div>
        </Card>
      </div>

      {/* Features Grid */}
      <div className="space-y-6">
        <h2 className="text-3xl font-display text-ink text-center">
          Что входит в Premium
        </h2>
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="bg-gradient-to-br from-emerald-50 to-white/70 p-6">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-4xl">👨‍👩‍👧</span>
                <span className="px-2 py-1 bg-emerald-500 text-white text-xs rounded-full font-semibold">ГОТОВО</span>
              </div>
              <h3 className="text-xl font-semibold text-ink">Family Banking Hub</h3>
              <p className="text-sm text-ink/60">
                Совместное управление финансами семьи. Общие счета, цели, бюджеты и переводы с контролем доступа.
              </p>
              <div className="pt-2 space-y-1 text-sm text-ink/50">
                <div>✓ Совместные счета</div>
                <div>✓ Семейные цели и бюджеты</div>
                <div>✓ Лимиты для членов семьи</div>
              </div>
            </div>
          </Card>

          <Card className="bg-gradient-to-br from-blue-50 to-white/70 p-6">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-4xl">📊</span>
                <span className="px-2 py-1 bg-emerald-500 text-white text-xs rounded-full font-semibold">ГОТОВО</span>
              </div>
              <h3 className="text-xl font-semibold text-ink">Глубокая аналитика</h3>
              <p className="text-sm text-ink/60">
                AI-рекомендации на основе ваших трат. Визуализация трендов, прогнозы и персональные советы по экономии.
              </p>
              <div className="pt-2 space-y-1 text-sm text-ink/50">
                <div>✓ Анализ до 365 дней</div>
                <div>✓ AI-рекомендации</div>
                <div>✓ Графики и тренды</div>
              </div>
            </div>
          </Card>

          <Card className="bg-gradient-to-br from-purple-50 to-white/70 p-6">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-4xl">🚀</span>
                <span className="px-2 py-1 bg-yellow-500 text-white text-xs rounded-full font-semibold">В РАЗРАБОТКЕ</span>
              </div>
              <h3 className="text-xl font-semibold text-ink">Автопилот & Прогнозы</h3>
              <p className="text-sm text-ink/60">
                Cashflow прогнозы до 180 дней. Автоматическая коррекция бюджетов. Сценарии "что если" для планирования.
              </p>
              <div className="pt-2 space-y-1 text-sm text-ink/50">
                <div>🚧 Прогноз cashflow</div>
                <div>🚧 Автопилот бюджета</div>
                <div>🚧 Симуляция сценариев</div>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Social Proof */}
      <Card className="bg-gradient-to-r from-primary-50 to-white/70 p-8">
        <div className="grid gap-8 md:grid-cols-3 text-center">
          <div>
            <p className="text-4xl font-bold text-primary-600">12 400 ₽</p>
            <p className="text-sm text-ink/60 mt-2">средняя экономия пользователей Premium за квартал</p>
          </div>
          <div>
            <p className="text-4xl font-bold text-primary-600">87%</p>
            <p className="text-sm text-ink/60 mt-2">пользователей достигают целей быстрее</p>
          </div>
          <div>
            <p className="text-4xl font-bold text-primary-600">3 месяца</p>
            <p className="text-sm text-ink/60 mt-2">в среднем ускорение достижения финансовых целей</p>
          </div>
        </div>
      </Card>

      {/* FAQ */}
      <div className="space-y-4">
        <h2 className="text-2xl font-display text-ink text-center">Частые вопросы</h2>
        <div className="space-y-3">
          <Card className="bg-white/70 p-6">
            <h4 className="font-semibold text-ink">Как работает пробный период?</h4>
            <p className="text-sm text-ink/60 mt-2">
              Первые 14 дней бесплатно. Вы можете отменить подписку в любой момент,
              и с вас не спишут ни копейки.
            </p>
          </Card>
          <Card className="bg-white/70 p-6">
            <h4 className="font-semibold text-ink">Можно ли отменить подписку?</h4>
            <p className="text-sm text-ink/60 mt-2">
              Да, отмена доступна в один клик в настройках. Подписка останется активной
              до конца оплаченного периода.
            </p>
          </Card>
          <Card className="bg-white/70 p-6">
            <h4 className="font-semibold text-ink">Какие способы оплаты поддерживаются?</h4>
            <p className="text-sm text-ink/60 mt-2">
              Банковские карты (Visa, Mastercard, Мир), Apple Pay, Google Pay,
              СБП (Система быстрых платежей).
            </p>
          </Card>
        </div>
      </div>

      {/* CTA */}
      <Card className="relative overflow-hidden bg-gradient-to-br from-primary-400 via-primary-500 to-primary-600 p-12 text-center text-white">
        <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.2),transparent_70%)]" />
        <div className="relative z-10 space-y-6">
          <h2 className="text-4xl font-display">Начните экономить уже сегодня</h2>
          <p className="text-lg opacity-90 max-w-2xl mx-auto">
            Присоединяйтесь к тысячам пользователей, которые оптимизировали свои финансы с FinanceHub Premium
          </p>
          <Button 
            onClick={handleSubscribe}
            className="bg-white text-primary-600 hover:bg-white/90 px-8 py-4 text-lg font-semibold"
          >
            Попробовать Premium бесплатно
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default PremiumPage;

