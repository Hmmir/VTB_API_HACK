/**
 * Format large numbers with K/M/B suffixes
 * Examples: 1500 -> 1.5K, 1500000 -> 1.5M, 1500000000 -> 1.5B
 */
export function formatCompactNumber(value: number): string {
  const absValue = Math.abs(value);
  
  if (absValue >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)}B`;
  }
  if (absValue >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  }
  if (absValue >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`;
  }
  
  return value.toFixed(0);
}

/**
 * Format currency with proper spacing and ruble sign
 * Examples: 1500 -> "1 500 ₽", 1500000 -> "1 500 000 ₽"
 */
export function formatCurrency(value: number, currency: string = 'RUB'): string {
  const formatted = new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
  
  const symbol = currency === 'RUB' ? '₽' : currency === 'USD' ? '$' : currency === 'EUR' ? '€' : currency;
  
  return `${formatted} ${symbol}`;
}

/**
 * Format currency in compact form for cards/buttons
 * Examples: 1500000 -> "1.5M ₽", 500000 -> "500K ₽"
 */
export function formatCompactCurrency(value: number, currency: string = 'RUB'): string {
  const symbol = currency === 'RUB' ? '₽' : currency === 'USD' ? '$' : currency === 'EUR' ? '€' : currency;
  return `${formatCompactNumber(value)} ${symbol}`;
}

/**
 * Format percentage
 */
export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

/**
 * Format date in Russian locale
 */
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

/**
 * Format date and time
 */
export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

