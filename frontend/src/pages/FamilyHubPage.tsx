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
} from '../types/family';
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
  to_member_id?: string; // Опционально - если переводим участнику
  to_account_id?: string; // Опционально - если переводим на конкретный счет
  from_account_id?: string;
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
  to_member_id: undefined,
  to_account_id: undefined,
  from_account_id: undefined,
  amount: '',
  description: '',
};

const defaultLimitForm: LimitFormState = {
  member_id: '',
  amount: '',
  period: 'monthly',
};

const FamilyHubPage = () => {
  const [families, setFamilies] = useState<Family[]>([]);
  const [selectedFamilyId, setSelectedFamilyId] = useState<number | null>(null);
  const [familyDetail, setFamilyDetail] = useState<FamilyDetail | null>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [budgets, setBudgets] = useState<FamilyBudget[]>([]);
  const [limits, setLimits] = useState<FamilyMemberLimit[]>([]);
  const [goals, setGoals] = useState<FamilyGoal[]>([]);
  const [transfers, setTransfers] = useState<FamilyTransfer[]>([]);
  const [notifications, setNotifications] = useState<FamilyNotification[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [familyAccounts, setFamilyAccounts] = useState<any[]>([]);
  const [familyTransactions, setFamilyTransactions] = useState<any[]>([]);
  const [selectedFamilyAccountId, setSelectedFamilyAccountId] = useState<number | 'all'>('all');
  const [familyTransactionSearch, setFamilyTransactionSearch] = useState('');
  const [familyTransactionType, setFamilyTransactionType] = useState<'all' | 'income' | 'expense'>('all');
  const [familyTransactionPeriod, setFamilyTransactionPeriod] = useState<'30' | '90' | '365' | 'all'>('90');
  const [categories, setCategories] = useState<{id: number, name: string}[]>([]);

  const [isCreateFamilyOpen, setIsCreateFamilyOpen] = useState(false);
  const [isJoinFamilyOpen, setIsJoinFamilyOpen] = useState(false);
  const [isBudgetModalOpen, setIsBudgetModalOpen] = useState(false);
  const [isGoalModalOpen, setIsGoalModalOpen] = useState(false);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [isLimitModalOpen, setIsLimitModalOpen] = useState(false);
  const [isAddAccountModalOpen, setIsAddAccountModalOpen] = useState(false);
  const [isContributionModalOpen, setIsContributionModalOpen] = useState(false);
  const [selectedGoalForContribution, setSelectedGoalForContribution] = useState<FamilyGoal | null>(null);
  const [contributionAmount, setContributionAmount] = useState('');
  const [contributionAccountId, setContributionAccountId] = useState<number | null>(null);

  const [createFamilyName, setCreateFamilyName] = useState('');
  const [createFamilyDescription, setCreateFamilyDescription] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [selectedAccountsForSharing, setSelectedAccountsForSharing] = useState<number[]>([]);
  const [budgetForm, setBudgetForm] = useState<BudgetFormState>(defaultBudgetForm);
  const [goalForm, setGoalForm] = useState<GoalFormState>(defaultGoalForm);
  const [transferForm, setTransferForm] = useState<TransferFormState>(defaultTransferForm);
  const [limitForm, setLimitForm] = useState<LimitFormState>(defaultLimitForm);
  const [activeTab, setActiveTab] = useState<'overview' | 'budgets' | 'goals' | 'analytics' | 'transfers'>('overview');

  const selectedFamily = useMemo(() => families.find((f) => f.id === selectedFamilyId) ?? null, [families, selectedFamilyId]);

  const filteredFamilyTransactions = useMemo(() => {
    const search = familyTransactionSearch.trim().toLowerCase();
    const now = new Date();
    const periodDays = familyTransactionPeriod === 'all' ? null : Number(familyTransactionPeriod);
    const minDate = periodDays ? new Date(now.getTime() - periodDays * 24 * 60 * 60 * 1000) : null;

    return familyTransactions.filter((tx: any) => {
      const txType = (tx.transaction_type || '').toString().toLowerCase();
      const accountMatches = selectedFamilyAccountId === 'all' || Number(tx.account_id) === selectedFamilyAccountId;
      if (!accountMatches) {
        return false;
      }

      if (familyTransactionType === 'income' && txType !== 'income') {
        return false;
      }

      if (familyTransactionType === 'expense' && txType !== 'expense') {
        return false;
      }

      if (minDate) {
        const txDate = new Date(tx.transaction_date);
        if (Number.isNaN(txDate.getTime()) || txDate < minDate) {
          return false;
        }
      }

      if (search) {
        const haystack = [
          tx.description,
          tx.merchant,
          tx.category_name,
          tx.account_name,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();

        if (!haystack.includes(search)) {
          return false;
        }
      }

      return true;
    });
  }, [
    familyTransactions,
    selectedFamilyAccountId,
    familyTransactionSearch,
    familyTransactionType,
    familyTransactionPeriod,
  ]);

  const familyTransactionsSummary = useMemo(() => {
    if (filteredFamilyTransactions.length === 0) {
      return {
        income: 0,
        expense: 0,
        balance: 0,
      };
    }

    const totals = filteredFamilyTransactions.reduce(
      (acc: { income: number; expense: number }, tx: any) => {
        const amount = Number(tx.signed_amount ?? tx.amount ?? 0);
        const type = (tx.transaction_type || '').toString().toLowerCase();

        if (type === 'expense') {
          acc.expense += Math.abs(amount);
        } else if (type === 'income') {
          acc.income += Math.abs(amount);
        } else {
          if (amount >= 0) {
            acc.income += amount;
          } else {
            acc.expense += Math.abs(amount);
          }
        }

        return acc;
      },
      { income: 0, expense: 0 }
    );

    return {
      income: totals.income,
      expense: totals.expense,
      balance: totals.income - totals.expense,
    };
  }, [filteredFamilyTransactions]);

  // Загрузка транзакций семейных счетов
  useEffect(() => {
    const loadFamilyTransactions = async () => {
      if (activeTab !== 'analytics') {
        return;
      }

      if (familyAccounts.length === 0) {
        setFamilyTransactions([]);
        return;
      }

      try {
        const allTransactions: any[] = [];

        for (const account of familyAccounts) {
          try {
            const txResponse = await api.get(`/accounts/${account.id}/transactions?limit=100`);
            const transactions = Array.isArray(txResponse.data) ? txResponse.data : [];

            transactions.forEach((tx: any) => {
            const rawAmount = Number(tx.amount ?? tx.amount_value ?? 0);
            const type = (tx.transaction_type || '').toString().toLowerCase();
            let signedAmount = rawAmount;

            if (type === 'expense' && rawAmount > 0) {
              signedAmount = -rawAmount;
            }

            if (type === 'income' && rawAmount < 0) {
              signedAmount = Math.abs(rawAmount);
            }

              allTransactions.push({
                ...tx,
                amount: signedAmount,
                signed_amount: signedAmount,
                raw_amount: rawAmount,
                account_id: tx.account_id ?? account.id,
                account_name: account?.account_name || account?.account_number || `Счет #${account.id}`,
                account_bank_name: account?.bank_name,
                bank_provider: account?.bank_provider,
              });
            });
          } catch (err) {
            console.warn(`Failed to load transactions for account ${account.id}:`, err);
          }
        }

        allTransactions.sort(
          (a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime()
        );
        setFamilyTransactions(allTransactions.slice(0, 300)); // Показываем до 300 операций
      } catch (error) {
        console.error('Failed to load family transactions:', error);
      }
    };

    loadFamilyTransactions();
  }, [activeTab, familyAccounts]);

  useEffect(() => {
    if (selectedFamilyAccountId === 'all') {
      return;
    }

    const accountStillShared = familyAccounts.some((account) => account.id === selectedFamilyAccountId);
    if (!accountStillShared) {
      setSelectedFamilyAccountId('all');
    }
  }, [familyAccounts, selectedFamilyAccountId]);

  const loadFamilies = useCallback(async () => {
    try {
      const data = await api.listFamilies();
      setFamilies(data);
      if (data.length > 0) {
        setSelectedFamilyId((prev) => prev ?? data[0].id);
      }
      
      // Load user accounts for sharing
      try {
        const accountsData = await api.getAccounts();
        setAccounts(accountsData);
      } catch (err) {
        console.error('Failed to load accounts:', err);
      }
      
      // Load categories for budget creation
      try {
        const expensesData = await api.getExpensesByCategory(30);
        setCategories(expensesData.map((c: any) => ({ id: c.category_id, name: c.category })));
      } catch (err) {
        console.error('Failed to load categories:', err);
      }
    } catch (error) {
      toast.error('Не удалось загрузить семьи');
    }
  }, []);

  const loadFamilyData = useCallback(async (familyId: number) => {
    console.log('🔄🔄🔄 loadFamilyData START - VERSION 2.0 🔄🔄🔄');
    console.log('🆔 familyId:', familyId);
    setLoading(true);
    try {
      // Загружаем данные последовательно, чтобы избежать падения Promise.all
      const detail = await api.getFamily(familyId);
      setFamilyDetail(detail);
      console.log('📄 Family detail loaded:', detail);
      
      const membersData = await api.getFamilyMembers(familyId);
      setMembers(membersData.data || membersData || []);
      console.log('👥 Members loaded:', membersData.data || membersData);
      
      console.log('📡 Calling getFamilySharedAccounts...');
      const sharedAccountsData = await api.getFamilySharedAccounts(familyId);
      console.log('📡 RAW sharedAccountsData:', sharedAccountsData);
      console.log('📡 sharedAccountsData type:', typeof sharedAccountsData);
      console.log('📡 sharedAccountsData length:', sharedAccountsData?.length);
      setFamilyAccounts(sharedAccountsData || []);
      console.log('💳 familyAccounts SET TO:', sharedAccountsData || []);
      
      // Остальные данные загружаем параллельно
      const [budgetsData, limitsData, goalsData, transfersData, notificationsData] = await Promise.all([
        api.listFamilyBudgets(familyId).catch(() => []),
        api.listFamilyMemberLimits(familyId).catch(() => []),
        api.listFamilyGoals(familyId).catch(() => []),
        api.listFamilyTransfers(familyId).catch(() => []),
        api.listFamilyNotifications(familyId).catch(() => []),
      ]);

      const normalizedBudgets = (Array.isArray(budgetsData) ? budgetsData : [])
        .map((budget: any) => {
          const amount = Number(budget.amount ?? 0);
          const spent = Number(budget.current_spending ?? budget.spent ?? 0);
          const usage = typeof budget.usage_percentage === 'number'
            ? budget.usage_percentage
            : amount > 0
              ? Number(((spent / amount) * 100).toFixed(2))
              : 0;

          return {
            ...budget,
            amount,
            current_spending: spent,
            spent,
            usage_percentage: usage,
          };
        });

      setBudgets(normalizedBudgets);
      setLimits(limitsData);
      setGoals(goalsData);
      setTransfers(transfersData);
      setNotifications(notificationsData);
      
      console.log('✅ loadFamilyData completed successfully');
    } catch (error) {
      console.error('❌ Error in loadFamilyData:', error);
      toast.error('Ошибка при загрузке данных семьи');
    } finally {
      setLoading(false);
      console.log('🔄 loadFamilyData END');
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
    console.log('🚀🚀🚀 handleCreateFamily START - NEW VERSION 🚀🚀🚀');
    console.log('📊 Selected accounts for sharing:', selectedAccountsForSharing);
    console.log('📊 Selected accounts length:', selectedAccountsForSharing.length);
    
    try {
      const familyResponse = await api.createFamily({ name: createFamilyName, description: createFamilyDescription });
      console.log('✅ Family created - RAW response:', familyResponse);
      
      // Извлекаем ID семьи из ответа
      const familyId = familyResponse.id || familyResponse.data?.id || familyResponse?.id;
      console.log('🆔 Extracted family ID:', familyId);
      
      if (!familyId) {
        console.error('❌ No family ID in response!', familyResponse);
        toast.error('Семья создана, но не удалось получить её ID');
        return;
      }
      
      toast.success('Семья создана');
      
      // 🏦 АВТОМАТИЧЕСКИ создаем MyBank счет для семьи
      try {
        console.log('🏦 Creating MyBank wallet for family...');
        await api.post(`/family/groups/${familyId}/wallet`, {
          account_name: `Семейный кошелек ${createFamilyName}`,
          initial_balance: 0
        });
        console.log('✅ MyBank wallet created successfully');
        toast.success('Создан семейный кошелек в MyBank!');
      } catch (walletErr: any) {
        console.error('⚠️ Failed to create MyBank wallet (non-critical):', walletErr);
        // Не блокируем создание семьи если не удалось создать кошелек
        if (walletErr?.response?.data?.detail) {
          toast(`Семья создана, но кошелек не создан: ${walletErr.response.data.detail}`);
        }
      }
      
      // Добавляем выбранные счета в семейную группу
      console.log('🔍 Checking selectedAccountsForSharing.length:', selectedAccountsForSharing.length);
      if (selectedAccountsForSharing.length > 0) {
        console.log('✅ Entering shared accounts block');
        try {
          // Get the created member (creator is auto-added as admin)
          console.log('📡 Fetching family members for familyId:', familyId);
          const membersData = await api.getFamilyMembers(familyId);
          console.log('📡 Members data:', membersData);
          const members = membersData.data || membersData || [];
          console.log('👥 Members array:', members);
          
          const currentUser = await api.getCurrentUser();
          console.log('👤 Current user:', currentUser);
          
          const myMember = members.find((m: any) => m.user_id === currentUser.id);
          console.log('👤 My member:', myMember);
          
          if (myMember && myMember.id) {
            console.log(`➡️ Calling setSharedAccounts(${familyId}, ${myMember.id}, [${selectedAccountsForSharing.join(', ')}])`);
            await api.setSharedAccounts(familyId, myMember.id, selectedAccountsForSharing);
            console.log('✅ setSharedAccounts completed');
            toast.success(`Добавлено счетов: ${selectedAccountsForSharing.length}`);
          } else {
            console.error('❌ myMember not found or has no ID!', myMember);
            toast.error('Не удалось найти вашу запись в семье');
          }
        } catch (err) {
          console.error('❌ Failed to add shared accounts:', err);
          toast.error('Семья создана, но не удалось добавить счета');
        }
      } else {
        console.log('⚠️ selectedAccountsForSharing is empty, skipping');
      }
      
      const family = { id: familyId };
      
      console.log('🧹 Cleaning up state');
      setIsCreateFamilyOpen(false);
      setCreateFamilyName('');
      setCreateFamilyDescription('');
      setSelectedAccountsForSharing([]);
      
      console.log('🔄 Loading families');
      await loadFamilies();
      
      console.log('🎯 Setting selected family:', family.id);
      setSelectedFamilyId(family.id);
      
      console.log('✅ handleCreateFamily END');
    } catch (error) {
      console.error('❌ Error creating family:', error);
      toast.error('Не удалось создать семью');
    }
  };

  const handleJoinFamily = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const response = await api.joinFamily(joinCode.trim());
      console.log('✅ Joined family, response:', response);
      
      // Извлекаем member из response (может быть в data или напрямую)
      const member = (response as any).data || response;
      
      // Проверяем что получили корректные данные
      if (!member || !member.family_id || !member.id) {
        console.error('❌ Invalid member data:', member);
        toast.error('Ошибка: некорректные данные от сервера');
        return;
      }
      
      // Если выбраны счета для шаринга, сохраняем их
      if (selectedAccountsForSharing.length > 0) {
        await api.setSharedAccounts(member.family_id, member.id, selectedAccountsForSharing);
      }
      
      toast.success('Вы присоединились к семье');
      setIsJoinFamilyOpen(false);
      setJoinCode('');
      setSelectedAccountsForSharing([]);
      await loadFamilies();
      setSelectedFamilyId(member.family_id);
    } catch (error: any) {
      console.error('❌ Join family error:', error);
      toast.error(error.response?.data?.detail || 'Не удалось присоединиться по коду приглашения');
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
      const now = new Date();
      await api.createFamilyBudget(selectedFamilyId, {
        name: budgetForm.name,
        amount: Number(budgetForm.amount),
        period: budgetForm.period,
        start_date: now.toISOString(),
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
    
    // Валидация суммы
    const targetAmount = Number(goalForm.target_amount);
    if (targetAmount > 9999999999) {
      toast.error('Максимальная сумма цели: 9 999 999 999 ₽');
      return;
    }
    if (targetAmount <= 0) {
      toast.error('Сумма цели должна быть больше 0');
      return;
    }
    
    try {
      await api.createFamilyGoal(selectedFamilyId, {
        name: goalForm.name,
        description: goalForm.description,
        target_amount: targetAmount,
        deadline: goalForm.deadline ? `${goalForm.deadline}T00:00:00` : undefined,
      });
      toast.success('Цель создана');
      setIsGoalModalOpen(false);
      setGoalForm(defaultGoalForm);
      loadFamilyData(selectedFamilyId);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Не удалось создать цель');
      console.error('Create goal error:', error);
    }
  };

  const handleCreateLimit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFamilyId) return;
    try {
      await api.createMemberLimit(selectedFamilyId, {
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
    
    // Валидация - должен быть указан либо to_member_id, либо to_account_id
    if (!transferForm.to_member_id && !transferForm.to_account_id) {
      toast.error('Укажите получателя или счет назначения');
      return;
    }
    
    try {
      await api.createFamilyTransfer(selectedFamilyId, {
        to_member_id: transferForm.to_member_id ? Number(transferForm.to_member_id) : undefined,
        to_account_id: transferForm.to_account_id ? Number(transferForm.to_account_id) : undefined,
        from_account_id: transferForm.from_account_id ? Number(transferForm.from_account_id) : undefined,
        amount: Number(transferForm.amount),
        description: transferForm.description,
      });
      toast.success('Перевод создан');
      setIsTransferModalOpen(false);
      setTransferForm(defaultTransferForm);
      loadFamilyData(selectedFamilyId);
    } catch (error: any) {
      console.error('Transfer creation error:', error);
      toast.error(error.response?.data?.detail || 'Не удалось создать перевод');
    }
    };

  const handleContributeToGoal = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFamilyId || !selectedGoalForContribution) return;
    
    const amount = Number(contributionAmount);
    if (amount <= 0) {
      toast.error('Сумма должна быть больше 0');
      return;
    }
    
    if (!contributionAccountId) {
      toast.error('Выберите счет для взноса');
      return;
    }
    
    try {
      await api.post(`/family/groups/${selectedFamilyId}/goals/${selectedGoalForContribution.id}/contributions`, {
        amount,
        source_account_id: contributionAccountId
      });
      toast.success('Взнос внесен успешно! Проверьте вкладку "📈 Статистика"');
      setIsContributionModalOpen(false);
      setContributionAmount('');
      setContributionAccountId(null);
      setSelectedGoalForContribution(null);
      
      // Перезагружаем данные семьи
      await loadFamilyData(selectedFamilyId);
      
      // Принудительно перезагружаем транзакции (они обновятся при переключении на вкладку Статистика)
      // Пользователь увидит обновленные транзакции когда откроет вкладку
    } catch (error: any) {
      console.error('Contribution error:', error);
      toast.error(error.response?.data?.detail || 'Не удалось внести взнос');
    }
  };
  
  // members уже определен в state, используем его
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
            <div className="flex-1">
              <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Активная семья</p>
              <h2 className="mt-1 text-2xl font-semibold text-ink">{selectedFamily?.name}</h2>
              <div className="mt-3 flex items-center gap-3">
                <div className="flex items-center gap-2 rounded-xl border border-white/50 bg-white/70 px-4 py-2">
                  <span className="text-xs text-ink/60">Код:</span>
                  <code className="font-mono text-sm font-semibold text-primary-700">
                    {familyDetail?.invite_code || 'Загрузка...'}
                  </code>
                  <button
                    type="button"
                    className="ml-2 text-primary-600 hover:text-primary-700"
                    onClick={() => {
                      if (familyDetail?.invite_code) {
                      navigator.clipboard.writeText(familyDetail.invite_code);
                        toast.success('Код скопирован');
                      }
                    }}
                  >
                    📋
                  </button>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm"
                  className="border border-white/60 bg-white/70" 
                  onClick={handleRotateInvite}
                >
                  🔄 Обновить
                </Button>
            </div>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-ink/45 mb-2">Переключить</p>
              <select
                value={selectedFamilyId ?? ''}
                onChange={(event) => setSelectedFamilyId(Number(event.target.value))}
                className="input-field"
              >
                {families.map((family) => (
                  <option key={family.id} value={family.id}>
                    {family.name}
                  </option>
                ))}
              </select>
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
          {/* Tabs Navigation */}
          <Card className="p-2">
            <div className="flex gap-2 overflow-x-auto">
              {[
                { id: 'overview', label: '📊 Обзор', icon: '📊' },
                { id: 'budgets', label: '💰 Бюджеты', icon: '💰' },
                { id: 'goals', label: '🎯 Цели', icon: '🎯' },
                { id: 'analytics', label: '📈 Статистика', icon: '📈' },
                { id: 'transfers', label: '💸 Переводы', icon: '💸' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex-1 min-w-[120px] px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white shadow-lg'
                      : 'bg-white/60 text-ink/70 hover:bg-white/80'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </Card>

          {loading ? (
            <Card className="p-12 text-center text-ink/60">Загрузка данных семьи...</Card>
          ) : (
            <>
              {/* Overview Tab */}
              {activeTab === 'overview' && (
            <>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <Card className="bg-gradient-to-br from-primary-50 via-white/80 to-white/60">
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Общий баланс семейных счетов</p>
                  <p className="mt-2 text-3xl font-semibold text-ink">
                    {familyAccounts.length > 0
                      ? formatCurrency(familyAccounts.reduce((sum, acc) => sum + (Number(acc.balance) || 0), 0))
                      : '0 ₽'}
                  </p>
                </Card>
                <Card>
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Счетов / Участников</p>
                  <div className="mt-2 text-sm text-ink/70">
                    <p>Семейных счетов: <span className="font-semibold text-primary-600">{familyAccounts.length}</span></p>
                    <p>Участников: <span className="font-semibold text-primary-600">{members.length}</span></p>
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

              {/* Family Accounts Card */}
              <Card className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-ink">💳 Семейные счета</h3>
                    <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Общие счета группы</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="border border-primary-200 bg-primary-50"
                      onClick={async () => {
                        if (!selectedFamilyId) return;
                        try {
                          const currentUser = await api.getCurrentUser();
                          const myMember = members.find(m => m.user_id === currentUser.id);
                          
                          if (!myMember || myMember.role !== 'admin') {
                            toast.error('Только администратор может создать семейный кошелек');
                            return;
                          }
                          
                          await api.post(`/family/groups/${selectedFamilyId}/wallet`, {
                            account_name: `Семейный кошелек ${familyDetail?.name || 'Семьи'}`,
                            initial_balance: 0
                          });
                          toast.success('Семейный кошелек создан в MyBank!');
                          loadFamilyData(selectedFamilyId);
                        } catch (error: any) {
                          console.error('Failed to create family wallet:', error);
                          toast.error(error.response?.data?.detail || 'Не удалось создать семейный кошелек');
                        }
                      }}
                    >
                      🏦 Создать семейный кошелек MyBank
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="border border-white/60 bg-white/70"
                      onClick={() => {
                        if (!selectedFamilyId) return;
                        setSelectedAccountsForSharing([]);
                        setIsAddAccountModalOpen(true);
                      }}
                    >
                      + Добавить счет
                    </Button>
                  </div>
                </div>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {familyAccounts.length > 0 ? familyAccounts.map((account) => (
                    <div key={account.id} className="rounded-xl border border-white/60 bg-gradient-to-br from-white/90 to-white/70 p-4">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs uppercase tracking-[0.28em] text-ink/40">{account.account_type || 'Счет'}</p>
                        <div className="flex items-center gap-2">
                          <span className="text-xs px-2 py-1 rounded-full bg-primary-100 text-primary-700">
                            {account.bank_name || 'Банк'}
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:bg-red-50"
                            onClick={async () => {
                              if (!selectedFamilyId) return;
                              try {
                                const currentUser = await api.getCurrentUser();
                                const member = members.find(m => m.user_id === currentUser.id);
                                if (!member) {
                                  toast.error('Вы не являетесь участником этой семьи');
                                  return;
                                }
                                await api.removeSharedAccount(selectedFamilyId, member.id, account.id);
                                toast.success('Счет удален из семейной группы');
                                loadFamilyData(selectedFamilyId);
                              } catch (error: any) {
                                console.error('Failed to remove account:', error);
                                toast.error('Не удалось удалить счет');
                              }
                            }}
                          >
                            🗑️
                          </Button>
                        </div>
                      </div>
                      <p className="text-2xl font-semibold text-ink">{Number(account.balance || 0).toLocaleString('ru-RU')} ₽</p>
                      <p className="mt-1 text-xs text-ink/50">{account.account_name || account.account_number || 'Счет'}</p>
                      <div className="mt-2 flex items-center gap-1">
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                          {account.visibility === 'FAMILY' ? '👁️ Виден всем' : '🔒 Приватный'}
                        </span>
                      </div>
                    </div>
                  )) : (
                    <div className="col-span-3 text-center py-8">
                      <p className="text-lg text-ink/60 mb-2">Нет добавленных счетов</p>
                      <p className="text-sm text-ink/50">Добавьте счета при создании семьи или нажмите "+ Добавить счет"</p>
                    </div>
                  )}
                </div>
              </Card>

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
                    {members.length > 0 ? members.map((member) => (
                      <div key={member.id} className="rounded-2xl border border-white/60 bg-white/70 p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-ink">
                              {member.user_name || member.user_email || `Пользователь #${member.user_id}`}
                            </p>
                            <p className="text-xs text-ink/50">
                              Роль: {member.role === 'admin' ? '👑 Администратор' : '👤 Участник'} · 
                              Статус: {member.status === 'active' ? '✅ Активен' : '⏳ Ожидает'}
                            </p>
                          </div>
                          {member.status === 'pending' ? (
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                variant="primary"
                                onClick={async () => {
                                  try {
                                    await api.approveMember(selectedFamily!.id, member.id);
                                    toast.success('Участник одобрен!');
                                    if (selectedFamilyId) await loadFamilyData(selectedFamilyId);
                                  } catch (error) {
                                    toast.error('Не удалось одобрить участника');
                                  }
                                }}
                              >
                                ✅ Одобрить
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="border border-red-300 bg-red-50 text-red-700 hover:bg-red-100"
                                onClick={async () => {
                                  if (!confirm('Вы уверены, что хотите отказать этому участнику?')) return;
                                  try {
                                    await api.rejectFamilyMember(selectedFamily!.id, member.id);
                                    toast.success('Участник отклонен');
                                    if (selectedFamilyId) await loadFamilyData(selectedFamilyId);
                                  } catch (error) {
                                    toast.error('Не удалось отклонить участника');
                                  }
                                }}
                              >
                                ❌ Отказать
                              </Button>
                            </div>
                          ) : (
                            <div className="text-right text-xs text-ink/50">
                              {member.joined_at ? `В группе с ${new Date(member.joined_at).toLocaleDateString('ru-RU')}` : ''}
                            </div>
                          )}
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
                    )) : (
                      <p className="text-sm text-ink/50">Загрузка участников...</p>
                    )}
                  </div>
                </Card>

                <Card>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold text-ink">📊 Бюджеты</h3>
                      <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Контроль расходов по категориям</p>
                    </div>
                    <Button variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setActiveTab('budgets')}>
                      Перейти →
                    </Button>
                  </div>
                  <div className="mt-4 space-y-3">
                    {budgets.map((budget) => (
                      <div key={budget.id} className="flex items-center justify-between rounded-2xl border border-white/60 bg-white/70 p-4">
                        <div>
                          <p className="text-sm font-semibold text-ink">{budget.name}</p>
                          <p className="text-xs text-ink/50">Период: {budget.period === 'monthly' ? 'Месяц' : 'Неделя'}</p>
                          {budget.category_name && (
                            <p className="text-xs text-ink/50 mt-1">Категория: {budget.category_name}</p>
                          )}
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold text-ink">{formatCurrency(budget.amount ?? 0)} </p>
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
                    <Button variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setActiveTab('goals')}>
                      Перейти →
                    </Button>
                  </div>
                  <div className="mt-4 space-y-3">
                    {goals.map((goal) => {
                      const progress = goal.target_amount > 0 ? Math.min(100, Math.round((goal.current_amount / goal.target_amount) * 100)) : 0;
                      const goalAccount = familyAccounts.find((account: any) => account.account_name === `Family Goal: ${goal.name}`);
                      return (
                        <div key={goal.id} className="rounded-2xl border border-white/60 bg-white/70 p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm font-semibold text-ink">{goal.name}</p>
                              <p className="text-xs text-ink/50">Цель: {formatCurrency(goal.target_amount)} · Собрано: {formatCurrency(goal.current_amount)}</p>
                              {goalAccount && (
                                <p className="text-xs text-ink/50 mt-1">
                                  Счет: {goalAccount.account_name} · {goalAccount.bank_name || 'MyBank'} · {formatCurrency(Number(goalAccount.balance ?? 0))}
                                </p>
                              )}
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
                    <Button variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setActiveTab('transfers')}>
                      Перейти →
                    </Button>
                  </div>
                  <div className="mt-4 space-y-3">
                    {transfers.slice(0, 3).map((transfer) => (
                      <div key={transfer.id} className="rounded-2xl border border-white/60 bg-white/70 p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-semibold text-ink">
                              {formatCurrency(transfer.amount)} · {
                                transfer.status === 'approved' ? '✅ Одобрен' :
                                transfer.status === 'pending' ? '⏳ Ожидает' :
                                transfer.status === 'executed' ? '✅ Выполнен' :
                                '❌ Отклонен'
                              }
                            </p>
                            <p className="text-xs text-ink/50">
                              От участника #{transfer.from_member_id} → {
                                transfer.to_member_id 
                                  ? `#${transfer.to_member_id}` 
                                  : transfer.to_account_id 
                                    ? `Счет #${transfer.to_account_id}` 
                                    : 'Не указан'
                              }
                            </p>
                          </div>
                          <p className="text-xs text-ink/50">
                            {new Date(transfer.created_at).toLocaleDateString('ru-RU', {
                              day: '2-digit',
                              month: '2-digit',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </p>
                        </div>
                        {transfer.description && (
                          <p className="mt-2 text-xs text-ink/60">{transfer.description}</p>
                        )}
                      </div>
                    ))}
                    {transfers.length === 0 && <p className="text-sm text-ink/50">Здесь появятся запросы и переводы внутри семьи.</p>}
                    {transfers.length > 3 && (
                      <p className="text-xs text-center text-ink/50 pt-2">
                        И еще {transfers.length - 3} перевод(а/ов). Перейдите в таб "Переводы" →
                      </p>
                    )}
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
                  {notifications.map((notification) => {
                    const payload = notification.payload || {};
                    const getNotificationText = () => {
                      // Перевод - transfer notification
                      if (payload.transfer_id) {
                        const amount = formatCurrency(payload.amount || 0);
                        const fromMember = payload.from_member_id 
                          ? `Участник #${payload.from_member_id}` 
                          : 'Неизвестный';
                        const toMember = payload.to_member_id 
                          ? `Участнику #${payload.to_member_id}` 
                          : payload.to_account_id 
                            ? `На счет #${payload.to_account_id}`
                            : 'Неизвестно';
                        
                        const limitStatus = payload.limit_exceeded 
                          ? '⚠️ Превышен лимит!' 
                          : '';
                        
                        return `💸 Перевод ${amount} от ${fromMember} → ${toMember} ${limitStatus}`;
                      }
                      
                      // Бюджет - budget notification
                      if (payload.budget_id) {
                        const percentage = payload.percentage ? Number(payload.percentage).toFixed(1) : undefined;
                        if (notification.type === 'budget_exceeded') {
                          return `🚨 Бюджет «${payload.budget_name || payload.budget_id}» превышен на ${percentage || '100'}%`;
                        }
                        if (notification.type === 'budget_approach') {
                          return `⚠️ Бюджет «${payload.budget_name || payload.budget_id}» израсходован на ${percentage || '80'}%`;
                        }
                        return `💰 Бюджет ${payload.budget_name || '#' + payload.budget_id}: ${payload.message || 'обновление'}`;
                      }
                      
                      // Цель - goal notification
                      if (payload.goal_id) {
                        return `🎯 Цель #${payload.goal_id}: ${payload.message || 'обновление'}`;
                      }
                      
                      // Лимит - limit notification
                      if (payload.limit_exceeded) {
                        return `⚠️ Превышен лимит: ${payload.message || 'проверьте расходы'}`;
                      }
                      
                      // Общее сообщение
                      return payload.message || 'Новое уведомление';
                    };

                    return (
                    <div key={notification.id} className="rounded-2xl border border-white/60 bg-white/70 p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <p className="text-sm text-ink">{getNotificationText()}</p>
                            {payload.limit_exceeded && (
                              <span className="mt-2 inline-block rounded-lg bg-red-100 px-2 py-1 text-xs font-semibold text-red-700">
                                ⚠️ Лимит превышен
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-ink/50 whitespace-nowrap">
                            {new Date(notification.created_at).toLocaleString('ru-RU')}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                  {notifications.length === 0 && <p className="text-sm text-ink/50">Уведомления появятся, когда семья начнёт тратить и копить.</p>}
                </div>
              </Card>
                </>
              )}

              {/* Budgets Tab */}
              {activeTab === 'budgets' && (
                <Card>
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-2xl font-semibold text-ink">💰 Семейные бюджеты</h2>
                      <p className="text-sm text-ink/60 mt-1">Контроль расходов всей семьи по категориям</p>
                    </div>
                    <Button variant="primary" onClick={() => setIsBudgetModalOpen(true)}>
                      + Создать бюджет
                    </Button>
                  </div>
                  <div className="space-y-4">
                    {budgets.map((budget) => {
                      const amount = Number(budget.amount ?? 0);
                      const spent = Number(budget.spent ?? budget.current_spending ?? 0);
                      const progressRaw = typeof budget.usage_percentage === 'number'
                        ? budget.usage_percentage
                        : amount > 0
                          ? (spent / amount) * 100
                          : 0;
                      const progress = Math.min(progressRaw, 100);
                      return (
                        <div key={budget.id} className="rounded-2xl border border-white/60 bg-white/70 p-6">
                          <div className="flex items-start justify-between mb-4">
                            <div>
                              <h3 className="text-lg font-semibold text-ink">{budget.name}</h3>
                              <p className="text-xs text-ink/50">
                                Период: {budget.period === 'monthly' ? 'Месячный' : 'Недельный'}
                              </p>
                              {budget.category_name && (
                                <p className="text-xs text-ink/50 mt-1">Категория: {budget.category_name}</p>
                              )}
                            </div>
                            <div className="text-right">
                              <p className="text-2xl font-bold text-ink">{formatCurrency(spent)}</p>
                              <p className="text-xs text-ink/50">из {formatCurrency(amount)}</p>
                            </div>
                          </div>
                          <div className="w-full bg-white/90 rounded-full h-3 overflow-hidden">
                            <div
                              className={`h-full transition-all ${
                                progress > 90 ? 'bg-red-500' : progress > 70 ? 'bg-yellow-500' : 'bg-primary-500'
                              }`}
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                          <p className="text-xs text-ink/50 mt-2">{progress.toFixed(1)}% использовано</p>
                        </div>
                      );
                    })}
                    {budgets.length === 0 && (
                      <div className="text-center py-12">
                        <p className="text-lg text-ink/60 mb-2">Создайте первый семейный бюджет</p>
                        <p className="text-sm text-ink/50">Используйте кнопку выше для создания</p>
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {/* Goals Tab */}
              {activeTab === 'goals' && (
                <Card>
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-2xl font-semibold text-ink">🎯 Семейные цели</h2>
                      <p className="text-sm text-ink/60 mt-1">Копите вместе на общие мечты</p>
                    </div>
                    <Button variant="primary" onClick={() => setIsGoalModalOpen(true)}>
                      + Создать цель
                    </Button>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    {goals.map((goal) => {
                      const progress = goal.target_amount > 0 ? Math.min((goal.current_amount / goal.target_amount) * 100, 100) : 0;
                      const goalAccount = familyAccounts.find((account: any) => account.account_name === `Family Goal: ${goal.name}`);
                      return (
                        <div key={goal.id} className="rounded-2xl border border-white/60 bg-gradient-to-br from-white/90 to-white/70 p-6">
                          <h3 className="text-lg font-semibold text-ink mb-2">{goal.name}</h3>
                          {goal.description && (
                            <p className="text-sm text-ink/60 mb-4">{goal.description}</p>
                          )}
                          <div className="space-y-3">
                            <div>
                              <div className="flex justify-between text-sm mb-2">
                                <span className="text-ink/60">Прогресс</span>
                                <span className="font-semibold text-ink">{progress.toFixed(1)}%</span>
                              </div>
                              <div className="w-full bg-white/90 rounded-full h-3 overflow-hidden">
                                <div
                                  className="h-full bg-gradient-to-r from-primary-400 to-primary-600 transition-all"
                                  style={{ width: `${progress}%` }}
                                />
                              </div>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-ink/60">Накоплено</span>
                              <span className="font-semibold text-primary-700">{formatCurrency(goal.current_amount)}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-ink/60">Цель</span>
                              <span className="font-semibold text-ink">{formatCurrency(goal.target_amount)}</span>
                            </div>
                            {goalAccount && (
                              <div className="flex justify-between text-sm">
                                <span className="text-ink/60">Счет MyBank</span>
                                <span className="text-ink/80">
                                  {formatCurrency(Number(goalAccount.balance ?? 0))}
                                </span>
                              </div>
                            )}
                            {goal.deadline && (
                              <div className="flex justify-between text-sm">
                                <span className="text-ink/60">Дедлайн</span>
                                <span className="text-ink">{new Date(goal.deadline).toLocaleDateString('ru-RU')}</span>
                              </div>
                            )}
                            <div className="pt-3 border-t border-white/60">
                              <Button
                                variant="primary"
                                size="sm"
                                className="w-full"
                                onClick={() => {
                                  setSelectedGoalForContribution(goal);
                                  setIsContributionModalOpen(true);
                                }}
                              >
                                💰 Внести взнос
                              </Button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    {goals.length === 0 && (
                      <div className="col-span-2 text-center py-12">
                        <p className="text-lg text-ink/60 mb-2">Создайте первую семейную цель</p>
                        <p className="text-sm text-ink/50">Используйте кнопку выше для создания</p>
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {/* Analytics Tab - показываем транзакции семейных счетов */}
              {activeTab === 'analytics' && selectedFamily && (
                <div className="space-y-6">
                  {familyTransactions.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100">
                      <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-emerald-700 font-medium">💰 Доходы</p>
                            <p className="text-2xl font-bold text-emerald-900 mt-1">{formatCurrency(familyTransactionsSummary.income)}</p>
                          </div>
                          <div className="text-4xl">📈</div>
                        </div>
                      </Card>
                      <Card className="bg-gradient-to-br from-rose-50 to-rose-100">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-rose-700 font-medium">💸 Расходы</p>
                            <p className="text-2xl font-bold text-rose-900 mt-1">{formatCurrency(familyTransactionsSummary.expense)}</p>
                          </div>
                          <div className="text-4xl">📉</div>
                        </div>
                      </Card>
                      <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-blue-700 font-medium">💵 Баланс</p>
                            <p className={`text-2xl font-bold mt-1 ${familyTransactionsSummary.balance >= 0 ? 'text-blue-900' : 'text-rose-900'}`}>
                              {familyTransactionsSummary.balance > 0 ? '+' : familyTransactionsSummary.balance < 0 ? '-' : ''}
                              {formatCurrency(Math.abs(familyTransactionsSummary.balance))}
                            </p>
                          </div>
                          <div className="text-4xl">⚖️</div>
                        </div>
                      </Card>
                    </div>
                  )}

                  <Card>
                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                      <div>
                        <h2 className="text-2xl font-semibold text-ink">📊 Транзакции семейных счетов</h2>
                        <p className="text-sm text-ink/60">
                          Все операции по счетам, добавленным в семейную группу (последние 90 дней)
                        </p>
                        </div>
                      {familyAccounts.length > 0 && (
                        <div className="flex flex-col">
                          <label htmlFor="family-account-filter" className="text-xs font-semibold uppercase tracking-wider text-ink/50">
                            Фильтр по счету
                          </label>
                          <select
                            id="family-account-filter"
                            value={selectedFamilyAccountId === 'all' ? 'all' : String(selectedFamilyAccountId)}
                            onChange={(event) => {
                              const value = event.target.value;
                              setSelectedFamilyAccountId(value === 'all' ? 'all' : Number(value));
                            }}
                            className="mt-1 rounded-lg border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink shadow-sm focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-200"
                          >
                            <option value="all">Все счета</option>
                            {familyAccounts.map((account) => (
                              <option key={account.id} value={account.id}>
                                {account.account_name || account.account_number || `Счет #${account.id}`} · {account.bank_name || 'Банк'}
                              </option>
                            ))}
                          </select>
                      </div>
                      )}
                    </div>
                  </Card>

                  {familyAccounts.length === 0 ? (
                    <Card className="text-center py-12">
                      <p className="text-lg text-ink/60 mb-2">Нет семейных счетов</p>
                      <p className="text-sm text-ink/50">Добавьте счета в семейную группу для просмотра транзакций</p>
                    </Card>
                  ) : (
                    <Card>
                      <div className="px-4 pb-4 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                        <div className="flex flex-wrap gap-3">
                          <div className="flex flex-col">
                            <label htmlFor="family-transaction-search" className="text-xs font-semibold uppercase tracking-wider text-ink/50">
                              Поиск
                            </label>
                            <input
                              id="family-transaction-search"
                              type="search"
                              value={familyTransactionSearch}
                              onChange={(event) => setFamilyTransactionSearch(event.target.value)}
                              placeholder="Описание, категория, сумма..."
                              className="mt-1 w-56 rounded-lg border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink shadow-sm focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-200"
                            />
                          </div>
                          <div className="flex flex-col">
                            <label htmlFor="family-transaction-type" className="text-xs font-semibold uppercase tracking-wider text-ink/50">
                              Тип
                            </label>
                            <select
                              id="family-transaction-type"
                              value={familyTransactionType}
                              onChange={(event) => setFamilyTransactionType(event.target.value as 'all' | 'income' | 'expense')}
                              className="mt-1 rounded-lg border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink shadow-sm focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-200"
                            >
                              <option value="all">Все</option>
                              <option value="income">Доходы</option>
                              <option value="expense">Расходы</option>
                            </select>
                          </div>
                          <div className="flex flex-col">
                            <label htmlFor="family-transaction-period" className="text-xs font-semibold uppercase tracking-wider text-ink/50">
                              Период
                            </label>
                            <select
                              id="family-transaction-period"
                              value={familyTransactionPeriod}
                              onChange={(event) => setFamilyTransactionPeriod(event.target.value as '30' | '90' | '365' | 'all')}
                              className="mt-1 rounded-lg border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink shadow-sm focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-200"
                            >
                              <option value="30">30 дней</option>
                              <option value="90">90 дней</option>
                              <option value="365">365 дней</option>
                              <option value="all">Весь период</option>
                            </select>
                          </div>
                        </div>
                        <div className="text-sm text-ink/60 text-right leading-tight">
                          <div>Всего: {filteredFamilyTransactions.length} / {familyTransactions.length}</div>
                          <div>
                            Доходы: <span className="text-emerald-600">+{formatCurrency(familyTransactionsSummary.income)}</span>
                          </div>
                          <div>
                            Расходы: <span className="text-rose-600">-{formatCurrency(familyTransactionsSummary.expense)}</span>
                          </div>
                          <div>
                            Баланс: <span className={familyTransactionsSummary.balance >= 0 ? 'text-emerald-600' : 'text-rose-600'}>
                              {familyTransactionsSummary.balance > 0 ? '+' : familyTransactionsSummary.balance < 0 ? '-' : ''}
                              {formatCurrency(Math.abs(familyTransactionsSummary.balance))}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="overflow-x-auto">
                         <table className="w-full">
                           <thead>
                             <tr className="border-b border-white/60">
                               <th className="px-4 py-3 text-left text-xs font-semibold text-ink/60 uppercase tracking-wider">Дата</th>
                               <th className="px-4 py-3 text-left text-xs font-semibold text-ink/60 uppercase tracking-wider">Счет</th>
                               <th className="px-4 py-3 text-left text-xs font-semibold text-ink/60 uppercase tracking-wider">Описание</th>
                               <th className="px-4 py-3 text-right text-xs font-semibold text-ink/60 uppercase tracking-wider">Сумма</th>
                             </tr>
                           </thead>
                           <tbody>
                             {filteredFamilyTransactions.length === 0 ? (
                               <tr>
                                 <td colSpan={4} className="px-4 py-12 text-center text-sm text-ink/50">
                                   Нет транзакций для выбранного счета за последние 90 дней
                                 </td>
                               </tr>
                             ) : (
                             filteredFamilyTransactions.map((t: any, idx: number) => {
                               const amount = Number(t.signed_amount ?? t.amount);
                               const sign = amount > 0 ? '+' : '';
                               const isPositive = amount >= 0;
                               return (
                                 <tr key={`${t.transaction_id || t.external_transaction_id || idx}`} className="border-b border-white/40 hover:bg-white/40 transition-colors">
                                   <td className="px-4 py-3 text-sm text-ink">
                                     {new Date(t.transaction_date).toLocaleDateString('ru-RU', {
                                       day: '2-digit',
                                       month: '2-digit',
                                       year: 'numeric',
                                     })}
                                   </td>
                                   <td className="px-4 py-3 text-sm text-ink/70">
                                     {t.account_name || `Счет #${t.account_id}`}
                                     {t.account_bank_name ? <span className="ml-2 text-xs text-ink/40">· {t.account_bank_name}</span> : null}
                                   </td>
                                   <td className="px-4 py-3 text-sm text-ink">
                                     {t.description || t.merchant || 'Без описания'}
                                   </td>
                                   <td className={`px-4 py-3 text-sm font-semibold text-right ${isPositive ? 'text-emerald-600' : 'text-rose-600'}`}>
                                     {sign}{formatCurrency(Math.abs(amount))}
                                   </td>
                                 </tr>
                               );
                             })
                             )}
                           </tbody>
                         </table>
                       </div>
                    </Card>
                  )}
                </div>
              )}

              {/* Transfers Tab */}
              {activeTab === 'transfers' && (
                <Card>
                  <div className="flex items-center justify-between mb-6">
                        <div>
                      <h2 className="text-2xl font-semibold text-ink">💸 Переводы и транзакции</h2>
                      <p className="text-sm text-ink/60 mt-1">История операций по семейным счетам</p>
                    </div>
                    <Button variant="primary" onClick={() => setIsTransferModalOpen(true)}>
                      + Новый перевод
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {transfers.map((transfer) => (
                      <div key={transfer.id} className="rounded-2xl border border-white/60 bg-white/70 p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-lg font-semibold text-ink">{formatCurrency(transfer.amount)}</p>
                            <p className="text-xs text-ink/50">
                              От участника #{transfer.from_member_id} → {
                                transfer.to_member_id 
                                  ? `#${transfer.to_member_id}` 
                                  : transfer.to_account_id 
                                    ? `Счет #${transfer.to_account_id}` 
                                    : 'Не указан'
                              }
                            </p>
                            {transfer.description && (
                              <p className="text-sm text-ink/60 mt-1">{transfer.description}</p>
                          )}
                        </div>
                          <div className="text-right">
                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                              transfer.status === 'executed' ? 'bg-emerald-100 text-emerald-700' :
                              transfer.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                              transfer.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-rose-100 text-rose-700'
                            }`}>
                              {transfer.status === 'executed' ? '✅ Выполнен' :
                               transfer.status === 'approved' ? '✅ Одобрен' :
                               transfer.status === 'pending' ? '⏳ Ожидает' :
                               '❌ Отклонен'}
                            </span>
                            <p className="text-xs text-ink/50 mt-1">
                              {new Date(transfer.created_at).toLocaleDateString('ru-RU', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </p>
                      </div>
                        </div>
                        {/* Кнопки одобрения/отклонения для администратора */}
                        {transfer.status === 'pending' && (() => {
                          const myMember = members.find(m => m.user_id === (familyDetail as any)?.created_by);
                          const isAdmin = myMember && myMember.role === 'admin';
                          return isAdmin;
                        })() && (
                          <div className="flex gap-2 mt-3 pt-3 border-t border-white/60">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="flex-1 border border-emerald-600 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                              onClick={async () => {
                                if (!selectedFamilyId) return;
                                try {
                                  await api.post(`/family/groups/${selectedFamilyId}/transfers/${transfer.id}/approve`, { approved: true });
                                  toast.success('Перевод одобрен!');
                                  loadFamilyData(selectedFamilyId);
                                } catch (error: any) {
                                  console.error('Approve transfer error:', error);
                                  toast.error('Не удалось одобрить перевод');
                                }
                              }}
                            >
                              ✅ Одобрить
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="flex-1 border border-rose-600 bg-rose-50 text-rose-700 hover:bg-rose-100"
                              onClick={async () => {
                                if (!selectedFamilyId) return;
                                try {
                                  await api.post(`/family/groups/${selectedFamilyId}/transfers/${transfer.id}/approve`, { approved: false });
                                  toast.success('Перевод отклонен');
                                  loadFamilyData(selectedFamilyId);
                                } catch (error: any) {
                                  console.error('Reject transfer error:', error);
                                  toast.error('Не удалось отклонить перевод');
                                }
                              }}
                            >
                              ❌ Отклонить
                            </Button>
                          </div>
                        )}
                    </div>
                  ))}
                    {transfers.length === 0 && (
                      <div className="text-center py-12">
                        <p className="text-lg text-ink/60 mb-2">Здесь появятся переводы внутри семьи</p>
                        <p className="text-sm text-ink/50">Создайте первый перевод, чтобы начать</p>
                      </div>
                    )}
                </div>
              </Card>
              )}
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
          
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Выберите счета для семейной группы</label>
            <p className="text-xs text-ink/50 mb-2">Отметьте счета, которые хотите добавить в семью</p>
            <div className="space-y-2 max-h-48 overflow-y-auto border border-white/60 rounded-lg p-3">
              {accounts.map((account) => (
                <label key={account.id} className="flex items-center gap-2 p-2 hover:bg-white/50 rounded cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedAccountsForSharing.includes(account.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedAccountsForSharing(prev => [...prev, account.id]);
                      } else {
                        setSelectedAccountsForSharing(prev => prev.filter(id => id !== account.id));
                      }
                    }}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-ink">
                    {account.account_name || account.account_type} - {account.balance.toLocaleString('ru-RU')} ₽
                  </span>
                </label>
              ))}
              {accounts.length === 0 && (
                <p className="text-sm text-ink/50 text-center py-2">Нет доступных счетов</p>
              )}
            </div>
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
          
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Выберите счета для шаринга с семьей</label>
            <p className="text-xs text-ink/50 mb-2">Отметьте счета, которые хотите показывать семье</p>
            <div className="space-y-2 max-h-48 overflow-y-auto border border-white/60 rounded-lg p-3">
              {accounts.map((account) => (
                <label key={account.id} className="flex items-center gap-2 p-2 hover:bg-white/50 rounded cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedAccountsForSharing.includes(account.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedAccountsForSharing(prev => [...prev, account.id]);
                      } else {
                        setSelectedAccountsForSharing(prev => prev.filter(id => id !== account.id));
                      }
                    }}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-ink">{account.account_type} - {account.balance.toLocaleString()} ₽</span>
                </label>
              ))}
              {accounts.length === 0 && (
                <p className="text-sm text-ink/50 text-center py-4">У вас нет счетов</p>
              )}
            </div>
            <p className="text-xs text-ink/40 italic">
              💡 Вы сможете изменить это позже в настройках
            </p>
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
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Категория</label>
            <select
              className="input-field"
              value={budgetForm.category_id || ''}
              onChange={(event) => setBudgetForm((prev) => ({ ...prev, category_id: event.target.value }))}
            >
              <option value="">Без категории (общий бюджет)</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
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
              <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Целевая сумма (макс. 9 999 999 999 ₽)</label>
              <input
                className="input-field"
                type="number"
                min="0"
                max="9999999999"
                step="0.01"
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
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Со счета (мои семейные счета)</label>
            <select
              className="input-field"
              value={transferForm.from_account_id || ''}
              onChange={(event) => setTransferForm((prev) => ({ ...prev, from_account_id: event.target.value }))}
            >
              <option value="">Не указан</option>
              {familyAccounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.bank_name} • {account.account_name} • {Number(account.balance).toLocaleString('ru-RU')} ₽
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">На счет (семейные счета)</label>
            <select
              className="input-field"
              value={transferForm.to_account_id || ''}
              onChange={(event) => setTransferForm((prev) => ({ ...prev, to_account_id: event.target.value, to_member_id: undefined }))}
              required
            >
              <option value="">-- Выберите счет --</option>
              {familyAccounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.bank_name} • {account.account_name} • {Number(account.balance).toLocaleString('ru-RU')} ₽
                </option>
              ))}
            </select>
            <p className="text-xs text-ink/60 mt-1">
              💡 Выберите семейный счет или кошелек MyBank для перевода
            </p>
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Сумма</label>
            <input
              className="input-field"
              type="number"
              min="0"
              step="0.01"
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
              Создать запрос на перевод
            </Button>
          </div>
        </form>
      </Modal>

      {/* Модальное окно добавления счетов */}
      <Modal
        title="Добавить счета в семейную группу"
        open={isAddAccountModalOpen}
        onClose={() => setIsAddAccountModalOpen(false)}
      >
        <form onSubmit={async (e) => {
          e.preventDefault();
          if (!selectedFamilyId) return;
          
          try {
            // Get current user and member
            const currentUser = await api.getCurrentUser();
            const member = members.find(m => m.user_id === currentUser.id);
            
            if (!member) {
              toast.error('Вы не являетесь участником этой семьи');
              return;
            }
            
            if (selectedAccountsForSharing.length === 0) {
              toast.error('Выберите хотя бы один счет');
              return;
            }
            
            await api.addSharedAccounts(selectedFamilyId, member.id, selectedAccountsForSharing);
            toast.success(`Добавлено счетов: ${selectedAccountsForSharing.length}`);
            setIsAddAccountModalOpen(false);
            setSelectedAccountsForSharing([]);
            loadFamilyData(selectedFamilyId);
          } catch (error: any) {
            console.error('Failed to add accounts:', error);
            toast.error('Не удалось добавить счета');
          }
        }} className="space-y-5">
          <div className="space-y-3">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">
              Выберите счета для добавления
            </label>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {accounts.map((account) => (
                <label
                  key={account.id}
                  className="flex items-center gap-3 p-3 rounded-lg border border-white/60 bg-white/50 hover:bg-white/70 cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedAccountsForSharing.includes(account.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedAccountsForSharing([...selectedAccountsForSharing, account.id]);
                      } else {
                        setSelectedAccountsForSharing(selectedAccountsForSharing.filter(id => id !== account.id));
                      }
                    }}
                    className="w-4 h-4"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-ink">{account.account_name}</div>
                    <div className="text-sm text-ink/60">
                      {account.bank_name || account.bank_provider} • {formatCurrency(account.balance)}
                    </div>
                  </div>
                </label>
              ))}
            </div>
            {accounts.length === 0 && (
              <p className="text-sm text-ink/60">У вас нет доступных счетов</p>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" className="border border-white/60 bg-white/70" onClick={() => setIsAddAccountModalOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" variant="primary" disabled={selectedAccountsForSharing.length === 0}>
              Добавить ({selectedAccountsForSharing.length})
            </Button>
          </div>
        </form>
      </Modal>

      {/* Contribution Modal */}
      <Modal 
        title={`Внести взнос: ${selectedGoalForContribution?.name || ''}`} 
        open={isContributionModalOpen} 
        onClose={() => {
          setIsContributionModalOpen(false);
          setContributionAmount('');
          setContributionAccountId(null);
          setSelectedGoalForContribution(null);
        }}
      >
        <form onSubmit={handleContributeToGoal} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Сумма взноса</label>
            <input
              type="number"
              min="0"
              step="0.01"
              className="input-field"
              value={contributionAmount}
              onChange={(e) => setContributionAmount(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-ink/45">Со счета (семейные счета)</label>
            <select
              className="input-field"
              value={contributionAccountId || ''}
              onChange={(e) => setContributionAccountId(Number(e.target.value))}
              required
            >
              <option value="">-- Выберите счет --</option>
              {familyAccounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.bank_name} • {account.account_name} • {formatCurrency(account.balance)} ₽
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2">
            <Button 
              type="button" 
              variant="ghost" 
              className="border border-white/60 bg-white/70" 
              onClick={() => {
                setIsContributionModalOpen(false);
                setContributionAmount('');
                setContributionAccountId(null);
                setSelectedGoalForContribution(null);
              }}
            >
              Отмена
            </Button>
            <Button type="submit" variant="primary">
              💰 Внести взнос
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default FamilyHubPage;


