import { useEffect, useState } from 'react';
import { api } from '../services/api';
import Card from './common/Card';
import { formatCurrency } from '../utils/formatters';

interface Insight {
  type: 'success' | 'warning' | 'alert' | 'info';
  title: string;
  message: string;
  icon: string;
  value?: number;
  details?: Record<string, any>;
}

interface FinancialHealth {
  score: number;
  grade: string;
  message: string;
  details: {
    savings_rate: number;
    expense_stability: number;
    months_of_runway: number;
  };
}

export default function AIInsights() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [health, setHealth] = useState<FinancialHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInsights();
  }, []);

  const loadInsights = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Загружаем инсайты и оценку здоровья параллельно
      const [insightsResponse, healthResponse] = await Promise.all([
        api.get('/analytics/ai-insights'),
        api.get('/analytics/financial-health')
      ]);

      setInsights(insightsResponse.data.insights || []);
      setHealth(healthResponse.data.health || null);
    } catch (err: any) {
      console.error('Failed to load AI insights:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить инсайты');
    } finally {
      setLoading(false);
    }
  };

  const getTypeStyles = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'alert':
        return 'bg-red-50 border-red-200 text-red-800';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  const getGradeColor = (grade: string) => {
    if (grade.startsWith('A')) return 'text-green-600';
    if (grade === 'B') return 'text-blue-600';
    if (grade === 'C') return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-neutral-600">Анализируем ваши финансы...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6 bg-red-50 border-red-200">
        <p className="text-red-800">❌ {error}</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Финансовое здоровье */}
      {health && (
        <Card className="p-6 bg-gradient-to-br from-primary-50 to-secondary-50">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-neutral-900 mb-1">
                Финансовое здоровье
              </h3>
              <p className="text-sm text-neutral-600">{health.message}</p>
            </div>
            <div className="text-center">
              <div className={`text-5xl font-bold ${getGradeColor(health.grade)}`}>
                {health.grade}
              </div>
              <div className="text-sm text-neutral-600 mt-1">
                {health.score}/100
              </div>
            </div>
          </div>

          {/* Детали */}
          <div className="mt-4 grid grid-cols-3 gap-4">
            <div className="bg-white/50 rounded-lg p-3">
              <div className="text-xs text-neutral-600">Норма сбережений</div>
              <div className="text-lg font-semibold text-neutral-900">
                {health.details.savings_rate.toFixed(1)}%
              </div>
            </div>
            <div className="bg-white/50 rounded-lg p-3">
              <div className="text-xs text-neutral-600">Стабильность</div>
              <div className="text-lg font-semibold text-neutral-900">
                {health.details.expense_stability.toFixed(0)}%
              </div>
            </div>
            <div className="bg-white/50 rounded-lg p-3">
              <div className="text-xs text-neutral-600">Резерв</div>
              <div className="text-lg font-semibold text-neutral-900">
                {health.details.months_of_runway.toFixed(1)} мес
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* AI Инсайты */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-neutral-900">
            🤖 AI Рекомендации
          </h3>
          <button
            onClick={loadInsights}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            ↻ Обновить
          </button>
        </div>

        {insights.length === 0 ? (
          <Card className="p-6 text-center">
            <p className="text-neutral-600">
              📊 Недостаточно данных для анализа. Совершите несколько транзакций.
            </p>
          </Card>
        ) : (
          <div className="space-y-3">
            {insights.map((insight, index) => (
              <Card
                key={index}
                className={`p-4 border-l-4 ${getTypeStyles(insight.type)}`}
              >
                <div className="flex items-start">
                  <span className="text-2xl mr-3">{insight.icon}</span>
                  <div className="flex-1">
                    <h4 className="font-semibold mb-1">{insight.title}</h4>
                    <p className="text-sm">{insight.message}</p>
                    
                    {insight.value !== undefined && insight.value !== null && (
                      <div className="mt-2 text-lg font-bold">
                        {formatCurrency(insight.value)}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Подсказка */}
      <Card className="p-4 bg-neutral-50">
        <p className="text-xs text-neutral-600 text-center">
          💡 Инсайты обновляются каждые 24 часа на основе ваших транзакций за последние 90 дней
        </p>
      </Card>
    </div>
  );
}







