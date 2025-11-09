import toast from 'react-hot-toast';

export interface APIError {
  status: number;
  message: string;
  detail?: string;
}

/**
 * Centralized error handler for API responses
 */
export const handleAPIError = (error: any): APIError => {
  // Default error
  let apiError: APIError = {
    status: 500,
    message: 'Произошла ошибка. Попробуйте ещё раз.',
    detail: error?.message || 'Unknown error'
  };

  // Parse different error formats
  if (error?.response) {
    // Axios-style error
    const status = error.response.status;
    const data = error.response.data;
    
    apiError.status = status;
    apiError.detail = data?.detail || data?.message || error.message;
    
    // Map status codes to user-friendly messages
    switch (status) {
      case 400:
        apiError.message = 'Ошибка валидации данных';
        break;
      case 401:
        apiError.message = 'Требуется авторизация';
        break;
      case 403:
        apiError.message = 'Доступ запрещён';
        break;
      case 404:
        apiError.message = 'Ресурс не найден';
        break;
      case 409:
        apiError.message = 'Конфликт данных: запись уже существует или нарушены ограничения БД';
        break;
      case 422:
        apiError.message = 'Ошибка валидации данных';
        break;
      case 429:
        apiError.message = 'Слишком много запросов. Подождите немного';
        break;
      case 500:
        apiError.message = 'Ошибка сервера';
        break;
      case 502:
        apiError.message = 'Сервис временно недоступен';
        break;
      case 503:
        apiError.message = 'Сервис на обслуживании';
        break;
      default:
        apiError.message = `Ошибка ${status}`;
    }
  } else if (error?.message) {
    // Native JS error
    if (error.message.includes('Network Error') || error.message.includes('fetch')) {
      apiError.message = 'Проблема с соединением. Проверьте интернет';
    } else if (error.message.includes('timeout')) {
      apiError.message = 'Превышено время ожидания. Попробуйте ещё раз';
    }
  }

  return apiError;
};

/**
 * Show error toast with retry option
 */
export const showErrorToast = (error: any, retryFn?: () => void) => {
  const apiError = handleAPIError(error);
  
  // Show error toast
  const message = retryFn 
    ? `${apiError.message} (Нажмите для повтора)`
    : apiError.message;
  
  const toastId = toast.error(message, {
    duration: 5000,
    onClick: retryFn ? () => {
      toast.dismiss(toastId);
      retryFn();
    } : undefined
  });
  
  // Log detail for debugging
  console.error('[API Error]', apiError);
  
  return apiError;
};

/**
 * Retry mechanism with exponential backoff
 */
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> => {
  let lastError: any;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      lastError = error;
      
      // Don't retry on client errors (4xx)
      if (error?.response?.status >= 400 && error?.response?.status < 500) {
        throw error;
      }
      
      // Don't retry on last attempt
      if (attempt === maxRetries - 1) {
        break;
      }
      
      // Exponential backoff: 1s, 2s, 4s, 8s...
      const delay = baseDelay * Math.pow(2, attempt);
      console.log(`[Retry] Attempt ${attempt + 1} failed, retrying in ${delay}ms...`);
      
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
};

/**
 * Wrapper for API calls with automatic retry and error handling
 */
export const apiCall = async <T>(
  fn: () => Promise<T>,
  options?: {
    retries?: number;
    showError?: boolean;
    retryFn?: () => void;
  }
): Promise<T> => {
  const { retries = 3, showError = true, retryFn } = options || {};
  
  try {
    return await retryWithBackoff(fn, retries);
  } catch (error) {
    if (showError) {
      showErrorToast(error, retryFn);
    }
    throw error;
  }
};
