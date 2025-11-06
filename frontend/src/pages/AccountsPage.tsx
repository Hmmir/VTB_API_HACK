import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import type { Account, BankConnection } from '../types';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import ConnectBankModal, { type SecurityEventPayload } from '../components/accounts/ConnectBankModal';
import Modal from '../components/common/Modal';
import toast from 'react-hot-toast';
import { formatCurrency, formatCompactCurrency } from '../utils/formatters';

const BANK_NAMES: Record<string, string> = {
  vbank: 'Virtual Bank',
  abank: 'Awesome Bank',
  sbank: 'Smart Bank'
};

const BANK_ICONS: Record<string, string> = {
  vbank: '💜',
  abank: '🟢',
  sbank: '🔵'
};

type TransferForm = {
  from_account_id: string;
  to_account_id: string;
  amount: string;
  description: string;
};

type SecurityEvent = SecurityEventPayload & {
  id: string;
  timestamp: string;
};

const SECURITY_LOG_STORAGE_KEY = 'financehub:security-log';

const AccountsPage = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [connections, setConnections] = useState<BankConnection[]>([]);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [connectModalOpen, setConnectModalOpen] = useState(false);
  const [expandedBank, setExpandedBank] = useState<string | null>(null);
  const [transferModalOpen, setTransferModalOpen] = useState(false);
  const [transferForm, setTransferForm] = useState<TransferForm>({
    from_account_id: '',
    to_account_id: '',
    amount: '',
    description: ''
  });

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    const raw = localStorage.getItem(SECURITY_LOG_STORAGE_KEY);
    if (raw) {
      try {
        const parsed: SecurityEvent[] = JSON.parse(raw);
        setSecurityEvents(parsed);
      } catch {
        setSecurityEvents([]);
      }
    }
  }, []);

  const persistSecurityEvents = (events: SecurityEvent[]) => {
    if (typeof window === 'undefined') {
      return;
    }
    localStorage.setItem(SECURITY_LOG_STORAGE_KEY, JSON.stringify(events));
  };

  const addSecurityEvent = (event: SecurityEventPayload) => {
    const entry: SecurityEvent = {
      id: `sec-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
      timestamp: new Date().toISOString(),
      ...event
    };
    setSecurityEvents((prev) => {
      const next = [entry, ...prev].slice(0, 10);
      persistSecurityEvents(next);
      return next;
    });
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [accountsData, connectionsData] = await Promise.all([
        api.getAccounts(),
        api.getBankConnections()
      ]);
      setAccounts(accountsData);
      setConnections(connectionsData);
    } catch (error) {
      toast.error('Не удалось загрузить данные счетов');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async (connectionId: number) => {
    const connection = connections.find((item) => item.id === connectionId);
    const bankCode = connection?.bank_provider?.toLowerCase?.();
    const bankName = bankCode ? BANK_NAMES[bankCode] || connection?.bank_provider.toUpperCase() : 'Банк';
    try {
      await api.syncBankConnection(connectionId);
      await loadData();
      toast.success('Данные обновлены');
      addSecurityEvent({
        title: `Синхронизация ${bankName}`,
        description: 'Данные счетов обновлены вручную пользователем.',
        meta: `Коннектор #${connectionId}`
      });
    } catch (error) {
      toast.error('Ошибка синхронизации');
    }
  };

  const handleDeleteConnection = async (connectionId: number) => {
    const connection = connections.find((item) => item.id === connectionId);
    const bankCode = connection?.bank_provider?.toLowerCase?.();
    const bankName = bankCode ? BANK_NAMES[bankCode] || connection?.bank_provider.toUpperCase() : 'Банк';
    if (!window.confirm('Удалить подключение к банку и все связанные счета?')) return;
    try {
      await api.deleteBankConnection(connectionId);
      await loadData();
      toast.success('Подключение удалено');
      addSecurityEvent({
        title: `Удалено подключение ${bankName}`,
        description: 'Доступ к данным отозван. Токены аннулированы.',
        meta: `Коннектор #${connectionId}`
      });
    } catch (error) {
      toast.error('Ошибка удаления');
    }
  };

  const formatAccountLabel = (account?: Account) => {
    if (!account) return 'Неизвестный счет';
    const suffix = account.account_number ? ` • ${account.account_number}` : '';
    return `${account.account_name}${suffix}`;
  };

  const handleDeleteAccount = async (accountId: number, accountName: string) => {
    if (!window.confirm(`Удалить счет "${accountName}"?`)) return;
    try {
      await api.deleteAccount(accountId);
      await loadData();
      toast.success('Счет удален');
      addSecurityEvent({
        title: 'Удален счет',
        description: `Счет ${accountName} удален вместе с историей транзакций.`,
        meta: `ID ${accountId}`
      });
    } catch (error) {
      toast.error('Ошибка удаления счета');
    }
  };

  const handleOpenTransfer = (fromAccountId?: number) => {
    setTransferForm((prev) => ({
      ...prev,
      from_account_id: fromAccountId ? String(fromAccountId) : prev.from_account_id,
      to_account_id: fromAccountId ? '' : prev.to_account_id,
      amount: '',
      description: ''
    }));
    setTransferModalOpen(true);
  };

  const handleTransferSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const { from_account_id, to_account_id, amount, description } = transferForm;

    if (!from_account_id || !to_account_id) {
      toast.error('Выберите счета отправителя и получателя');
      return;
    }

    if (from_account_id === to_account_id) {
      toast.error('Выберите разные счета для перевода');
      return;
    }

    const amountValue = Number(amount);
    if (Number.isNaN(amountValue) || amountValue <= 0) {
      toast.error('Введите корректную сумму перевода');
      return;
    }

    const fromAccount = accounts.find((account) => account.id === Number(from_account_id));
    const toAccount = accounts.find((account) => account.id === Number(to_account_id));

    try {
      await api.transferFunds({
        from_account_id: Number(from_account_id),
        to_account_id: Number(to_account_id),
        amount: amountValue,
        description: description || undefined
      });
      toast.success('Перевод выполнен');
      addSecurityEvent({
        title: 'Внутренний перевод выполнен',
        description: `Переведено ${formatCurrency(amountValue)} ₽ с ${formatAccountLabel(fromAccount)} на ${formatAccountLabel(toAccount)}.`,
        meta: description ? description : undefined
      });
      setTransferModalOpen(false);
      setTransferForm({ from_account_id: '', to_account_id: '', amount: '', description: '' });
      await loadData();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Не удалось выполнить перевод';
      toast.error(message);
    }
  };

  const totalBalance = useMemo(
    () => accounts.reduce((sum, account) => sum + Number(account.balance), 0),
    [accounts]
  );

  const enrichedConnections = useMemo(() =>
    connections.map((connection) => {
      const bankAccounts = accounts.filter((acc) => acc.bank_connection_id === connection.id);
      const total = bankAccounts.reduce((sum, acc) => sum + Number(acc.balance), 0);
      return {
        connection,
        accounts: bankAccounts,
        totalBalance: total
      };
    }),
  [accounts, connections]);

  const accountOptions = useMemo(
    () =>
      accounts.map((account) => ({
        id: account.id,
        label: formatAccountLabel(account),
        balance: Number(account.balance),
        currency: account.currency
      })),
    [accounts]
  );

  const destinationOptions = useMemo(() => {
    if (!transferForm.from_account_id) return accountOptions;
    const fromAccount = accounts.find((acc) => acc.id === Number(transferForm.from_account_id));
    return accountOptions.filter(
      (option) =>
        option.id !== Number(transferForm.from_account_id) && (!fromAccount || option.currency === fromAccount.currency)
    );
  }, [accountOptions, accounts, transferForm.from_account_id]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <span className="rounded-full border border-white/30 bg-white/60 px-4 py-2 text-sm uppercase tracking-[0.32em] text-ink/50">
          Загружаем счета...
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
                <p className="text-xs uppercase tracking-[0.35em] text-ink/45">Мультибанковый контур</p>
                <h1 className="text-4xl font-display text-ink">Все счета под контролем и готовы к переводу</h1>
                <p className="text-sm text-ink/60">
                  На платформе <span className="font-semibold text-primary-700">{connections.length}</span> банковских подключений и{' '}
                  <span className="font-semibold text-primary-700">{accounts.length}</span> активных счетов. Общий баланс -{' '}
                  <span className="font-semibold text-ink">{formatCurrency(totalBalance)} ₽</span>.
          </p>
        </div>
              <div className="flex flex-col items-stretch gap-3 rounded-[1.4rem] border border-white/30 bg-white/70 p-5 shadow-[0_20px_45px_rgba(14,23,40,0.12)]">
                <div className="text-xs uppercase tracking-[0.32em] text-ink/40">Быстрые действия</div>
                <Button variant="primary" size="lg" onClick={() => setConnectModalOpen(true)}>
                  <span className="text-lg">+</span>
                  <span className="ml-2">Подключить банк</span>
                </Button>
                <Button variant="ghost" onClick={() => handleOpenTransfer()} className="border border-white/40 bg-white/60 text-ink">
                  Перевод между счетами
                </Button>
                <div className="rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-3 text-xs text-ink/55">
                  Premium автоматизирует перевод средств, удерживает остатки и уведомляет о кассовых разрывах.
                </div>
              </div>
            </div>

            <Card className="bg-white/80 p-6 shadow-none">
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Общий баланс</p>
                  <p className="mt-2 font-display text-3xl text-ink">{formatCurrency(totalBalance)} ₽</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Подключений</p>
                  <p className="mt-2 font-display text-3xl text-ink">{connections.length}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Счетов</p>
                  <p className="mt-2 font-display text-3xl text-ink">{accounts.length}</p>
                </div>
              </div>
            </Card>
          </div>
        </Card>

        <Card className="relative overflow-hidden bg-gradient-to-br from-primary-500 to-primary-700 p-7 text-white">
          <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.22),transparent_70%)]" />
          <div className="relative z-10 space-y-4">
            <p className="text-xs uppercase tracking-[0.32em] text-white/70">Premium «Cashflow Autopilot»</p>
            <h2 className="font-display text-2xl">Автоматические распределения и сценарии кассовых разрывов</h2>
            <ul className="space-y-2 text-sm text-white/80">
              <li>• Автоматическое смещение остатков по правилам и целям</li>
              <li>• Push-уведомления при снижении остатка ниже лимита</li>
              <li>• A/B тест балансировки между кредитными линиями</li>
            </ul>
            <Button variant="ghost" className="bg-white/20 text-white hover:bg-white/30">
              Подключить Premium 14 дней
        </Button>
      </div>
        </Card>
      </section>

      {securityEvents.length > 0 && (
        <Card className="space-y-4 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.32em] text-ink/40">Журнал безопасности</p>
              <h3 className="mt-2 font-display text-xl text-ink">Последние события подключения и переводов</h3>
            </div>
            <Button variant="ghost" size="sm" className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.26em] text-ink/60" onClick={() => { setSecurityEvents([]); persistSecurityEvents([]); }}>
              Очистить журнал
            </Button>
          </div>
          <div className="space-y-3">
            {securityEvents.slice(0, 6).map((event) => (
              <div key={event.id} className="rounded-[1.1rem] border border-white/40 bg-white/60 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-ink">{event.title}</span>
                  <span className="text-xs text-ink/45">{new Date(event.timestamp).toLocaleString('ru-RU')}</span>
                </div>
                <p className="mt-2 text-xs text-ink/60">{event.description}</p>
                {event.meta && (
                  <p className="mt-1 text-xs text-ink/45">{event.meta}</p>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      <section className="space-y-6">
      {connections.length === 0 ? (
          <Card className="relative overflow-hidden bg-white/70 p-12 text-center">
            <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,rgba(36,176,154,0.15),transparent_65%)]" />
            <div className="relative z-10 space-y-4">
              <span className="text-6xl">🏦</span>
              <h4 className="text-2xl font-display text-ink">Подключите первый банк</h4>
              <p className="text-sm text-ink/60">Синхронизируйте счета, чтобы начать отображать весь денежный поток.</p>
              <Button size="lg" variant="primary" onClick={() => setConnectModalOpen(true)}>
              Подключить банк
            </Button>
          </div>
        </Card>
      ) : (
          <div className="space-y-6">
            {enrichedConnections.map(({ connection, accounts: bankAccounts, totalBalance }) => {
            const isExpanded = expandedBank === connection.bank_provider;
              const gradient = isExpanded
                ? 'from-primary-100/45 via-white/70 to-white/60'
                : 'from-white/60 via-white/70 to-white/60';
            const bankCode = connection.bank_provider.toLowerCase();
              const bankName = BANK_NAMES[bankCode] || connection.bank_provider.toUpperCase();
              const bankIcon = BANK_ICONS[bankCode] || '🏦';
            
            return (
                <Card key={connection.id} className={`relative overflow-hidden bg-gradient-to-br ${gradient} p-6`}>
                  <span className="pointer-events-none absolute -left-16 -top-24 h-48 w-48 rounded-full bg-white/25 blur-3xl" />
                  <div className="relative z-10 space-y-5">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Банк</p>
                        <h3 className="text-xl font-semibold text-ink">{bankIcon} {bankName}</h3>
                        <p className="text-sm text-ink/50">{bankAccounts.length} счет(а) • {formatCurrency(totalBalance)} ₽</p>
                      {connection.last_synced_at && (
                          <p className="text-xs text-ink/40">Обновлено {new Date(connection.last_synced_at).toLocaleString('ru-RU')}</p>
                      )}
                    </div>
                      <div className="flex flex-wrap gap-2">
                        <Button variant="ghost" size="sm" className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.22em] text-ink" onClick={() => handleSync(connection.id)}>
                          Синхронизировать
                        </Button>
                        <Button variant="ghost" size="sm" className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.22em] text-roseflare" onClick={() => handleDeleteConnection(connection.id)}>
                          Удалить
                    </Button>
                        <Button variant="ghost" size="sm" className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.22em] text-ink" onClick={() => setExpandedBank(isExpanded ? null : connection.bank_provider)}>
                          {isExpanded ? 'Свернуть' : 'Показать счета'}
                    </Button>
                  </div>
                </div>

                {isExpanded && (
                      <div className="grid gap-4 md:grid-cols-2">
                        {bankAccounts.map((account) => (
                          <Card key={account.id} className="relative overflow-hidden bg-white/80 p-5">
                            <div className="flex items-start justify-between gap-4">
                              <div className="space-y-1">
                                <p className="text-xs uppercase tracking-[0.26em] text-ink/40">{account.account_type.toUpperCase()}</p>
                                <h4 className="text-lg font-semibold text-ink">{account.account_name}</h4>
                                {account.account_number && (
                                  <p className="text-xs text-ink/50">{account.account_number}</p>
                                )}
                      </div>
                              <div className="text-right">
                                <p className="text-xs text-ink/45">Баланс</p>
                                <p className="text-lg font-semibold text-ink">{formatCurrency(Number(account.balance))} ₽</p>
                              </div>
                            </div>

                            <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-white/40 pt-3 text-xs text-ink/50">
                              <span>Обновлено {account.last_synced_at ? new Date(account.last_synced_at).toLocaleString('ru-RU') : 'в реальном времени'}</span>
                              <div className="flex gap-2">
                                <Button variant="ghost" size="sm" className="border border-white/40 bg-white/60 text-ink" onClick={() => handleOpenTransfer(account.id)}>
                                  Перевести
                                </Button>
                                <Button variant="ghost" size="sm" className="border border-white/40 bg-white/60 text-roseflare" onClick={() => handleDeleteAccount(account.id, account.account_name)}>
                                  Удалить
                                </Button>
                              </div>
                            </div>
                          </Card>
                        ))}
                      </div>
                    )}
                  </div>
              </Card>
            );
          })}
        </div>
      )}
      </section>

      <ConnectBankModal
        open={connectModalOpen}
        onClose={() => setConnectModalOpen(false)}
        onConnected={(event) => {
          void loadData();
          if (event) {
            addSecurityEvent(event);
          }
        }}
      />

      <Modal title="Перевод между счетами" open={transferModalOpen} onClose={() => setTransferModalOpen(false)}>
        <form onSubmit={handleTransferSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Со счета</label>
            <select
              value={transferForm.from_account_id}
              onChange={(e) => setTransferForm((prev) => ({ ...prev, from_account_id: e.target.value, to_account_id: '' }))}
              className="input-field"
              required
            >
              <option value="">Выберите счет</option>
              {accountOptions.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label} • {formatCurrency(option.balance)} ₽
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">На счет</label>
            <select
              value={transferForm.to_account_id}
              onChange={(e) => setTransferForm((prev) => ({ ...prev, to_account_id: e.target.value }))}
              className="input-field"
              required
            >
              <option value="">Выберите счет</option>
              {destinationOptions.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label} • {formatCurrency(option.balance)} ₽
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Сумма (₽)</label>
            <input
              type="number"
              min="1"
              value={transferForm.amount}
              onChange={(e) => setTransferForm((prev) => ({ ...prev, amount: e.target.value }))}
              className="input-field"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Комментарий (опционально)</label>
            <textarea
              value={transferForm.description}
              onChange={(e) => setTransferForm((prev) => ({ ...prev, description: e.target.value }))}
              className="input-field min-h-[100px]"
              placeholder="Например: перемещение под финансовую цель"
            />
          </div>

          <div className="rounded-[1.1rem] border border-white/40 bg-white/60 px-4 py-3 text-xs text-ink/55">
            Переводы выполняются мгновенно. Premium позволит настроить расписание и правила автоперераспределения.
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setTransferModalOpen(false)}
              className="border border-white/40 bg-white/60 text-xs uppercase tracking-[0.26em] text-ink/70"
            >
              Отмена
            </Button>
            <Button type="submit" variant="primary">
              Выполнить перевод
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default AccountsPage;
