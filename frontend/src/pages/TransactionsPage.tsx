import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import type { Transaction } from '../types';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import { formatCurrency } from '../utils/formatters';

const TransactionsPage = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [accountFilter, setAccountFilter] = useState<string>('all');
  const [periodFilter, setPeriodFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'amount'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  useEffect(() => {
    loadTransactions();
    loadAccounts();
  }, []);

  const loadTransactions = async () => {
    try {
      const data = await api.getTransactions();
      setTransactions(data);
    } catch (error) {
      console.error('Failed to load transactions:', error);
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  const loadAccounts = async () => {
    try {
      const data = await api.getAccounts();
      setAccounts(data);
    } catch (error) {
      console.error('Failed to load accounts:', error);
      setAccounts([]);
    }
  };

  const filtered = useMemo(() => {
    let result = transactions;
    
    // Фильтр по типу
    if (typeFilter !== 'all') {
      result = result.filter(t => t.transaction_type === typeFilter);
    }
    
    // Фильтр по счету
    if (accountFilter !== 'all') {
      result = result.filter(t => t.account_id === parseInt(accountFilter));
    }
    
    // Фильтр по периоду
    if (periodFilter !== 'all') {
      const now = new Date();
      const periodMap: Record<string, number> = {
        '7d': 7,
        '30d': 30,
        '90d': 90,
        '1y': 365
      };
      const days = periodMap[periodFilter];
      if (days) {
        const cutoffDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
        result = result.filter(t => new Date(t.transaction_date) >= cutoffDate);
      }
    }
    
    // Поиск
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(t => 
        t.description?.toLowerCase().includes(query) ||
        t.category?.name?.toLowerCase().includes(query) ||
        t.amount.toString().includes(query)
      );
    }
    
    // Сортировка
    result = [...result].sort((a, b) => {
      if (sortBy === 'date') {
        const diff = new Date(a.transaction_date).getTime() - new Date(b.transaction_date).getTime();
        return sortOrder === 'asc' ? diff : -diff;
      } else {
        const diff = a.amount - b.amount;
        return sortOrder === 'asc' ? diff : -diff;
      }
    });
    
    return result;
  }, [transactions, typeFilter, accountFilter, periodFilter, searchQuery, sortBy, sortOrder]);

  // Пагинация
  const totalPages = Math.ceil(filtered.length / itemsPerPage);
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filtered.slice(startIndex, startIndex + itemsPerPage);
  }, [filtered, currentPage]);

  // Сбросить страницу при изменении фильтров
  useEffect(() => {
    setCurrentPage(1);
  }, [typeFilter, accountFilter, periodFilter, searchQuery, sortBy, sortOrder]);

  const toggleSort = (column: 'date' | 'amount') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  if (loading) {
    return <div className="h-28 bg-gray-200 animate-pulse rounded-xl" />;
  }

  const handleExport = async (format: 'csv' | 'pdf' | 'excel') => {
    try {
      const token = localStorage.getItem('access_token');
      const url = `http://localhost:8000/api/v1/export/transactions/${format}?from_date=&to_date=`;
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Export failed');
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `transactions_${Date.now()}.${format === 'excel' ? 'xlsx' : format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Export error:', error);
      alert('Ошибка экспорта. Попробуйте снова.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-display text-ink">Транзакции</h1>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => handleExport('pdf')} title="Экспорт в PDF">
            📑 PDF
          </Button>
        </div>
      </div>

      {/* Фильтры и поиск */}
      <Card className="p-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          {/* Поиск */}
          <div className="lg:col-span-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45 mb-2 block">🔍 Поиск</label>
            <input
              type="text"
              placeholder="Описание, категория, сумма..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-2 text-sm text-ink placeholder:text-ink/40 focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-200/50"
            />
          </div>

          {/* Фильтр по счету */}
          <div>
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45 mb-2 block">Счет</label>
            <select
              value={accountFilter}
              onChange={(e) => setAccountFilter(e.target.value)}
              className="w-full rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-2 text-sm text-ink focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-200/50"
            >
              <option value="all">Все счета</option>
              {accounts.map(acc => {
                // Создаем УНИКАЛЬНОЕ читаемое название счета
                const last4 = acc.account_number ? acc.account_number.slice(-4) : acc.id;
                const bankName = acc.bank_name || acc.bank_code || '';
                const accountType = acc.account_name || 'Счет';
                
                // Формат: "Checking счет (**1234) - Virtual Bank"
                const displayName = `${accountType} (**${last4})${bankName ? ` - ${bankName}` : ''}`;
                
                return (
                  <option key={acc.id} value={acc.id}>
                    {displayName}
                  </option>
                );
              })}
            </select>
          </div>

          {/* Фильтр по типу */}
          <div>
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45 mb-2 block">Тип</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-2 text-sm text-ink focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-200/50"
            >
              <option value="all">Все</option>
              <option value="income">Доходы</option>
              <option value="expense">Расходы</option>
            </select>
          </div>

          {/* Фильтр по периоду */}
          <div>
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45 mb-2 block">Период</label>
            <select
              value={periodFilter}
              onChange={(e) => setPeriodFilter(e.target.value)}
              className="w-full rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-2 text-sm text-ink focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-200/50"
            >
              <option value="all">Все время</option>
              <option value="7d">7 дней</option>
              <option value="30d">30 дней</option>
              <option value="90d">90 дней</option>
              <option value="1y">1 год</option>
            </select>
          </div>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-1 lg:grid-cols-1">
          {/* Сортировка */}
          <div>
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45 mb-2 block">Сортировка</label>
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [newSortBy, newSortOrder] = e.target.value.split('-') as ['date' | 'amount', 'asc' | 'desc'];
                setSortBy(newSortBy);
                setSortOrder(newSortOrder);
              }}
              className="w-full rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-2 text-sm text-ink focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-200/50"
            >
              <option value="date-desc">Дата (сначала новые)</option>
              <option value="date-asc">Дата (сначала старые)</option>
              <option value="amount-desc">Сумма (по убыванию)</option>
              <option value="amount-asc">Сумма (по возрастанию)</option>
            </select>
          </div>
        </div>

        {/* Статистика */}
        <div className="mt-4 flex items-center gap-6 text-sm text-ink/60">
          <span>Всего транзакций: <strong className="text-ink">{transactions.length}</strong></span>
          <span>Отфильтровано: <strong className="text-ink">{filtered.length}</strong></span>
          <span>Страница: <strong className="text-ink">{currentPage} из {totalPages || 1}</strong></span>
        </div>
      </Card>

      <Card>
        {filtered.length === 0 ? (
          <div className="text-ink/50 text-center py-10">Нет транзакций для отображения</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-white/30">
              <thead className="bg-white/40">
                <tr>
                  <th 
                    className="px-4 py-3 text-left text-xs font-semibold text-ink/60 uppercase tracking-wider cursor-pointer hover:bg-white/60 transition-colors"
                    onClick={() => toggleSort('date')}
                  >
                    Дата {sortBy === 'date' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-ink/60 uppercase tracking-wider">Описание</th>
                  <th 
                    className="px-4 py-3 text-right text-xs font-semibold text-ink/60 uppercase tracking-wider cursor-pointer hover:bg-white/60 transition-colors"
                    onClick={() => toggleSort('amount')}
                  >
                    Сумма {sortBy === 'amount' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white/20 divide-y divide-white/20">
                {paginatedData.map((t) => (
                  <tr key={t.id} className="hover:bg-white/40 transition-colors">
                    <td className="px-4 py-3 text-sm text-ink">{new Date(t.transaction_date).toLocaleString('ru-RU')}</td>
                    <td className="px-4 py-3 text-sm text-ink">
                      <div className="font-medium">{t.description || 'Транзакция'}</div>
                      {t.merchant && <div className="text-ink/50 text-xs mt-1">{t.merchant}</div>}
                    </td>
                    <td className={"px-4 py-3 text-sm font-semibold text-right " + (t.transaction_type==='income'? 'text-primary-600':'text-roseflare')}>
                      {t.transaction_type === 'income' ? '+' : '-'}{formatCurrency(Number(t.amount))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Пагинация */}
        {totalPages > 1 && (
          <div className="border-t border-white/30 bg-white/20 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-ink/60">
                Показано {((currentPage - 1) * itemsPerPage) + 1}–{Math.min(currentPage * itemsPerPage, filtered.length)} из {filtered.length}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                  className="border border-white/30"
                >
                  ««
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="border border-white/30"
                >
                  ‹
                </Button>
                
                {/* Номера страниц */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const pageNum = currentPage <= 3 
                    ? i + 1 
                    : currentPage >= totalPages - 2 
                      ? totalPages - 4 + i 
                      : currentPage - 2 + i;
                  
                  if (pageNum < 1 || pageNum > totalPages) return null;
                  
                  return (
                    <Button
                      key={pageNum}
                      size="sm"
                      variant={pageNum === currentPage ? 'primary' : 'ghost'}
                      onClick={() => setCurrentPage(pageNum)}
                      className={pageNum === currentPage ? '' : 'border border-white/30'}
                    >
                      {pageNum}
                    </Button>
                  );
                })}

                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="border border-white/30"
                >
                  ›
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setCurrentPage(totalPages)}
                  disabled={currentPage === totalPages}
                  className="border border-white/30"
                >
                  »»
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default TransactionsPage;

