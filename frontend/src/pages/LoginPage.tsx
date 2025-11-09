import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import toast from 'react-hot-toast';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login({ email, password });
      toast.success('Вход выполнен!');
      navigate('/');
    } catch (err: any) {
      console.error('Login error details:', err.response?.data);
      let errorMessage = 'Ошибка входа';
      
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ');
        } else {
          errorMessage = JSON.stringify(err.response.data.detail);
        }
      }
      
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-noise-soft">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-[-15%] top-[-10%] h-[28rem] w-[28rem] rounded-full bg-primary-200/30 blur-[120px]" />
        <div className="absolute right-[-18%] top-[20%] h-[30rem] w-[30rem] rounded-full bg-roseflare/20 blur-[150px]" />
        <div className="absolute bottom-[-12%] left-[40%] h-[22rem] w-[45rem] rounded-full bg-glow/30 blur-[180px]" />
      </div>

      <div className="relative z-10 grid min-h-screen items-center gap-16 px-6 py-16 lg:grid-cols-[1.1fr_minmax(0,0.9fr)] lg:px-12">
        <div className="hidden flex-col gap-10 pr-12 lg:flex">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-ink/40">FinanceHub · мультибанк</p>
            <h1 className="mt-4 text-5xl font-display text-ink">
              Интерфейс, где банки играют ансамблем
            </h1>
            <p className="mt-4 max-w-xl text-sm text-ink/60">
              Подключайте счета из разных банков, управляйте финансами в одном месте, получайте персональные рекомендации
              и используйте ГОСТ-шифрование для максимальной безопасности ваших данных.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card className="p-6">
              <p className="text-xs uppercase tracking-[0.26em] text-ink/45">ГОСТ-канал</p>
              <p className="mt-3 font-display text-xl text-ink">Шифрование уровня ЦБ РФ</p>
              <p className="mt-2 text-xs text-ink/60">Активируйте режим еще до входа - демо-доступ уже ждет жюри.</p>
            </Card>
            <Card className="p-6">
              <p className="text-xs uppercase tracking-[0.26em] text-ink/45">Режим демо</p>
              <p className="mt-3 font-display text-xl text-ink">Готовые профили</p>
              <p className="mt-2 text-xs text-ink/60">Заполните входные поля в один тап и сразу демонстрируйте сценарии.</p>
            </Card>
          </div>
        </div>

        <Card className="mx-auto w-full max-w-md border-white/30 bg-white/80 p-10">
          <div className="space-y-4 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-[1.4rem_1.4rem_0.9rem_0.9rem] bg-primary-500 text-white shadow-[0_12px_30px_rgba(36,176,154,0.35)]">
              FH
            </div>
            <h2 className="text-3xl font-display text-ink">Войдите в оркестр</h2>
            <p className="text-sm text-ink/60">Выберите подходящий ключ доступа или используйте свои учетные данные.</p>
          </div>

          <div className="mt-8">
            <div className="rounded-[1.4rem] border border-primary-200 bg-primary-100/70 p-4">
              <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.25em] text-primary-700">
                <span>Командные клиенты</span>
                <span>team075-x</span>
              </div>
              <Button
                onClick={() => {
                  const randomNum = Math.floor(Math.random() * 10) + 1;
                  setEmail(`team075-${randomNum}`);
                  setPassword('1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di');
                }}
                variant="secondary"
                size="sm"
                className="mt-3 w-full"
                type="button"
              >
                🎲 Сгенерировать логин
              </Button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label htmlFor="email" className="block text-xs font-semibold uppercase tracking-[0.26em] text-ink/50">
                Login
              </label>
              <input
                id="email"
                type="text"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field mt-2"
                placeholder="demo или team075-1"
              />
              <p className="mt-2 text-xs text-ink/45">Используйте логин без домена: demo, team075-1 ... team075-10</p>
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-semibold uppercase tracking-[0.26em] text-ink/50">
                Пароль
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field mt-2"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="rounded-[1.2rem] border border-roseflare/40 bg-roseflare/10 px-4 py-3 text-sm font-semibold text-roseflare">
                {error}
              </div>
            )}

            <Button type="submit" disabled={loading} className="w-full" variant="primary">
              {loading ? 'Вход...' : 'Войти'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-ink/60">
            Нет аккаунта?{' '}
            <Link to="/register" className="font-semibold text-primary-600 hover:text-primary-700">
              Зарегистрироваться
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;

