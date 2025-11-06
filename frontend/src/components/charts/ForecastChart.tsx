import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts';
import { formatCompactCurrency, formatDate } from '../../utils/formatters';

interface ForecastData {
  date: string;
  actual?: number;
  forecast: number;
  lower_bound?: number;
  upper_bound?: number;
}

interface ForecastChartProps {
  data: ForecastData[];
  forecastStartIndex: number;
}

export default function ForecastChart({ data, forecastStartIndex }: ForecastChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          stroke="rgba(0,0,0,0.3)"
          tickFormatter={(value) => {
            const date = new Date(value);
            return date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
          }}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          stroke="rgba(0,0,0,0.3)"
          tickFormatter={(value) => formatCompactCurrency(value, '')}
        />
        <Tooltip
          formatter={(value: number, name: string) => [
            formatCompactCurrency(value),
            name === 'actual' ? 'Факт' : name === 'forecast' ? 'Прогноз' : name === 'lower_bound' ? 'Мин' : 'Макс'
          ]}
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid rgba(0, 0, 0, 0.1)',
            borderRadius: '8px',
            padding: '8px 12px',
          }}
        />
        <Legend
          formatter={(value) => 
            value === 'actual' ? 'Факт' : 
            value === 'forecast' ? 'Прогноз' : 
            value === 'lower_bound' ? 'Мин' : 'Макс'
          }
        />
        <ReferenceLine
          x={data[forecastStartIndex]?.date}
          stroke="#FF6B9D"
          strokeDasharray="3 3"
          label={{ value: 'Прогноз', position: 'top', fill: '#FF6B9D', fontSize: 12 }}
        />
        <Line
          type="monotone"
          dataKey="actual"
          stroke="#24B09A"
          strokeWidth={2}
          dot={{ fill: '#24B09A', r: 4 }}
          activeDot={{ r: 6 }}
          name="actual"
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="forecast"
          stroke="#FF6B9D"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={{ fill: '#FF6B9D', r: 4 }}
          activeDot={{ r: 6 }}
          name="forecast"
        />
        {data[0]?.lower_bound !== undefined && (
          <>
            <Line
              type="monotone"
              dataKey="lower_bound"
              stroke="#9C27B0"
              strokeWidth={1}
              strokeDasharray="2 2"
              dot={false}
              name="lower_bound"
            />
            <Line
              type="monotone"
              dataKey="upper_bound"
              stroke="#9C27B0"
              strokeWidth={1}
              strokeDasharray="2 2"
              dot={false}
              name="upper_bound"
            />
          </>
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}

