import axios, { AxiosInstance } from 'axios';
import { handleAPIError, retryOperation } from '../utils/errorHandler';
import type {
  User,
  LoginCredentials,
  RegisterData,
  AuthTokens,
  BankConnection,
  Account,
  Transaction,
  Category,
  Budget,
  Goal,
  Recommendation
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const refreshToken = localStorage.getItem('refresh_token');
            const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
              refresh_token: refreshToken,
            });
            
            const { access_token, refresh_token } = response.data;
            localStorage.setItem('access_token', access_token);
            localStorage.setItem('refresh_token', refresh_token);
            
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Generic HTTP methods
  async get<T = any>(url: string, config?: any): Promise<{ data: T }> {
    return this.client.get(url, config);
  }

  async post<T = any>(url: string, data?: any, config?: any): Promise<{ data: T }> {
    return this.client.post(url, data, config);
  }

  async put<T = any>(url: string, data?: any, config?: any): Promise<{ data: T }> {
    return this.client.put(url, data, config);
  }

  async delete<T = any>(url: string, config?: any): Promise<{ data: T }> {
    return this.client.delete(url, config);
  }

  // Auth endpoints
  async register(data: RegisterData): Promise<User> {
    const response = await this.client.post('/auth/register', data);
    return response.data;
  }

  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await this.client.post('/auth/login', credentials);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // Bank endpoints
  async connectBank(bankProvider: string, authCode: string): Promise<BankConnection> {
    const response = await this.client.post('/banks/connect', {
      bank_provider: bankProvider,
      authorization_code: authCode,
    });
    return response.data;
  }

  async getBankConnections(): Promise<BankConnection[]> {
    const response = await this.client.get('/banks/connections');
    return response.data;
  }

  async syncBankConnection(connectionId: number): Promise<BankConnection> {
    const response = await this.client.post(`/banks/connections/${connectionId}/sync`);
    return response.data;
  }

  async deleteBankConnection(connectionId: number): Promise<void> {
    await this.client.delete(`/banks/connections/${connectionId}`);
  }

  // Transactions
  async getTransactions(params?: {
    account_id?: number;
    category_id?: number;
    transaction_type?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
  }): Promise<Transaction[]> {
    const response = await this.client.get('/transactions', { params });
    return response.data;
  }

  // Analytics
  async getAnalyticsSummary(periodDays: number = 30): Promise<any> {
    const response = await this.client.get('/analytics/summary', {
      params: { period_days: periodDays }
    });
    return response.data;
  }

  async getExpensesByCategory(periodDays: number = 30): Promise<any[]> {
    const response = await this.client.get('/analytics/by-category', {
      params: { period_days: periodDays }
    });
    return response.data;
  }

  async getSpendingTrends(periodDays: number = 30): Promise<any[]> {
    const response = await this.client.get('/analytics/trends', {
      params: { period_days: periodDays }
    });
    return response.data;
  }

  // OpenBanking Sandbox helpers
  async getAvailableBanks(): Promise<{ banks: { code: string; name: string; description: string }[] }> {
    const response = await this.client.get('/banks/available-banks');
    return response.data;
  }

  async connectBankDemo(bankCode: string, clientNumber: string = '1'): Promise<BankConnection> {
    const response = await this.client.post('/banks/connect-demo', { 
      bank_code: bankCode,
      client_number: clientNumber
    });
    return response.data;
  }

  // Account endpoints
  async getAccounts(): Promise<Account[]> {
    const response = await this.client.get('/accounts');
    return response.data;
  }

  async deleteAccount(accountId: number): Promise<void> {
    await this.client.delete(`/accounts/${accountId}`);
  }

  async transferFunds(payload: {
    from_account_id: number;
    to_account_id: number;
    amount: number;
    description?: string;
  }): Promise<{ message: string }> {
    const response = await this.client.post('/accounts/transfer', payload);
    return response.data;
  }

  async getAccount(accountId: number): Promise<Account> {
    const response = await this.client.get(`/accounts/${accountId}`);
    return response.data;
  }

  // Category endpoints
  async getCategories(): Promise<Category[]> {
    const response = await this.client.get('/categories');
    return response.data;
  }

  // Budget endpoints
  async getBudgets(): Promise<Budget[]> {
    const response = await this.client.get('/budgets');
    return response.data;
  }

  async createBudget(data: Partial<Budget>): Promise<Budget> {
    const response = await this.client.post('/budgets', data);
    return response.data;
  }

  async deleteBudget(budgetId: number): Promise<void> {
    await this.client.delete(`/budgets/${budgetId}`);
  }

  async getBudgetStatus(budgetId: number): Promise<any> {
    const response = await this.client.get(`/budgets/${budgetId}/status`);
    return response.data;
  }

  // Goal endpoints
  async getGoals(): Promise<Goal[]> {
    const response = await this.client.get('/goals');
    return response.data;
  }

  async createGoal(data: Partial<Goal>): Promise<Goal> {
    const response = await this.client.post('/goals', data);
    return response.data;
  }

  async updateGoal(goalId: number, data: Partial<Goal>): Promise<Goal> {
    const response = await this.client.put(`/goals/${goalId}`, data);
    return response.data;
  }

  async deleteGoal(goalId: number): Promise<void> {
    await this.client.delete(`/goals/${goalId}`);
  }

  async contributeToGoal(goalId: number, amount: number): Promise<any> {
    const response = await this.client.post(`/goals/${goalId}/contribute`, { amount });
    return response.data;
  }

  // Product endpoints
  async getBankProducts(filters?: any): Promise<any> {
    const response = await this.client.get('/products/', { params: filters });
    return response.data;
  }

  async createProductAgreement(data: {
    bank_product_id: string;
    linked_account_id: number;
    amount: number;
    term_months: number;
  }): Promise<any> {
    const response = await this.client.post('/products/agreements', data);
    return response.data;
  }

  async getBankProduct(productId: string, bankCode: string): Promise<any> {
    const response = await this.client.get(`/products/${productId}`, { params: { bank_code: bankCode } });
    return response.data;
  }

  async compareProducts(productType: string): Promise<any> {
    const response = await this.client.get(`/products/compare/${productType}`);
    return response.data;
  }

  // Recommendation endpoints
  async getRecommendations(): Promise<Recommendation[]> {
    const response = await this.client.get('/recommendations');
    return response.data;
  }

  // System endpoints
  async getSystemInfo(): Promise<any> {
    const response = await this.client.get('/system/info');
    return response.data;
  }

  async getGostStatus(): Promise<any> {
    const response = await this.client.get('/gost/status');
    return response.data;
  }

  async testGostConnection(): Promise<{ success: boolean; message: string; [key: string]: any }> {
    const response = await this.client.get('/gost/test-connection');
    return response.data;
  }

  // Bank Capital endpoints
  async getBankCapital(): Promise<any[]> {
    try {
      const response = await retryOperation(() => this.client.get('/bank-capital/'));
      return response.data;
    } catch (error) {
      handleAPIError(error, 'Не удалось загрузить данные о капитале банков');
      return [];
    }
  }

  async getBankCapitalByCode(bankCode: string): Promise<any> {
    try {
      const response = await this.client.get(`/bank-capital/${bankCode}`);
      return response.data;
    } catch (error) {
      handleAPIError(error, `Не удалось загрузить данные о капитале банка ${bankCode}`);
      throw error;
    }
  }

  // Key Rate endpoints
  async getCurrentKeyRate(): Promise<any> {
    try {
      const response = await this.client.get('/key-rate/current');
      return response.data;
    } catch (error) {
      handleAPIError(error, 'Не удалось загрузить текущую ключевую ставку ЦБ');
      throw error;
    }
  }

  async getKeyRateHistory(limit: number = 10): Promise<any[]> {
    try {
      const response = await this.client.get('/key-rate/history', { params: { limit } });
      return response.data;
    } catch (error) {
      handleAPIError(error, 'Не удалось загрузить историю ключевой ставки');
      return [];
    }
  }
}

export const api = new APIService();

