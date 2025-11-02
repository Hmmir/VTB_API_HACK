import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import type { Transaction } from '../types';
import Card from '../components/common/Card';
import Button from '../components/common/Button';

const TransactionsPage = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTransactions();
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

  const [typeFilter, setTypeFilter] = useState<string>('all');
  const filtered = useMemo(() => {
    if (typeFilter === 'all') return transactions;
    return transactions.filter(t => t.transaction_type === typeFilter);
  }, [transactions, typeFilter]);

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
        <h1 className="text-3xl font-bold text-gray-900">Транзакции</h1>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => handleExport('pdf')} title="Экспорт в PDF">
            📑 Экспорт PDF
          </Button>
          <div className="h-6 w-px bg-gray-300"></div>
          <Button variant={typeFilter==='all'?'primary':'secondary'} size="sm" onClick={()=>setTypeFilter('all')}>Все</Button>
          <Button variant={typeFilter==='income'?'primary':'secondary'} size="sm" onClick={()=>setTypeFilter('income')}>Доходы</Button>
          <Button variant={typeFilter==='expense'?'primary':'secondary'} size="sm" onClick={()=>setTypeFilter('expense')}>Расходы</Button>
        </div>
      </div>

      <Card>
        {filtered.length === 0 ? (
          <div className="text-gray-500 text-center py-10">Нет транзакций для отображения</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Дата</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Описание</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">Сумма</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {filtered.map((t) => (
                  <tr key={t.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-700">{new Date(t.transaction_date).toLocaleString('ru-RU')}</td>
                    <td className="px-4 py-3 text-sm text-gray-800">
                      <div className="font-medium">{t.description || 'Транзакция'}</div>
                      {t.merchant && <div className="text-gray-500">{t.merchant}</div>}
                      {t.category && (
                        <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
                          {t.category.name}
                        </span>
                      )}
                    </td>
                    <td className={"px-4 py-3 text-sm font-semibold text-right " + (t.transaction_type==='income'? 'text-green-600':'text-red-600')}>
                      {t.transaction_type === 'income' ? '+' : '-'}{Number(t.amount).toLocaleString('ru-RU')} ₽
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};

export default TransactionsPage;

