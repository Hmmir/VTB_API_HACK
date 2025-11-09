/**
 * Family Banking Hub types
 */

export interface FamilyGroup {
  id: number;
  name: string;
  created_by: number;
  invite_code: string;
  created_at: string;
  updated_at: string;
  member_count?: number;
}

// Aliases for compatibility
export type Family = FamilyGroup;
export type FamilyDetail = FamilyGroup;

export interface FamilyMember {
  id: number;
  family_id: number;
  user_id: number;
  role: 'admin' | 'member';
  status: 'pending' | 'active' | 'blocked';
  joined_at: string;
  user_name?: string;
  user_email?: string;
}

export interface FamilyBudget {
  id: number;
  family_id: number;
  category_id?: number;
  name: string;
  amount: number;
  period: 'weekly' | 'monthly';
  start_date: string;
  end_date?: string;
  status: string;
  created_at: string;
  current_spending?: number;
  spent?: number; // Alias for current_spending
  category_name?: string;
  usage_percentage?: number;
}

export interface FamilyMemberLimit {
  id: number;
  family_id: number;
  member_id: number;
  category_id?: number;
  amount: number;
  period: 'weekly' | 'monthly';
  auto_unlock: boolean;
  status: string;
  created_at: string;
  current_spending?: number;
  member_name?: string;
  category_name?: string;
}

export interface FamilyGoal {
  id: number;
  family_id: number;
  name: string;
  description?: string;
  target_amount: number;
  current_amount: number;
  deadline?: string;
  status: 'active' | 'completed' | 'archived';
  created_by?: number;
  created_at: string;
  completed_at?: string;
  progress_percentage?: number;
  contributions?: FamilyGoalContribution[];
}

export interface FamilyGoalContribution {
  id: number;
  goal_id: number;
  member_id: number;
  amount: number;
  source_account_id?: number;
  created_at: string;
  member_name?: string;
}

export interface FamilyTransfer {
  id: number;
  family_id: number;
  from_member_id: number;
  to_member_id: number;
  from_account_id?: number;
  to_account_id?: number;
  amount: number;
  currency: string;
  description?: string;
  status: 'pending' | 'approved' | 'rejected' | 'executed';
  created_at: string;
  executed_at?: string;
  approved_by?: number;
  from_member_name?: string;
  to_member_name?: string;
}

export interface FamilyNotification {
  id: number;
  family_id: number;
  member_id?: number;
  type: string;
  notification_type?: string; // Alias for type
  payload: any;
  status: string;
  created_at: string;
}

export interface FamilyAnalyticsSummary {
  total_income: number;
  total_expenses: number;
  total_expense?: number; // Alias for total_expenses
  net_balance: number;
  total_balance?: number; // Total balance of all accounts
  category_spending?: Array<{
    category: string;
    amount: number;
  }>;
  budget_usage: Array<{
    budget_id: number;
    name: string;
    amount: number;
    spent: number;
    percentage: number;
  }>;
  limit_usage: Array<{
    limit_id: number;
    member_id: number;
    amount: number;
    spent: number;
    percentage: number;
  }>;
  goal_progress: Array<{
    goal_id: number;
    name: string;
    target: number;
    current: number;
    percentage: number;
    status: string;
  }>;
  top_categories: Array<{
    category: string;
    amount: number;
  }>;
  member_spending: Array<{
    member_id: number;
    user_id: number;
    spent: number;
  }>;
}

