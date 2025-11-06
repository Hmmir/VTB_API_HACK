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

// Family Hub types
export interface Family {
  id: number;
  name: string;
  description?: string;
  invite_code: string;
  created_at: string;
  updated_at: string;
  role: string;
  status: string;
}

export interface FamilyMember {
  id: number;
  user_id: number;
  role: string;
  status: string;
  joined_at?: string;
  show_accounts?: boolean;
  default_visibility?: string;
  custom_limits?: Record<string, unknown> | null;
}

export interface FamilyDetail extends Family {
  members: FamilyMember[];
}

export interface FamilyBudget {
  id: number;
  name: string;
  amount: number;
  period: string;
  status: string;
  category_id?: number;
  start_date?: string;
  end_date?: string;
  created_at: string;
  updated_at: string;
}

export interface FamilyMemberLimit {
  id: number;
  member_id: number;
  amount: number;
  period: string;
  status: string;
  category_id?: number;
  auto_unlock: boolean;
  created_at: string;
  updated_at: string;
}

export interface FamilyGoal {
  id: number;
  name: string;
  description?: string;
  target_amount: number;
  current_amount: number;
  deadline?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface FamilyGoalContribution {
  id: number;
  goal_id: number;
  member_id: number;
  amount: number;
  source_account_id?: number;
  scheduled: boolean;
  schedule_rule?: Record<string, unknown> | null;
  created_at: string;
}

export interface FamilyTransfer {
  id: number;
  family_id: number;
  from_member_id?: number;
  to_member_id?: number;
  from_account_id?: number;
  to_account_id?: number;
  requested_by_member_id?: number;
  approved_by_member_id?: number;
  amount: number;
  currency: string;
  description?: string;
  status: string;
  created_at: string;
  approved_at?: string;
  executed_at?: string;
  failed_reason?: string;
}

export interface FamilyNotification {
  id: number;
  family_id: number;
  member_id?: number;
  notification_type: string;
  payload?: Record<string, unknown> | null;
  status: string;
  created_at: string;
  read_at?: string;
}

export interface FamilyAnalyticsSummary {
  total_balance: number;
  total_income: number;
  total_expense: number;
  budgets: Array<Record<string, unknown>>;
  member_spending: Array<Record<string, unknown>>;
  category_spending: Array<Record<string, unknown>>;
  goals: Array<Record<string, unknown>>;
}

