/**
 * Centralized Error Handler - Централизованная обработка ошибок
 */
import toast from 'react-hot-toast';

export interface APIError {
  detail?: string;
  errors?: string[];
  message?: string;
  path?: string;
  status?: number;
}

/**
 * Извлечь читаемое сообщение об ошибке из API response
 */
export function extractErrorMessage(error: any): string {
  // Axios error
  if (error.response) {
    const data = error.response.data;
    
    // Structured error from backend
    if (data.detail) {
      if (typeof data.detail === 'string') {
        return data.detail;
      }
      if (Array.isArray(data.detail)) {
        return data.detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ');
      }
    }
    
    // Validation errors
    if (data.errors && Array.isArray(data.errors)) {
      return data.errors.join('; ');
    }
    
    // Generic message
    if (data.message) {
      return data.message;
    }
    
    // HTTP status messages
    const status = error.response.status;
    switch (status) {
      case 400:
        return 'Некорректный запрос. Проверьте введённые данные.';
      case 401:
        return 'Необходима авторизация. Войдите в систему.';
      case 403:
        return 'Доступ запрещён. Недостаточно прав.';
      case 404:
        return 'Запрашиваемый ресурс не найден.';
      case 409:
        return 'Конфликт данных. Возможно, запись уже существует.';
      case 422:
        return 'Ошибка валидации данных.';
      case 429:
        return 'Слишком много запросов. Попробуйте позже.';
      case 500:
        return 'Внутренняя ошибка сервера. Попробуйте позже.';
      case 502:
        return 'Сервер временно недоступен.';
      case 503:
        return 'Сервис временно недоступен.';
      default:
        return `Ошибка ${status}: ${error.response.statusText || 'Неизвестная ошибка'}`;
    }
  }
  
  // Network error
  if (error.request) {
    return 'Ошибка сети. Проверьте подключение к интернету.';
  }
  
  // Other errors
  if (error.message) {
    return error.message;
  }
  
  return 'Произошла неизвестная ошибка';
}

/**
 * Handle API error and show toast notification
 */
export function handleAPIError(error: any, customMessage?: string): void {
  console.error('API Error:', error);
  
  const message = customMessage || extractErrorMessage(error);
  toast.error(message, {
    duration: 5000,
    position: 'top-right',
  });
}

/**
 * Handle success with toast notification
 */
export function handleSuccess(message: string): void {
  toast.success(message, {
    duration: 3000,
    position: 'top-right',
  });
}

/**
 * Handle info with toast notification
 */
export function handleInfo(message: string): void {
  toast(message, {
    duration: 4000,
    position: 'top-right',
    icon: 'ℹ️',
  });
}

/**
 * Handle loading state with toast
 */
export function handleLoading(message: string): string {
  return toast.loading(message, {
    position: 'top-right',
  });
}

/**
 * Dismiss toast by ID
 */
export function dismissToast(toastId: string): void {
  toast.dismiss(toastId);
}

/**
 * Try-catch wrapper for async operations
 */
export async function withErrorHandling<T>(
  operation: () => Promise<T>,
  errorMessage?: string,
  successMessage?: string
): Promise<T | null> {
  try {
    const result = await operation();
    if (successMessage) {
      handleSuccess(successMessage);
    }
    return result;
  } catch (error) {
    handleAPIError(error, errorMessage);
    return null;
  }
}

/**
 * Retry an operation with exponential backoff
 */
export async function retryOperation<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  let lastError: any;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error: any) {
      lastError = error;
      
      // Don't retry on client errors (4xx)
      if (error.response && error.response.status >= 400 && error.response.status < 500) {
        throw error;
      }
      
      // Wait before retry with exponential backoff
      if (i < maxRetries - 1) {
        const delay = initialDelay * Math.pow(2, i);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
}

