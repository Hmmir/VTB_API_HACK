import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { formatCompactCurrency } from '../../utils/formatters';

interface SpendingData {
  category: string;
  amount: number;
  color: string;
}

interface SpendingChartProps {
  data: SpendingData[];
}

const COLORS = ['#24B09A', '#FF6B9D', '#FFC107', '#9C27B0', '#00BCD4', '#FF5722'];

export default function SpendingChart({ data }: SpendingChartProps) {
  const chartData = data.map((item, index) => ({
    name: item.category,
    value: Math.abs(item.amount),
    color: item.color || COLORS[index % COLORS.length],
  }));

  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="h-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => formatCompactCurrency(value)}
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid rgba(0, 0, 0, 0.1)',
              borderRadius: '8px',
              padding: '8px 12px',
            }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value, entry: any) => (
              <span className="text-sm">
                {value}: {formatCompactCurrency(entry.payload.value)}
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="text-center mt-2">
        <p className="text-xs text-text-secondary">Всего расходов</p>
        <p className="text-lg font-bold">{formatCompactCurrency(total)}</p>
      </div>
    </div>
  );
}

