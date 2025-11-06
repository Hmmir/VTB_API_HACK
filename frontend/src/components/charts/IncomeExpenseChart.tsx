import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { formatCompactCurrency } from '../../utils/formatters';

interface MonthlyData {
  month: string;
  income: number;
  expense: number;
}

interface IncomeExpenseChartProps {
  data: MonthlyData[];
}

export default function IncomeExpenseChart({ data }: IncomeExpenseChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 12 }}
          stroke="rgba(0,0,0,0.3)"
        />
        <YAxis
          tick={{ fontSize: 12 }}
          stroke="rgba(0,0,0,0.3)"
          tickFormatter={(value) => formatCompactCurrency(value, '')}
        />
        <Tooltip
          formatter={(value: number, name: string) => [
            formatCompactCurrency(value),
            name === 'income' ? 'Доходы' : 'Расходы'
          ]}
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid rgba(0, 0, 0, 0.1)',
            borderRadius: '8px',
            padding: '8px 12px',
          }}
        />
        <Legend
          formatter={(value) => value === 'income' ? 'Доходы' : 'Расходы'}
        />
        <Bar dataKey="income" fill="#24B09A" name="income" radius={[8, 8, 0, 0]} />
        <Bar dataKey="expense" fill="#FF6B9D" name="expense" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

