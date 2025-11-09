import axios, { AxiosInstance } from 'axios';
import { handleAPIError, retryWithBackoff } from '../utils/errorHandler';
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

  async contributeToGoal(goalId: number, amount: number, from_card_id?: string): Promise<any> {
    const response = await this.client.post(`/goals/${goalId}/contribute`, { 
      amount,
      from_card_id 
    });
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
    const response = await this.client.post('/gost/test');
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

  // ==================== Family Banking Hub ====================
  
  async getFamilyGroups() {
    return this.get('/family/groups');
  }

  async createFamilyGroup(data: { name: string; description?: string }) {
    return this.post('/family/groups', data);
  }

  async createFamily(data: { name: string; description?: string }) {
    const response = await this.createFamilyGroup(data);
    return response.data;
  }

  async rotateFamilyInvite(familyId: number) {
    const response = await this.post(`/family/groups/${familyId}/invite`, {});
    return response.data;
  }

  async getFamilyMembers(familyId: number, includePending = false) {
    const params = includePending ? '?include_pending=true' : '';
    return this.get(`/family/groups/${familyId}/members${params}`);
  }

  async joinFamily(inviteCode: string) {
    // Backend expects invite_code in body, family lookup by invite_code
    return this.post(`/family/join`, { invite_code: inviteCode });
  }

  async approveMember(familyId: number, memberId: number) {
    return this.post(`/family/groups/${familyId}/members/${memberId}/approve`, {});
  }

  async rejectFamilyMember(familyId: number, memberId: number) {
    return this.post(`/family/groups/${familyId}/members/${memberId}/reject`, {});
  }

  async addSharedAccounts(familyId: number, memberId: number, accountIds: number[]) {
    console.log(`🌐 API: addSharedAccounts(familyId=${familyId}, memberId=${memberId}, accountIds=[${accountIds.join(', ')}])`);
    return this.post(`/family/groups/${familyId}/members/${memberId}/shared-accounts`, accountIds);
  }

  async setSharedAccounts(familyId: number, memberId: number, accountIds: number[]) {
    console.log(`🌐 API: setSharedAccounts(familyId=${familyId}, memberId=${memberId}, accountIds=[${accountIds.join(', ')}])`);
    return this.put(`/family/groups/${familyId}/members/${memberId}/shared-accounts`, accountIds);
  }

  async removeSharedAccount(familyId: number, memberId: number, accountId: number) {
    console.log(`🌐 API: removeSharedAccount(familyId=${familyId}, memberId=${memberId}, accountId=${accountId})`);
    return this.delete(`/family/groups/${familyId}/members/${memberId}/shared-accounts/${accountId}`);
  }

  async getFamilySharedAccounts(familyId: number) {
    console.log(`🌐 API: getFamilySharedAccounts(familyId=${familyId})`);
    const response = await this.get(`/family/groups/${familyId}/shared-accounts`);
    console.log(`🌐 API Response:`, response);
    console.log(`🌐 API Response.data:`, response.data);
    return response.data || response;  // Извлекаем data из Axios response
  }

  async getMemberLimits(familyId: number, memberId: number) {
    return this.get(`/family/groups/${familyId}/members/${memberId}/limits`);
  }

  async createMemberLimit(familyId: number, data: any) {
    return this.post(`/family/groups/${familyId}/limits`, data);
  }

  async getFamilyTransfers(familyId: number) {
    return this.get(`/family/groups/${familyId}/transfers`);
  }

  async createFamilyTransfer(familyId: number, data: any) {
    return this.post(`/family/groups/${familyId}/transfers`, data);
  }

  async approveFamilyTransfer(familyId: number, transferId: number, approved: boolean, reason?: string) {
    return this.post(`/family/groups/${familyId}/transfers/${transferId}/approve`, { approved, reason });
  }

  async getFamilyAnalytics(familyId: number, periodDays = 30) {
    return this.get(`/family/groups/${familyId}/analytics/summary`, { period_days: periodDays });
  }

  async getFamilyNotifications(familyId: number) {
    return this.get(`/family/groups/${familyId}/notifications`);
  }

  async getFamilyActivity(familyId: number, limit = 50) {
    return this.get(`/family/groups/${familyId}/activity`, { limit });
  }

  // Family Budgets
  async createFamilyBudget(familyId: number, data: any) {
    return this.post(`/family/groups/${familyId}/budgets`, data);
  }

  async getFamilyBudgets(familyId: number) {
    return this.get(`/family/groups/${familyId}/budgets`);
  }

  async deleteFamilyBudget(familyId: number, budgetId: number) {
    return this.delete(`/family/groups/${familyId}/budgets/${budgetId}`);
  }

  // Family Goals
  async createFamilyGoal(familyId: number, data: any) {
    return this.post(`/family/groups/${familyId}/goals`, data);
  }

  async getFamilyGoals(familyId: number) {
    return this.get(`/family/groups/${familyId}/goals`);
  }

  async deleteFamilyGoal(familyId: number, goalId: number) {
    return this.delete(`/family/groups/${familyId}/goals/${goalId}`);
  }

  async contributeToFamilyGoal(familyId: number, goalId: number, data: { amount: number }) {
    return this.post(`/family/groups/${familyId}/goals/${goalId}/contributions`, data);
  }

  // Family Limits
  async setFamilyLimit(familyId: number, memberId: number, data: any) {
    return this.post(`/family/groups/${familyId}/members/${memberId}/limits`, data);
  }

  async getFamilyLimits(familyId: number, memberId?: number) {
    const endpoint = memberId 
      ? `/family/groups/${familyId}/members/${memberId}/limits`
      : `/family/groups/${familyId}/limits`;
    return this.get(endpoint);
  }

  // Aliases for FamilyHubPage compatibility
  async listFamilies() {
    const response = await this.getFamilyGroups();
    return response.data;
  }

  async getFamily(familyId: number) {
    const response = await this.get(`/family/groups/${familyId}`);
    return response.data;
  }

  async listFamilyBudgets(familyId: number) {
    const response = await this.getFamilyBudgets(familyId);
    return response.data;
  }

  async listFamilyGoals(familyId: number) {
    const response = await this.getFamilyGoals(familyId);
    return response.data;
  }

  async listFamilyMemberLimits(familyId: number) {
    // Get all members first, then fetch limits for each
    const membersResponse = await this.getFamilyMembers(familyId);
    const members = membersResponse.data;
    
    const allLimits: any[] = [];
    for (const member of members) {
      try {
        const limitsResponse = await this.getFamilyLimits(familyId, member.id);
        allLimits.push(...limitsResponse.data);
      } catch (error) {
        // Member might not have limits, that's okay
        console.log(`No limits for member ${member.id}`);
      }
    }
    
    return allLimits;
  }

  async listFamilyTransfers(familyId: number) {
    const response = await this.getFamilyTransfers(familyId);
    return response.data;
  }

  async listFamilyNotifications(familyId: number) {
    const response = await this.getFamilyNotifications(familyId);
    return response.data;
  }

}

export const api = new APIService();

