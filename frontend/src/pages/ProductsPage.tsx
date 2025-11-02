import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import toast from 'react-hot-toast';

const formatCurrency = (value?: number) =>
  value !== undefined ? value.toLocaleString('ru-RU', { maximumFractionDigits: 0 }) : '-';

const formatPercent = (value?: number) =>
  value !== undefined ? `${value.toFixed(2)}%` : '-';

const PRODUCT_LABELS: Record<string, string> = {
  DEPOSIT: 'Депозит',
  LOAN: 'Кредит',
  CREDIT_CARD: 'Кредитная карта',
  DEBIT_CARD: 'Дебетовая карта',
  CARD: 'Банковская карта',
  INVESTMENT: 'Инвестиционный продукт',
  INSURANCE: 'Страхование'
};

const BANK_GRADIENTS: Record<string, string> = {
  vbank: 'from-primary-100/50 via-white/70 to-white/60',
  abank: 'from-glow/35 via-white/70 to-white/60',
  sbank: 'from-roseflare/18 via-white/70 to-white/60'
};

const ProductsPage = () => {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    bank_code: '',
    product_type: ''
  });

  useEffect(() => {
    void loadProducts();
  }, [filter]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await api.getBankProducts(filter);
      setProducts(data.products || []);
    } catch (error) {
      toast.error('Не удалось загрузить продукты. Подключите банки сначала.');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const featuredProduct = useMemo(() => products[0], [products]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <span className="rounded-full border border-white/30 bg-white/60 px-4 py-2 text-sm uppercase tracking-[0.32em] text-ink/50">
          Собираем витрину офферов...
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(260px,0.9fr)]">
        <Card className="relative overflow-hidden bg-gradient-to-br from-primary-100/70 via-white/75 to-white/55 p-8">
          <span className="pointer-events-none absolute -right-20 -top-16 h-64 w-64 rounded-full bg-primary-300/25 blur-3xl" />
          <div className="relative z-10 space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div className="max-w-xl space-y-3">
                <p className="text-xs uppercase tracking-[0.35em] text-ink/45">Маркетплейс решений</p>
                <h1 className="text-4xl font-display text-ink">Монетизируйте инсайты: предлагаем лучшие продукты партнёров</h1>
                <p className="text-sm text-ink/60">
                  На витрине сейчас{' '}
                  <span className="font-semibold text-primary-700">{products.length}</span>{' '}
                  продуктов. Каждый оффер - потенциальная сделка с партнёрским вознаграждением и шанс укрепить финансовое здоровье клиента.
                </p>
              </div>
              <div className="flex flex-col gap-3 rounded-[1.4rem] border border-white/30 bg-white/70 p-5 shadow-[0_20px_45px_rgba(14,23,40,0.12)]">
                <div className="text-xs uppercase tracking-[0.32em] text-ink/40">Монетизация</div>
                <Button variant="primary" size="lg">
                  Разместить партнёрский оффер
                </Button>
                <div className="rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-3 text-xs text-ink/55">
                  Premium открывает персональную витрину и автоматический расчёт рев-шеринга для подключённых банков.
                </div>
              </div>
            </div>

            {featuredProduct && (
              <Card className="bg-white/80 p-6 shadow-none">
                <div className="flex flex-wrap items-center justify-between gap-6">
                  <div className="space-y-2">
                    <p className="text-xs uppercase tracking-[0.32em] text-ink/45">Рекомендация недели</p>
                    <h2 className="text-2xl font-display text-ink">{featuredProduct.productName || featuredProduct.name}</h2>
                    <p className="text-sm text-ink/60 max-w-prose">
                      {featuredProduct.description || 'Партнёрский продукт с высоким потенциалом конверсии. Используйте его в рекомендациях клиентам.'}
                    </p>
                  </div>
                  <div className="rounded-[1.2rem] border border-primary-200 bg-primary-50/70 px-6 py-4 text-sm text-primary-700">
                    Комиссия партнёра до{' '}
                    <span className="font-semibold">1.8%</span>{' '}
                    от привлечённого объёма. Средняя выручка продукта -
                    <span className="font-semibold"> 4 200 ₽</span> за клиента.
                  </div>
                </div>
              </Card>
            )}
          </div>
        </Card>

        <Card className="relative overflow-hidden bg-gradient-to-br from-roseflare/18 via-white/70 to-white/60 p-7">
          <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.22),transparent_70%)]" />
          <div className="relative z-10 space-y-4 text-ink">
            <p className="text-xs uppercase tracking-[0.32em] text-ink/45">Premium «Партнёрский контур»</p>
            <h2 className="font-display text-xl">Автоматизируйте работу с ревеню: аналитика, воронки, A/B-тесты</h2>
            <ul className="space-y-2 text-sm text-ink/70">
              <li>• Персональные рекомендации продуктов на основе расходов пользователя</li>
              <li>• A/B тесты офферов и отслеживание конверсии в едином дашборде</li>
              <li>• Готовые маркетинговые лендинги под бренд партнёра</li>
            </ul>
            <Button variant="ghost" className="border border-white/30 bg-white/50 text-ink">
              Узнать о партнёрской программе
            </Button>
          </div>
        </Card>
      </section>

      <section className="space-y-6">
        <Card className="p-6">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Банк</label>
              <select
                value={filter.bank_code}
                onChange={(e) => setFilter({ ...filter, bank_code: e.target.value })}
                className="input-field"
              >
                <option value="">Все банки</option>
                <option value="vbank">Virtual Bank</option>
                <option value="abank">Awesome Bank</option>
                <option value="sbank">Smart Bank</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Тип продукта</label>
              <select
                value={filter.product_type}
                onChange={(e) => setFilter({ ...filter, product_type: e.target.value })}
                className="input-field"
              >
                <option value="">Все типы</option>
                <option value="DEPOSIT">Депозиты</option>
                <option value="LOAN">Кредиты</option>
                <option value="CREDIT_CARD">Кредитные карты</option>
                <option value="DEBIT_CARD">Дебетовые карты</option>
                <option value="INVESTMENT">Инвестиции</option>
              </select>
            </div>
            <div className="flex items-end gap-3">
              <Button
                onClick={() => loadProducts()}
                variant="secondary"
                className="border border-white/40 bg-white/70 text-ink"
              >
                Обновить витрину
              </Button>
              <Button
                onClick={() => setFilter({ bank_code: '', product_type: '' })}
                variant="ghost"
                className="border border-white/40 bg-white/60 text-ink"
              >
                Сбросить
              </Button>
            </div>
          </div>
        </Card>

        {products.length === 0 ? (
          <Card className="relative overflow-hidden bg-white/70 p-12 text-center">
            <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,rgba(255,111,145,0.18),transparent_65%)]" />
            <div className="relative z-10 space-y-4">
              <span className="text-6xl">🧭</span>
              <h4 className="text-2xl font-display text-ink">Пока нет подходящих продуктов</h4>
              <p className="text-sm text-ink/60">
                Измените фильтры или подключите дополнительные банки, чтобы расширить выбор.
              </p>
            </div>
          </Card>
        ) : (
          <div className="grid gap-6 lg:grid-cols-3">
            {products.map((product, index) => {
              const bankCode = (product.bank_code || '').toLowerCase();
              const gradient = BANK_GRADIENTS[bankCode] || 'from-primary-50/40 via-white/70 to-white/60';
              const label = PRODUCT_LABELS[product.productType?.toUpperCase()] || product.productType;

              return (
                <Card key={`${product.productId || index}`} className={`relative overflow-hidden bg-gradient-to-br ${gradient} p-6`}>
                  <span className="pointer-events-none absolute -left-12 -top-16 h-40 w-40 rounded-full bg-white/25 blur-3xl" />
                  <div className="relative z-10 space-y-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-2">
                        <p className="text-xs uppercase tracking-[0.28em] text-ink/40">{label}</p>
                        <h3 className="text-xl font-semibold text-ink">{product.productName || product.name}</h3>
                        <p className="text-sm text-ink/60 min-h-[60px]">
                          {product.description || 'Партнёрский продукт, который можно добавить в рекомендации клиентам.'}
                        </p>
                      </div>
                      <span className="rounded-full border border-white/40 bg-white/70 px-3 py-1 text-xs font-semibold text-ink/70">
                        {product.bank_name || product.bank_code || 'Банк'}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-3 text-xs text-ink/60">
                      <div>
                        <p>Ставка</p>
                        <p className="mt-1 font-semibold text-ink">{formatPercent(product.interestRate)}</p>
                      </div>
                      <div>
                        <p>Мин. сумма</p>
                        <p className="mt-1 font-semibold text-ink">{formatCurrency(product.minAmount)} ₽</p>
                      </div>
                      <div>
                        <p>Макс. сумма</p>
                        <p className="mt-1 font-semibold text-ink">{formatCurrency(product.maxAmount)} ₽</p>
                      </div>
                      <div>
                        <p>Срок</p>
                        <p className="mt-1 font-semibold text-ink">{product.term_months ? `${product.term_months} мес.` : 'Гибко'}</p>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/40 pt-4">
                      <a
                        href={product.url || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex"
                      >
                        <Button
                          variant="primary"
                          className="text-xs uppercase tracking-[0.22em]"
                        >
                          Подать заявку
                        </Button>
                      </a>
                      <Button
                        variant="ghost"
                        className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.22em] text-ink"
                      >
                        Добавить в рекомендации
                      </Button>
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

export default ProductsPage;
