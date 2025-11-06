import { useCallback, useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';

import Card from '../components/common/Card';
import Button from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { api } from '../services/api';
import {
  Family,
  FamilyDetail,
  FamilyBudget,
  FamilyGoal,
  FamilyMemberLimit,
  FamilyTransfer,
  FamilyNotification,
  FamilyAnalyticsSummary,
  FamilyMember,
} from '../types';
import { formatCurrency } from '../utils/formatters';

interface BudgetFormState {
  name: string;
  amount: string;
  period: 'weekly' | 'monthly';
  category_id?: string;
}

interface GoalFormState {
  name: string;
  description: string;
  target_amount: string;
  deadline: string;
}

interface TransferFormState {
  to_member_id: string;
  amount: string;
  description: string;
}

interface LimitFormState {
  member_id: string;
  amount: string;
  period: 'weekly' | 'monthly';
}

const defaultBudgetForm: BudgetFormState = {
  name: '',
  amount: '',
  period: 'monthly',
};

const defaultGoalForm: GoalFormState = {
  name: '',
  description: '',
  target_amount: '',
  deadline: '',
};

const defaultTransferForm: TransferFormState = {
  to_member_id: '',
  amount: '',
  description: '',
};

const defaultLimitForm: LimitFormState = {
  member_id: '',
  amount: '',
  period: 'monthly',
};

const emptyAnalytics: FamilyAnalyticsSummary = {
  total_balance: 0,
  total_income: 0,
  total_expense: 0,
  budgets: [],
  member_spending: [],
  category_spending: [],
  goals: [],
};

const FamilyHubPage = () => {
  const [families, setFamilies] = useState<Family[]>([]);
  const [selectedFamilyId, setSelectedFamilyId] = useState<number | null>(null);
  const [familyDetail, setFamilyDetail] = useState<FamilyDetail | null>(null);
  const [budgets, setBudgets] = useState<FamilyBudget[]>([]);
  const [limits, setLimits] = useState<FamilyMemberLimit[]>([]);
  const [goals, setGoals] = useState<FamilyGoal[]>([]);
  const [transfers, setTransfers] = useState<FamilyTransfer[]>([]);
  const [notifications, setNotifications] = useState<FamilyNotification[]>([]);
  const [analytics, setAnalytics] = useState<FamilyAnalyticsSummary>(emptyAnalytics);
  const [loading, setLoading] = useState<boolean>(false);

  const [isCreateFamilyOpen, setIsCreateFamilyOpen] = useState(false);
  const [isJoinFamilyOpen, setIsJoinFamilyOpen] = useState(false);
  const [isBudgetModalOpen, setIsBudgetModalOpen] = useState(false);
  const [isGoalModalOpen, setIsGoalModalOpen] = useState(false);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [isLimitModalOpen, setIsLimitModalOpen] = useState(false);

  const [createFamilyName, setCreateFamilyName] = useState('');
  const [createFamilyDescription, setCreateFamilyDescription] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [budgetForm, setBudgetForm] = useState<BudgetFormState>(defaultBudgetForm);
  const [goalForm, setGoalForm] = useState<GoalFormState>(defaultGoalForm);
  const [transferForm, setTransferForm] = useState<TransferFormState>(defaultTransferForm);
  const [limitForm, setLimitForm] = useState<LimitFormState>(defaultLimitForm);

  const selectedFamily = useMemo(() => families.find((f) => f.id === selectedFamilyId) ?? null, [families, selectedFamilyId]);

  const loadFamilies = useCallback(async () => {
    try {
      const data = await api.listFamilies();
      setFamilies(data);
      if (data.length > 0) {
        setSelectedFamilyId((prev) => prev ?? data[0].id);
      }
    } catch (error) {
      toast.error('Не удалось загрузить семьи');
    }
  }, []);

  const loadFamilyData = useCallback(async (familyId: number) => {
    setLoading(true);
    try {
      const [detail, budgetsData, limitsData, goalsData, transfersData, notificationsData, analyticsData] = await Promise.all([
        api.getFamily(familyId),
        api.listFamilyBudgets(familyId),
        api.listFamilyMemberLimits(familyId),
        api.listFamilyGoals(familyId),
        api.listFamilyTransfers(familyId),
        api.listFamilyNotifications(familyId),
        api.getFamilyAnalytics(familyId),
      ]);

      setFamilyDetail(detail);
      setBudgets(budgetsData);
      setLimits(limitsData);
      setGoals(goalsData);
      setTransfers(transfersData);
      setNotifications(notificationsData);
      setAnalytics(analyticsData);
    } catch (error) {
      toast.error('Ошибка при загрузке данных семьи');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFamilies();
  }, [loadFamilies]);

  useEffect(() => {
    if (selectedFamilyId) {
      loadFamilyData(selectedFamilyId);
    }
  }, [selectedFamilyId, loadFamilyData]);

  const handleCreateFamily = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const family = await api.createFamily({ name: createFamilyName, description: createFamilyDescription });
      toast.success('Семья создана');
      setIsCreateFamilyOpen(false);
      setCreateFamilyName('');
      setCreateFamilyDescription('');
      await loadFamilies();
      setSelectedFamilyId(family.id);
    } catch (error) {
      toast.error('Не удалось создать семью');
    }
  };

  const handleJoinFamily = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const family = await api.joinFamily(joinCode.trim());
      toast.success('Вы присоединились к семье');
      setIsJoinFamilyOpen(false);
      setJoinCode('');
      await loadFamilies();
      setSelectedFamilyId(family.id);
    } catch (error) {
      toast.error('Не удалось присоединиться по коду приглашения');
    }
  };

  const handleRotateInvite = async () => {
    if (!selectedFamilyId) return;
    try {
      const data = await api.rotateFamilyInvite(selectedFamilyId);
      if (familyDetail) {
        setFamilyDetail({ ...familyDetail, invite_code: data.invite_code });
      }
      toast.success('Обновлён код приглашения');
    } catch (error) {
      toast.error('Не удалось обновить код приглашения');
    }
  };

  const handleCreateBudget = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFamilyId) return;
    try {
      await api.createFamilyBudget(selectedFamilyId, {
        name: budgetForm.name,
        amount: Number(budgetForm.amount),
        period: budgetForm.period,
        category_id: budgetForm.category_id ? Number(budgetForm.category_id) : undefined,
      });
      toast.success('Бюджет создан');
      setIsBudgetModalOpen(false);
      setBudgetForm(defaultBudgetForm);
      loadFamilyData(selectedFamilyId);
    } catch (error) {
      toast.error('Не удалось создать бюджет');
    }
  };

  const handleCreateGoal = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFamilyId) return;
    try {
      await api.createFamilyGoal(selectedFamilyId, {
        name: goalForm.name,
        description: goalForm.description,
        target_amount: Number(goalForm.target_amount),
        deadline: goalForm.deadline || undefined,
      });
      toast.success('Цель создана');
      setIsGoalModalOpen(false);
      setGoalForm(defaultGoalForm);
      loadFamilyData(selectedFamilyId);
    } catch (error) {
      toast.error('Не удалось создать цель');
    }
  };

  const handleCreateLimit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFamilyId) return;
    try {
      await api.createFamilyMemberLimit(selectedFamilyId, {
        member_id: Number(limitForm.member_id),
        amount: Number(limitForm.amount),
        period: limitForm.period,
      });
      toast.success('Лимит установлен');
      setIsLimitModalOpen(false);
      setLimitForm(defaultLimitForm);
      loadFamilyData(selectedFamilyId);
    } catch (error) {
      toast.error('Не удалось установить лимит');
    }
  };

  const handleCreateTransfer = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFamilyId) return;
    try {
      await api.createFamilyTransfer(selectedFamilyId, {
        to_member_id: Number(transferForm.to_member_id),
        amount: Number(transferForm.amount),
        description: transferForm.description,
      });
      toast.success('Перевод создан');
      setIsTransferModalOpen(false);
      setTransferForm(defaultTransferForm);
      loadFamilyData(selectedFamilyId);
    } catch (error) {
      toast.error('Не удалось создать перевод');
    }
  };

  const members: FamilyMember[] = familyDetail?.members || [];
  const memberLimitMap = useMemo(() => {
    const map: Record<number, FamilyMemberLimit[]> = {};
    limits.forEach((limit) => {
      if (!map[limit.member_id]) {
        map[limit.member_id] = [];
      }
      map[limit.member_id].push(limit);
    });
    return map;
  }, [limits]);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display text-ink">👨‍👩‍👧 Family Banking Hub</h1>
          <p className="mt-2 text-sm text-ink/60">Управляйте семейными финансами, лимитами и общими целями</p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setIsJoinFamilyOpen(true)}>
            + Присоединиться
          </Button>
          <Button variant="primary" onClick={() => setIsCreateFamilyOpen(true)}>
            + Создать семью
          </Button>
        </div>
      </div>

      {families.length > 0 && (
        <Card className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Активная семья</p>
              <h2 className="mt-1 text-2xl font-semibold text-ink">{selectedFamily?.name}</h2>
              {familyDetail?.invite_code && (
                <div className="mt-2 inline-flex items-center gap-2 rounded-full border border-white/50 bg-white/70 px-3 py-1 text-xs text-ink/70">
                  <span>Код приглашения:</span>
                  <code className="font-mono tracking-wide">{familyDetail.invite_code}</code>
                  <button
                    type="button"
                    className="text-primary-600 hover:underline"
                    onClick={() => {
                      navigator.clipboard.writeText(familyDetail.invite_code);
                      toast.success('Код скопирован в буфер обмена');
                    }}
                  >
                    Скопировать
                  </button>
                </div>
              )}
            </div>
            <div className="flex items-center gap-3">
              <select
                value={selectedFamilyId ?? ''}
                onChange={(event) => setSelectedFamilyId(Number(event.target.value))}
                className="input-field max-w-xs"
              >
                {families.map((family) => (
                  <option key={family.id} value={family.id}>
                    {family.name}
                  </option>
                ))}
              </select>
              <Button variant="ghost" className="border border-white/60 bg-white/70" onClick={handleRotateInvite}>
                Обновить код
              </Button>
            </div>
          </div>
        </Card>
      )}

      {families.length === 0 ? (
        <Card className="p-12 text-center">
          <h3 className="text-2xl font-semibold text-ink">Создайте первую семейную группу</h3>
          <p className="mt-4 text-sm text-ink/60">
            Объедините счета, установите лимиты для детей, планируйте общие цели и следите за бюджетом всей семьи.
          </p>
          <Button variant="primary" className="mt-6" onClick={() => setIsCreateFamilyOpen(true)}>
            Начать
          </Button>
        </Card>
      ) : (
        <div className="space-y-6">
          {loading ? (
            <Card className="p-12 text-center text-ink/60">Загрузка данных семьи...</Card>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <Card className="bg-gradient-to-br from-primary-50 via-white/80 to-white/60">
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Общий баланс</p>
                  <p className="mt-2 text-3xl font-semibold text-ink">
                    {formatCurrency(analytics.total_balance || 0)}
                  </p>
                </Card>
                <Card>
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Доходы / расходы</p>
                  <div className="mt-2 text-sm text-ink/70">
                    <p>Доходы: <span className="font-semibold text-emerald-600">{formatCurrency(analytics.total_income || 0)}</span></p>
                    <p>Расходы: <span className="font-semibold text-rose-600">{formatCurrency(analytics.total_expense || 0)}</span></p>
                  </div>
                </Card>
                <Card>
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Активные цели</p>
                  <p className="mt-2 text-3xl font-semibold text-ink">{goals.length}</p>
                </Card>
                <Card>
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Уведомления</p>
                  <p className="mt-2 text-3xl font-semibold text-ink">{notifications.length}</p>
                </Card>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <Card>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold text-ink">👥 Участники</h3>
                      <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Роли, лимиты и приватность</p>
                    </div>
                    <Button
                      variant="ghost"
                      className="border border-white/60 bg-white/70"
                      onClick={() => setIsLimitModalOpen(true)}
                    >
                      Установить лимит
                    </Button>
                  </div>
                  <div className="mt-4 space-y-3">
                    {members.map((member) => (
                      <div key={member.id} className="rounded-2xl border border-white/60 bg-white/70 p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-semibold text-ink">Пользователь #{member.user_id}</p>
                            <p className="text-xs text-ink/50">
                              Роль: {member.role === 'admin' ? 'Администратор' : 'Участник'} · Статус: {member.status}
                            </p>
                          </div>
                          <div className="text-right text-xs text-ink/50">
                            {member.joined_at ? `В группе с ${new Date(member.joined_at).toLocaleDateString('ru-RU')}` : 'Ожидает подтверждения'}
                          </div>
                        </div>
                        {memberLimitMap[member.id]?.length ? (
                          <div className="mt-3 grid gap-2 rounded-xl border border-white/50 bg-white/70 p-3 text-xs text-ink/60">
                            {memberLimitMap[member.id].map((limit) => (
                              <div key={limit.id} className="flex items-center justify-between">
                                <span>Лимит {limit.period === 'monthly' ? 'в месяц' : 'в неделю'}:</span>
                                <span className="font-semibold text-ink">{formatCurrency(limit.amount)}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="mt-3 rounded-xl border border-dashed border-white/40 bg-white/60 px-3 py-2 text-xs text-ink/50">
                            Лимиты не заданы
                          </p>
                        )}
                      </div>
                    ))}
                    {members.length === 0 && <p className="text-sm text-ink/50">В этой семье пока нет участников.</p>}
                  </div>
                </Card>

                <Card>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold text-ink">📊 Бюджеты</h3>
                      <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Контроль расходов по категориям</p>
                    </div>
                    <Button variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setIsBudgetModalOpen(true)}>
                      + Бюджет
                    </Button>
                  </div>
                  <div className="mt-4 space-y-3">
                    {budgets.map((budget) => (
                      <div key={budget.id} className="flex items-center justify-between rounded-2xl border border-white/60 bg-white/70 p-4">
                        <div>
                          <p className="text-sm font-semibold text-ink">{budget.name}</p>
                          <p className="text-xs text-ink/50">Период: {budget.period === 'monthly' ? 'Месяц' : 'Неделя'}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold text-ink">{formatCurrency(budget.amount)} </p>
                          <p className="text-xs text-ink/50">Статус: {budget.status}</p>
                        </div>
                      </div>
                    ))}
                    {budgets.length === 0 && <p className="text-sm text-ink/50">Добавьте первый бюджет для совместного контроля.</p>}
                  </div>
                </Card>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <Card>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold text-ink">🎯 Семейные цели</h3>
                      <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Краудфандинг внутри семьи</p>
                    </div>
                    <Button variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setIsGoalModalOpen(true)}>
                      + Цель
                    </Button>
                  </div>
                  <div className="mt-4 space-y-3">
                    {goals.map((goal) => {
                      const progress = goal.target_amount > 0 ? Math.min(100, Math.round((goal.current_amount / goal.target_amount) * 100)) : 0;
                      return (
                        <div key={goal.id} className="rounded-2xl border border-white/60 bg-white/70 p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm font-semibold text-ink">{goal.name}</p>
                              <p className="text-xs text-ink/50">Цель: {formatCurrency(goal.target_amount)} · Собрано: {formatCurrency(goal.current_amount)}</p>
                            </div>
                            <span className="text-xs text-primary-600">{progress}%</span>
                          </div>
                          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/60">
                            <div className="h-full rounded-full bg-primary-500" style={{ width: `${progress}%` }} />
                          </div>
                        </div>
                      );
                    })}
                    {goals.length === 0 && <p className="text-sm text-ink/50">Создайте цель, чтобы копить вместе.</p>}
                  </div>
                </Card>

                <Card>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold text-ink">💸 Переводы</h3>
                      <p className="text-xs uppercase tracking-[0.28em] text-ink/45">История и запросы</p>
                    </div>
                    <Button variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setIsTransferModalOpen(true)}>
                      + Перевод
                    </Button>
                  </div>
                  <div className="mt-4 space-y-3">
                    {transfers.map((transfer) => (
                      <div key={transfer.id} className="rounded-2xl border border-white/60 bg-white/70 p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-semibold text-ink">{formatCurrency(transfer.amount)} · {transfer.status}</p>
                            <p className="text-xs text-ink/50">От участника #{transfer.from_member_id} → #{transfer.to_member_id}</p>
                          </div>
                          <p className="text-xs text-ink/50">{new Date(transfer.created_at).toLocaleString('ru-RU')}</p>
                        </div>
                        {transfer.description && (
                          <p className="mt-2 text-xs text-ink/60">{transfer.description}</p>
                        )}
                      </div>
                    ))}
                    {transfers.length === 0 && <p className="text-sm text-ink/50">Здесь появятся запросы и переводы внутри семьи.</p>}
                  </div>
                </Card>
              </div>

              <Card>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-semibold text-ink">🔔 Уведомления</h3>
                    <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Контроль за превышениями и событиями</p>
                  </div>
                </div>
                <div className="mt-4 space-y-3">
                  {notifications.map((notification) => (
                    <div key={notification.id} className="rounded-2xl border border-white/60 bg-white/70 p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-semibold text-ink">Тип: {notification.notification_type}</p>
                          {notification.payload && (
                            <pre className="mt-2 rounded-xl bg-white/90 p-3 text-xs text-ink/70">
                              {JSON.stringify(notification.payload, null, 2)}
                            </pre>
                          )}
                        </div>
                        <p className="text-xs text-ink/50">{new Date(notification.created_at).toLocaleString('ru-RU')}</p>
                      </div>
                    </div>
                  ))}
                  {notifications.length === 0 && <p className="text-sm text-ink/50">Уведомления появятся, когда семья начнёт тратить и копить.</p>}
                </div>
              </Card>
            </>
          )}
        </div>
      )}

      <Modal title="Создать семейную группу" open={isCreateFamilyOpen} onClose={() => setIsCreateFamilyOpen(false)}>
        <form className="space-y-4" onSubmit={handleCreateFamily}>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Название семьи</label>
            <input
              className="input-field"
              value={createFamilyName}
              onChange={(event) => setCreateFamilyName(event.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Описание</label>
            <textarea
              className="input-field min-h-[100px]"
              value={createFamilyDescription}
              onChange={(event) => setCreateFamilyDescription(event.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setIsCreateFamilyOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" variant="primary">
              Создать
            </Button>
          </div>
        </form>
      </Modal>

      <Modal title="Присоединиться по коду" open={isJoinFamilyOpen} onClose={() => setIsJoinFamilyOpen(false)}>
        <form className="space-y-4" onSubmit={handleJoinFamily}>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Код приглашения</label>
            <input
              className="input-field"
              value={joinCode}
              onChange={(event) => setJoinCode(event.target.value)}
              required
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setIsJoinFamilyOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" variant="primary">
              Присоединиться
            </Button>
          </div>
        </form>
      </Modal>

      <Modal title="Новый семейный бюджет" open={isBudgetModalOpen} onClose={() => setIsBudgetModalOpen(false)}>
        <form className="space-y-4" onSubmit={handleCreateBudget}>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Название</label>
            <input
              className="input-field"
              value={budgetForm.name}
              onChange={(event) => setBudgetForm((prev) => ({ ...prev, name: event.target.value }))}
              required
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Сумма</label>
              <input
                className="input-field"
                type="number"
                min="0"
                value={budgetForm.amount}
                onChange={(event) => setBudgetForm((prev) => ({ ...prev, amount: event.target.value }))}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Период</label>
              <select
                className="input-field"
                value={budgetForm.period}
                onChange={(event) => setBudgetForm((prev) => ({ ...prev, period: event.target.value as 'weekly' | 'monthly' }))}
              >
                <option value="monthly">Месяц</option>
                <option value="weekly">Неделя</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setIsBudgetModalOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" variant="primary">
              Сохранить
            </Button>
          </div>
        </form>
      </Modal>

      <Modal title="Новая семейная цель" open={isGoalModalOpen} onClose={() => setIsGoalModalOpen(false)}>
        <form className="space-y-4" onSubmit={handleCreateGoal}>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Название</label>
            <input
              className="input-field"
              value={goalForm.name}
              onChange={(event) => setGoalForm((prev) => ({ ...prev, name: event.target.value }))}
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Описание</label>
            <textarea
              className="input-field min-h-[100px]"
              value={goalForm.description}
              onChange={(event) => setGoalForm((prev) => ({ ...prev, description: event.target.value }))}
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Целевая сумма</label>
              <input
                className="input-field"
                type="number"
                min="0"
                value={goalForm.target_amount}
                onChange={(event) => setGoalForm((prev) => ({ ...prev, target_amount: event.target.value }))}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Дедлайн</label>
              <input
                className="input-field"
                type="date"
                value={goalForm.deadline}
                onChange={(event) => setGoalForm((prev) => ({ ...prev, deadline: event.target.value }))}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setIsGoalModalOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" variant="primary">
              Сохранить
            </Button>
          </div>
        </form>
      </Modal>

      <Modal title="Установить лимит участнику" open={isLimitModalOpen} onClose={() => setIsLimitModalOpen(false)}>
        <form className="space-y-4" onSubmit={handleCreateLimit}>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Участник</label>
            <select
              className="input-field"
              value={limitForm.member_id}
              onChange={(event) => setLimitForm((prev) => ({ ...prev, member_id: event.target.value }))}
              required
            >
              <option value="">-- Выберите --</option>
              {members.map((member) => (
                <option key={member.id} value={member.id}>
                  Пользователь #{member.user_id} ({member.role})
                </option>
              ))}
            </select>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Лимит</label>
              <input
                className="input-field"
                type="number"
                min="0"
                value={limitForm.amount}
                onChange={(event) => setLimitForm((prev) => ({ ...prev, amount: event.target.value }))}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Период</label>
              <select
                className="input-field"
                value={limitForm.period}
                onChange={(event) => setLimitForm((prev) => ({ ...prev, period: event.target.value as 'weekly' | 'monthly' }))}
              >
                <option value="monthly">Месяц</option>
                <option value="weekly">Неделя</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setIsLimitModalOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" variant="primary">
              Сохранить
            </Button>
          </div>
        </form>
      </Modal>

      <Modal title="Создать перевод" open={isTransferModalOpen} onClose={() => setIsTransferModalOpen(false)}>
        <form className="space-y-4" onSubmit={handleCreateTransfer}>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Получатель</label>
            <select
              className="input-field"
              value={transferForm.to_member_id}
              onChange={(event) => setTransferForm((prev) => ({ ...prev, to_member_id: event.target.value }))}
              required
            >
              <option value="">-- Выберите --</option>
              {members.map((member) => (
                <option key={member.id} value={member.id}>
                  Пользователь #{member.user_id} ({member.role})
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Сумма</label>
            <input
              className="input-field"
              type="number"
              min="0"
              value={transferForm.amount}
              onChange={(event) => setTransferForm((prev) => ({ ...prev, amount: event.target.value }))}
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Комментарий</label>
            <textarea
              className="input-field min-h-[100px]"
              value={transferForm.description}
              onChange={(event) => setTransferForm((prev) => ({ ...prev, description: event.target.value }))}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setIsTransferModalOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" variant="primary">
              Создать
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default FamilyHubPage;


