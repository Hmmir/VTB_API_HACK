import { useEffect, useState } from 'react';
import Button from './common/Button';
import Card from './common/Card';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

const PWAInstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      
      // Show prompt after 30 seconds if user hasn't dismissed it
      setTimeout(() => {
        const dismissed = localStorage.getItem('pwa-install-dismissed');
        if (!dismissed) {
          setShowPrompt(true);
        }
      }, 30000);
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('User accepted the install prompt');
    }

    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-install-dismissed', 'true');
  };

  if (!showPrompt || !deferredPrompt) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 animate-slide-up">
      <Card className="bg-gradient-to-br from-primary-100 via-white to-primary-50 shadow-2xl border-2 border-primary-200">
        <div className="p-6 space-y-4">
          <div className="flex items-start gap-3">
            <span className="text-3xl">📱</span>
            <div className="flex-1">
              <h3 className="text-lg font-display font-semibold text-ink mb-1">
                Установите FinanceHub
              </h3>
              <p className="text-sm text-ink/70">
                Добавьте приложение на главный экран для быстрого доступа и работы офлайн
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="primary"
              onClick={handleInstall}
              className="flex-1"
            >
              Установить
            </Button>
            <Button
              variant="ghost"
              onClick={handleDismiss}
              className="px-4"
            >
              Позже
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default PWAInstallPrompt;

