import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { ArrowRightOnRectangleIcon, SparklesIcon, SunIcon, MoonIcon } from '@heroicons/react/24/outline';
import Button from './Button';
import Card from './Card';
import { useTheme } from '../../contexts/ThemeContext';

const Layout = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const isNocturne = theme === 'nocturne';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Дашборд', icon: '🏠', tagline: 'Орбитальная сводка' },
    { path: '/accounts', label: 'Счета', icon: '💳', tagline: 'Управление капиталом' },
    { path: '/transactions', label: 'Транзакции', icon: '💸', tagline: 'История потоков' },
    { path: '/analytics', label: 'Аналитика', icon: '📊', tagline: 'Спектр метрик' },
    { path: '/budgets', label: 'Бюджеты', icon: '💰', tagline: 'Контуры планирования' },
    { path: '/goals', label: 'Цели', icon: '🎯', tagline: 'Финансовые векторы' },
    { path: '/products', label: 'Продукты', icon: '🏦', tagline: 'Витрина сервисов' },
    { path: '/recommendations', label: 'Советы', icon: '💡', tagline: 'Персональные инсайты' },
  ];

  const renderNavItem = (item: typeof navItems[number]) => {
    const isRoot = item.path === '/';
    const isActive = isRoot
      ? location.pathname === '/'
      : location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);

    return (
      <Link
        key={item.path}
        to={item.path}
        className={`group relative block overflow-hidden rounded-[1.4rem_1.4rem_0.95rem_0.95rem] border border-white/20 px-5 py-4 transition-all duration-300 ${
          isActive
            ? 'bg-white text-ink shadow-prism'
            : 'bg-white/60 text-ink/70 hover:-translate-y-1 hover:bg-white/80 hover:text-ink'
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className={`text-2xl ${isActive ? 'animate-dash-glow' : ''}`}>{item.icon}</span>
            <div>
              <p className="font-display text-[0.95rem] uppercase tracking-[0.18em]">{item.label}</p>
              <p className="text-xs font-medium text-ink/50 group-hover:text-ink/70 transition-colors">{item.tagline}</p>
            </div>
          </div>
          <span
            aria-hidden
            className={`h-2 w-2 rounded-full ${
              isActive ? 'bg-primary-400 shadow-[0_0_0_4px_rgba(36,176,154,0.18)]' : 'bg-ink/10 group-hover:bg-primary-200'
            }`}
          />
        </div>
      </Link>
    );
  };

  return (
    <div className="relative min-h-screen text-ink">
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute left-[10%] top-[-15%] h-72 w-72 rounded-full bg-primary-200/40 blur-3xl animate-float-slow" />
        <div className="absolute right-[-12%] top-[10%] h-96 w-96 rounded-full bg-roseflare/20 blur-[140px] animate-float-slow" />
        <div className="absolute bottom-[-20%] left-[35%] h-80 w-[40rem] rounded-full bg-glow/25 blur-[160px]" />
      </div>

      <div className="mx-auto max-w-7xl px-4 pb-16 pt-10 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between gap-4 rounded-[1.75rem] border border-white/30 bg-white/70 px-6 py-4 shadow-[0_18px_45px_rgba(14,23,40,0.12)] backdrop-blur-xl">
          <div className="flex items-center gap-4">
            <span className="flex h-12 w-12 items-center justify-center rounded-[1.4rem_1.4rem_0.9rem_0.9rem] bg-primary-500 text-white shadow-[0_12px_30px_rgba(36,176,154,0.35)]">
              <SparklesIcon className="h-6 w-6" />
            </span>
            <div>
              <p className="font-display text-lg uppercase tracking-[0.4em] text-ink/70">FinanceHub</p>
              <p className="text-xs font-medium text-ink/50">Мультибанковая оркестровка</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              className="relative h-11 w-11 rounded-[1.2rem] border border-white/30 bg-white/60 text-ink hover:bg-white/80"
              title={isNocturne ? 'Вернуться к дневной теме' : 'Погрузиться в ночную тему'}
              aria-label="Переключить тему"
            >
              {isNocturne ? <SunIcon className="h-5 w-5" /> : <MoonIcon className="h-5 w-5" />}
            </Button>
            <Card className="hidden items-center gap-3 rounded-[1.3rem] border-white/20 bg-white/70 px-4 py-3 sm:flex">
              <div className="rounded-full bg-primary-200/40 px-3 py-1 text-xs font-semibold text-primary-700">LIVE</div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-ink/40">Контур</p>
                <p className="font-display text-sm text-ink/80">{user?.full_name || user?.email}</p>
              </div>
            </Card>
            <Button variant="ghost" size="sm" onClick={handleLogout} className="text-ink">
              <ArrowRightOnRectangleIcon className="h-4 w-4" />
              <span className="ml-2 text-[0.68rem]">Выйти</span>
            </Button>
          </div>
        </header>

        <div className="mt-10 grid gap-8 lg:grid-cols-[300px_minmax(0,1fr)]">
          <aside className="hidden lg:flex lg:flex-col lg:gap-6">
            <Card className="rounded-[1.85rem] border-white/20 bg-white/60 p-6">
              <p className="text-xs uppercase tracking-[0.28em] text-ink/40">панорамный маршрут</p>
              <h2 className="mt-2 font-display text-xl text-ink">Навигация</h2>
              <div className="mt-4 flex flex-col gap-3">
                {navItems.map(renderNavItem)}
              </div>
            </Card>

            <Card className="rounded-[1.85rem] border-dashed border-white/30 bg-gradient-to-br from-white/60 to-white/30 p-6">
              <p className="text-xs font-medium uppercase tracking-[0.24em] text-ink/40">Синхронизация банков</p>
              <h3 className="mt-3 font-display text-lg text-ink">Мультиканальный профиль</h3>
              <p className="mt-2 text-sm text-ink/60">
                Сбалансируйте традиционные и цифровые банки: подключайте провайдеров, комбинируйте продукты,
                активируйте ГОСТ-канал одним кликом.
              </p>
              <Link
                to="/accounts"
                className="mt-4 inline-flex items-center text-sm font-semibold text-primary-600 hover:text-primary-700"
              >
                Расширить сеть →
              </Link>
            </Card>
          </aside>

          <main className="min-w-0 space-y-8">
            <div className="lg:hidden">
              <div className="space-y-3">
                {navItems.map(renderNavItem)}
              </div>
            </div>
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};

export default Layout;

