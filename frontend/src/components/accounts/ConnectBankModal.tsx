import { useEffect, useMemo, useState } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import { api } from '../../services/api';
import toast from 'react-hot-toast';

export interface SecurityEventPayload {
  title: string;
  description: string;
  meta?: string;
}

interface ConnectBankModalProps {
  open: boolean;
  onClose: () => void;
  onConnected?: (event?: SecurityEventPayload) => void;
}

type BankInfo = {
  code: string;
  name: string;
  description: string;
};

type Step = 'select' | 'consent' | 'success';

type ConsentState = {
  balance: boolean;
  transactions: boolean;
  profile: boolean;
  acknowledge: boolean;
  gostAck: boolean;
};

// Removed CLIENT_OPTIONS - auto-connect uses current user

const OAUTH_SCOPES = [
  {
    id: 'accounts.read',
    label: 'Просмотр счетов',
    description: 'Баланс, реквизиты и статус счетов для агрегирования в панели.'
  },
  {
    id: 'transactions.read',
    label: 'История операций',
    description: 'Транзакции последних 90 дней с категоризацией для рекомендаций.'
  },
  {
    id: 'profile.basic',
    label: 'Базовый профиль',
    description: 'Имя клиента, тип договора и метки риска.'
  }
];

const HANDSHAKE_TIMELINE = [
  'Инициирована OAuth-редирект с передачей client_id и redirect_uri',
  'Пользователь подтверждает выдачу токена доступа',
  'VTB API Sandbox возвращает authorization_code',
  'FinanceHub обменивает код на access_token и refresh_token',
  'Генерируется запись в журнале безопасности и синхронизация счетов'
];

const createConsentState = (isGost: boolean): ConsentState => ({
  balance: true,
  transactions: true,
  profile: true,
  acknowledge: false,
  gostAck: !isGost
});

