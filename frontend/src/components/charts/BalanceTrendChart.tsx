import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { formatCompactCurrency, formatDate } from '../../utils/formatters';

interface BalanceData {
  date: string;
  balance: number;
}

interface BalanceTrendChartProps {
  data: BalanceData[];
}

export default function BalanceTrendChart({ data }: BalanceTrendChartProps) {
  const chartData = data.map(item => ({
    date: formatDate(item.date),
    balance: item.balance,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          stroke="rgba(0,0,0,0.3)"
        />
        <YAxis
          tick={{ fontSize: 12 }}
          stroke="rgba(0,0,0,0.3)"
          tickFormatter={(value) => formatCompactCurrency(value, '')}
        />
        <Tooltip
          formatter={(value: number) => [formatCompactCurrency(value), 'Баланс']}
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid rgba(0, 0, 0, 0.1)',
            borderRadius: '8px',
            padding: '8px 12px',
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="balance"
          stroke="#24B09A"
          strokeWidth={2}
          dot={{ fill: '#24B09A', r: 4 }}
          activeDot={{ r: 6 }}
          name="Баланс"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

