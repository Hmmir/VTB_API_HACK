// User types
export interface User {
  id: number;
  email: string;
  full_name?: string;
  phone?: string;
  is_active: boolean;
  use_gost_mode?: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
  phone?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Bank types
export interface BankConnection {
  id: number;
  bank_provider: string;
  status: string;
  last_synced_at?: string;
  created_at: string;
}

// Account types
export interface Account {
  id: number;
  bank_connection_id: number;
  account_name: string;
  account_number?: string;
  account_type: string;
  balance: number;
  currency: string;
  credit_limit?: number;
  is_active: number;
  last_synced_at?: string;
}

// Transaction types
export interface Transaction {
  id: number;
  account_id: number;
  category_id?: number;
  amount: number;
  transaction_type: string;
  description?: string;
  merchant?: string;
  transaction_date: string;
  is_pending: number;
  category?: Category;
}

// Category types
export interface Category {
  id: number;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  is_system: number;
}

// Budget types
export interface Budget {
  id: number;
  user_id: number;
  category_id?: number;
  name: string;
  amount: number;
  period: string;
  start_date: string;
  end_date?: string;
  is_active: number;
}

// Goal types
export interface Goal {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  target_amount: number;
  current_amount: number;
  target_date?: string;
  status: string;
  completed_at?: string;
}

// Bank Product types
export interface BankProduct {
  id: number;
  bank_provider: string;
  product_type: string;
  name: string;
  description?: string;
  interest_rate?: number;
  min_amount?: number;
  max_amount?: number;
  term_months?: number;
  url?: string;
}

// Recommendation types
export interface Recommendation {
  id: number;
  user_id: number;
  recommendation_type: string;
  title: string;
  description: string;
  estimated_savings?: string;
  priority: number;
  status: string;
  viewed_at?: string;
  created_at: string;
}