export function ConnectBankModal({ open, onClose, onConnected }: ConnectBankModalProps) {
  const [banks, setBanks] = useState<BankInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [isGostMode, setIsGostMode] = useState(false);
  const [step, setStep] = useState<Step>('select');
  const [selectedBank, setSelectedBank] = useState<BankInfo | null>(null);
  const [consentState, setConsentState] = useState<ConsentState>(createConsentState(false));

  useEffect(() => {
    if (!open) {
      return;
    }

    setStep('select');
    setSelectedBank(null);
    setConsentState(createConsentState(isGostMode));

    (async () => {
      try {
        const res = await api.getAvailableBanks();
        setBanks(res.banks || []);
        
        const user = await api.getCurrentUser();
        const gost = Boolean(user.use_gost_mode);
        setIsGostMode(gost);
        setConsentState(createConsentState(gost));
      } catch (error) {
        toast.error('Не удалось загрузить список банков');
      }
    })();
  }, [open]);

  useEffect(() => {
    if (!selectedBank) {
      return;
    }
    // Reset consent state whenever bank changes
    setConsentState(createConsentState(isGostMode));
  }, [selectedBank, isGostMode]);

  const handleSelectBank = (bank: BankInfo) => {
    setSelectedBank(bank);
    setStep('consent');
  };

  const handleReset = () => {
    setStep('select');
    setSelectedBank(null);
    setConsentState(createConsentState(isGostMode));
    setLoading(false);
  };

  const canConfirmConsent = useMemo(() => {
    if (!consentState.acknowledge) {
      return false;
    }
    if (isGostMode && !consentState.gostAck) {
      return false;
    }
    return true;
  }, [consentState, isGostMode]);

  const connect = async () => {
    if (!selectedBank) {
      return;
    }

    setLoading(true);
    try {
      await api.connectBankDemo(selectedBank.code, '0'); // Use auto-assigned client
      toast.success('Банк подключен');

      const event: SecurityEventPayload = {
        title: `Подключение банка ${selectedBank.name}`,
        description: isGostMode
          ? 'ГОСТ-туннель активирован, токены зашифрованы по ГОСТ Р 34.10-2012.'
          : 'OAuth-сессия sandbox завершена, токены сохранены локально.',
        meta: 'Счета синхронизированы'
      };

      onConnected?.(event);
      setStep('success');
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Ошибка подключения');
    } finally {
      setLoading(false);
    }
  };

  const closeAndReset = () => {
    onClose();
    setTimeout(() => handleReset(), 300);
  };

  return (
    <Modal title="Подключение банка" open={open} onClose={closeAndReset}>
      <div className="space-y-6">
        {step === 'select' && (
          <>
            <div className="rounded-[1.2rem] border border-white/40 bg-white/60 p-4 text-sm text-ink/60">
              <p className="font-semibold text-ink">
                {isGostMode ? '🔒 ГОСТ режим активирован' : '🧪 Sandbox подключение'}
              </p>
              <p className="mt-2">Выберите банк для подключения. Система автоматически синхронизирует счета текущего пользователя.</p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {banks.map((bank) => (
                <div
                  key={bank.code}
                  className="rounded-[1.2rem] border border-white/40 bg-white/60 p-4 shadow-[0_12px_24px_rgba(14,23,40,0.08)]"
                >
                  <p className="text-sm font-semibold text-ink">{bank.name}</p>
                  <p className="mt-2 text-xs text-ink/55 min-h-[48px]">{bank.description}</p>
                  <Button className="mt-3 w-full" onClick={() => handleSelectBank(bank)}>
                    Инициировать OAuth
                  </Button>
                </div>
              ))}
            </div>
          </>
        )}

        {step === 'consent' && selectedBank && (
          <div className="space-y-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Редирект</p>
                <h3 className="text-xl font-semibold text-ink">{selectedBank.name}</h3>
                <p className="mt-1 text-xs text-ink/50">OAuth 2.0 / OpenID Connect</p>
              </div>
              <Button variant="ghost" size="sm" onClick={handleReset} className="border border-white/40 bg-white/60 text-ink">
                Назад
              </Button>
            </div>

            <div className="space-y-3 rounded-[1.2rem] border border-white/40 bg-white/60 p-4">
              <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Запрашиваемые права</p>
              <div className="space-y-3">
                {OAUTH_SCOPES.map((scope) => (
                  <label key={scope.id} className="flex items-start gap-3 rounded-[1rem] border border-white/30 bg-white/70 p-3 text-xs text-ink/60">
                    <input type="checkbox" checked disabled className="mt-1" />
                    <span>
                      <span className="block font-semibold text-ink">{scope.label}</span>
                      <span>{scope.description}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-2 rounded-[1.2rem] border border-white/40 bg-white/60 p-4 text-xs text-ink/60">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={consentState.acknowledge}
                  onChange={(e) => setConsentState((prev) => ({ ...prev, acknowledge: e.target.checked }))}
                />
                <span>Я подтверждаю, что банк {selectedBank.name} может предоставить доступ к данным и понимаю условия обработки.</span>
              </label>
              {isGostMode && (
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={consentState.gostAck}
                    onChange={(e) => setConsentState((prev) => ({ ...prev, gostAck: e.target.checked }))}
                  />
                  <span>Я подтверждаю согласование ГОСТ-канала и активацию криптографических ключей.</span>
                </label>
              )}
            </div>

            <div className="flex justify-end gap-3">
              <Button variant="ghost" onClick={handleReset} className="border border-white/40 bg-white/60 text-ink">
                Отмена
              </Button>
              <Button
                variant="primary"
                onClick={connect}
                disabled={!canConfirmConsent || loading}
                isLoading={loading}
              >
                Подтвердить доступ
              </Button>
            </div>
          </div>
        )}

        {step === 'success' && selectedBank && (
          <div className="space-y-6">
            <div className="rounded-[1.2rem] border border-white/40 bg-white/60 px-4 py-3 text-sm text-ink/60">
              <p className="text-lg font-semibold text-ink">Подключение завершено</p>
              <p className="mt-1 text-xs text-ink/55">
                Трансфер ключей завершен {isGostMode ? 'через ГОСТ-шлюз. Сессия подписана.' : 'в sandbox-режиме.'} Журнал безопасности обновлен.
          </p>
        </div>

            <div className="space-y-3">
              <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Хендшейк</p>
              <ul className="space-y-2 text-xs text-ink/60">
                {HANDSHAKE_TIMELINE.map((item, index) => (
                  <li key={item} className="flex items-start gap-3">
                    <span className="mt-0.5 text-primary-600">{index + 1}.</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex justify-end gap-3">
              <Button variant="ghost" onClick={handleReset} className="border border-white/40 bg-white/60 text-ink">
                Подключить еще банк
              </Button>
              <Button variant="primary" onClick={closeAndReset}>
                Перейти к счетам
              </Button>
            </div>
        </div>
        )}
      </div>
    </Modal>
  );
}

export default ConnectBankModal;


