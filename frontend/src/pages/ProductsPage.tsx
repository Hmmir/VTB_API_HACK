import { useEffect, useState } from 'react';
import { api } from '../services/api';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import toast from 'react-hot-toast';

interface Product {
  productId: string;
  productName: string;
  productType: string;
  interestRate?: number;
  minAmount?: number;
  maxAmount?: number;
  termMonths?: number;
  bank_name?: string;
  bank_code?: string;
}

interface Account {
  id: number;
  account_number: string;
  account_name: string;
  balance: number;
  bank_name?: string;
}

const ProductsPage = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [agreements, setAgreements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    product_id: '',
    account_id: '',
    amount: '',
    term_months: '12'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Загружаем продукты из всех банков
      const productsData = await api.getBankProducts({});
      setProducts(Array.isArray(productsData.products) ? productsData.products : []);
      
      // Загружаем счета пользователя
      const accountsData = await api.getAccounts();
      setAccounts(accountsData);
      
      // Загружаем договоры пользователя
      try {
        const agreementsRes = await api.get('/products/agreements');
        console.log('Agreements response:', agreementsRes);
        setAgreements(agreementsRes.data.agreements || agreementsRes.data || []);
      } catch (err) {
        console.error('Failed to load agreements:', err);
        setAgreements([]);
      }
    } catch (error: any) {
      console.error('Load error:', error);
      toast.error('Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = () => {
    setFormData({
      product_id: '',
      account_id: accounts.length > 0 ? String(accounts[0].id) : '',
      amount: '',
      term_months: '12'
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.product_id) {
      toast.error('Выберите продукт');
      return;
    }

    try {
      console.log('Creating product agreement...');
      await api.createProductAgreement({
        bank_product_id: formData.product_id,
        linked_account_id: Number(formData.account_id),
        amount: Number(formData.amount),
        term_months: Number(formData.term_months)
      });
      
      console.log('Product created successfully!');
      toast.success('Продукт успешно открыт!');
      setShowModal(false);
      
      // Обновляем список договоров
      console.log('Reloading data...');
      await loadData();
      console.log('Data reloaded!');
    } catch (error: any) {
      console.error('Open product error:', error);
      toast.error(error.response?.data?.detail || 'Не удалось открыть продукт');
    }
  };

  const formatCurrency = (value?: number | null) => {
    if (value === undefined || value === null || isNaN(Number(value))) return '—';
    return Number(value).toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <span className="rounded-full border border-white/30 bg-white/60 px-4 py-2 text-sm uppercase tracking-[0.32em] text-ink/50">
          Загрузка...
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section>
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-display text-ink">📦 Банковские продукты</h1>
              <p className="text-sm text-ink/60 mt-2">
                Управление вашими банковскими продуктами
              </p>
            </div>
            <Button onClick={handleOpenModal} variant="primary">
              + Открыть продукт
            </Button>
          </div>
        </Card>
      </section>

      <section>
        {agreements.length === 0 ? (
          <Card className="p-12 text-center bg-white/70">
            <div className="space-y-4">
              <span className="text-6xl">📦</span>
              <h4 className="text-2xl font-display text-ink">У вас нет активных продуктов</h4>
              <p className="text-sm text-ink/60">
                Нажмите "Открыть продукт" чтобы выбрать депозит, кредит или карту
              </p>
            </div>
          </Card>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            {agreements.map((agreement: any) => (
              <Card key={agreement.id} className="bg-gradient-to-br from-primary-50/40 via-white/70 to-white/60 p-6">
                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.28em] text-ink/40">
                        {agreement.product_type || 'Продукт'}
                      </p>
                      <h3 className="mt-1 text-xl font-semibold text-ink">Договор #{agreement.agreement_number}</h3>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      agreement.status === 'draft' ? 'bg-yellow-100 text-yellow-700' :
                      agreement.status === 'active' ? 'bg-green-100 text-green-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {agreement.status === 'draft' ? 'Черновик' :
                       agreement.status === 'active' ? 'Активен' :
                       agreement.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-3 text-xs">
                    <div>
                      <p className="text-ink/60">Сумма</p>
                      <p className="mt-1 font-semibold text-ink">{formatCurrency(agreement.amount)} ₽</p>
                    </div>
                    <div>
                      <p className="text-ink/60">Ставка</p>
                      <p className="mt-1 font-semibold text-ink">{agreement.interest_rate}%</p>
                    </div>
                    <div>
                      <p className="text-ink/60">Срок</p>
                      <p className="mt-1 font-semibold text-ink">{agreement.term_months} мес.</p>
                    </div>
                    <div>
                      <p className="text-ink/60">Дата начала</p>
                      <p className="mt-1 font-semibold text-ink">
                        {new Date(agreement.start_date).toLocaleDateString('ru-RU')}
                      </p>
                    </div>
                  </div>

                  {agreement.status === 'draft' && (
                    <Button variant="primary" className="w-full">
                      Подписать договор
                    </Button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      <Modal
        title="Открыть продукт"
        open={showModal}
        onClose={() => setShowModal(false)}
      >
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Выберите продукт</label>
            <select
              value={formData.product_id}
              onChange={(e) => {
                const selectedProduct = products.find(p => (p.productId || '') === e.target.value);
                setFormData({ 
                  ...formData, 
                  product_id: e.target.value,
                  amount: selectedProduct?.minAmount ? String(selectedProduct.minAmount) : '',
                  term_months: selectedProduct?.termMonths ? String(selectedProduct.termMonths) : '12'
                });
              }}
              className="input-field"
              required
            >
              <option value="">-- Выберите --</option>
              {products.map((product, idx) => {
                const productId = product.productId || String(idx);
                const bankCode = product.bank_code || 'unknown';
                const uniqueKey = `${bankCode}-${productId}`; // Уникальный ключ с банком
                const productName = product.productName || 'Продукт';
                const rate = product.interestRate ? ` (${product.interestRate}%)` : '';
                const bank = product.bank_name || product.bank_code || '';
                
                return (
                  <option key={uniqueKey} value={productId}>
                    {productName}{rate} - {bank}
                  </option>
                );
              })}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Сумма (₽)</label>
            <input
              type="number"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              className="input-field"
              min="0"
              required
            />
            {formData.product_id && (() => {
              const selected = products.find(p => (p.productId || '') === formData.product_id);
              if (selected?.minAmount || selected?.maxAmount) {
                return (
                  <p className="text-xs text-ink/50">
                    {selected.minAmount && `Мин: ${formatCurrency(selected.minAmount)} ₽`}
                    {selected.minAmount && selected.maxAmount && ', '}
                    {selected.maxAmount && `Макс: ${formatCurrency(selected.maxAmount)} ₽`}
                  </p>
                );
              }
              return null;
            })()}
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Пополнить из счета</label>
            <select
              value={formData.account_id}
              onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
              className="input-field"
              required
            >
              <option value="">-- Выберите счет --</option>
              {accounts.map((acc) => {
                const last4 = acc.account_number ? acc.account_number.slice(-4) : acc.id;
                const displayName = `${acc.account_name || 'Счет'} (**${last4}) - ${formatCurrency(acc.balance)} ₽`;
                return (
                  <option key={acc.id} value={acc.id}>
                    {displayName}
                  </option>
                );
              })}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Срок (месяцы)</label>
            <input
              type="number"
              value={formData.term_months}
              onChange={(e) => setFormData({ ...formData, term_months: e.target.value })}
              className="input-field"
              min="1"
              max="120"
              required
            />
          </div>

          <div className="rounded-[1.1rem] border border-primary-100 bg-primary-50/70 px-4 py-3 text-xs text-ink/55">
            После открытия продукта деньги будут списаны с выбранного счета
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setShowModal(false)}
              className="border border-white/40 bg-white/60"
            >
              Отмена
            </Button>
            <Button type="submit" variant="primary">
              Открыть продукт
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ProductsPage;
