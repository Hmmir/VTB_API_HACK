"""
AI-powered Budget Insights Service
Анализирует транзакции пользователя и генерирует персонализированные рекомендации
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.transaction import Transaction
from app.models.account import Account
from app.models.bank_connection import BankConnection


class AIInsightsService:
    """Service for generating AI-powered budget insights."""
    
    @staticmethod
    def generate_insights(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Генерирует 3-5 персонализированных инсайтов на основе истории транзакций.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of insights with type, title, message, value
        """
        insights = []
        
        # Получаем транзакции за последние 90 дней
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        # Получаем счета пользователя
        user_accounts = db.query(Account).join(BankConnection).filter(
            BankConnection.user_id == user_id
        ).all()
        
        account_ids = [acc.id for acc in user_accounts]
        
        if not account_ids:
            return [{
                "type": "info",
                "title": "Добро пожаловать!",
                "message": "Подключите банковский счёт, чтобы получить персонализированные рекомендации",
                "icon": "👋",
                "value": None
            }]
        
        # Получаем транзакции
        transactions = db.query(Transaction).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.created_at >= ninety_days_ago
        ).all()
        
        if not transactions:
            return [{
                "type": "info",
                "title": "Недостаточно данных",
                "message": "Совершите несколько транзакций, чтобы получить аналитику",
                "icon": "📊",
                "value": None
            }]
        
        # Инсайт 1: Топ категория расходов
        insight = AIInsightsService._analyze_top_spending_category(transactions)
        if insight:
            insights.append(insight)
        
        # Инсайт 2: Анализ трендов (неделя vs средние)
        insight = AIInsightsService._analyze_spending_trends(transactions)
        if insight:
            insights.append(insight)
        
        # Инсайт 3: Потенциал сбережений
        insight = AIInsightsService._analyze_savings_potential(transactions)
        if insight:
            insights.append(insight)
        
        # Инсайт 4: Необычная активность
        insight = AIInsightsService._detect_unusual_activity(transactions)
        if insight:
            insights.append(insight)
        
        # Инсайт 5: Рекомендация по оптимизации
        insight = AIInsightsService._generate_optimization_tip(transactions)
        if insight:
            insights.append(insight)
        
        return insights[:5]  # Максимум 5 инсайтов
    
    @staticmethod
    def _analyze_top_spending_category(transactions: List[Transaction]) -> Dict[str, Any]:
        """Анализирует топ категорию расходов."""
        category_totals = defaultdict(float)
        
        for t in transactions:
            if t.amount < 0:  # Расход
                # Исправление: используем t.category.name вместо объекта Category
                category_name = t.category.name if t.category else "Другое"
                category_totals[category_name] += abs(float(t.amount))
        
        if not category_totals:
            return None
        
        top_category = max(category_totals, key=category_totals.get)
        top_amount = category_totals[top_category]
        total_expenses = sum(category_totals.values())
        percentage = (top_amount / total_expenses * 100) if total_expenses > 0 else 0
        
        return {
            "type": "warning" if percentage > 40 else "info",
            "title": f"Топ расход: {top_category}",
            "message": f"Составляет {percentage:.1f}% от всех расходов за 90 дней",
            "icon": "💰",
            "value": top_amount,
            "details": {
                "category": top_category,
                "amount": top_amount,
                "percentage": percentage
            }
        }
    
    @staticmethod
    def _analyze_spending_trends(transactions: List[Transaction]) -> Dict[str, Any]:
        """Анализирует тренды расходов."""
        # Расходы за последнюю неделю
        week_ago = datetime.utcnow() - timedelta(days=7)
        last_week_transactions = [t for t in transactions if t.created_at >= week_ago and t.amount < 0]
        last_week_total = sum(abs(float(t.amount)) for t in last_week_transactions)
        
        # Средние недельные расходы за 90 дней
        all_expenses = [t for t in transactions if t.amount < 0]
        if not all_expenses:
            return None
        
        total_expenses = sum(abs(float(t.amount)) for t in all_expenses)
        avg_weekly = total_expenses / 13  # ~13 недель в 90 днях
        
        if avg_weekly == 0:
            return None
        
        change_percent = ((last_week_total - avg_weekly) / avg_weekly * 100)
        
        if abs(change_percent) < 10:
            return {
                "type": "success",
                "title": "Стабильные расходы",
                "message": f"Ваши расходы остаются стабильными: {last_week_total:.2f} ₽ на этой неделе",
                "icon": "📈",
                "value": last_week_total,
                "details": {
                    "current_week": last_week_total,
                    "average_week": avg_weekly,
                    "change_percent": change_percent
                }
            }
        elif change_percent > 50:
            return {
                "type": "alert",
                "title": "Резкий рост расходов!",
                "message": f"Расходы выросли на {change_percent:.1f}% по сравнению со средними",
                "icon": "⚠️",
                "value": last_week_total - avg_weekly,
                "details": {
                    "current_week": last_week_total,
                    "average_week": avg_weekly,
                    "change_percent": change_percent
                }
            }
        elif change_percent < -30:
            return {
                "type": "success",
                "title": "Отличная экономия!",
                "message": f"Расходы снизились на {abs(change_percent):.1f}% - так держать!",
                "icon": "🎉",
                "value": avg_weekly - last_week_total,
                "details": {
                    "current_week": last_week_total,
                    "average_week": avg_weekly,
                    "change_percent": change_percent
                }
            }
        
        return None
    
    @staticmethod
    def _analyze_savings_potential(transactions: List[Transaction]) -> Dict[str, Any]:
        """Анализирует потенциал сбережений."""
        # Доходы и расходы за последние 3 месяца
        total_income = sum(float(t.amount) for t in transactions if t.amount > 0)
        total_expenses = sum(abs(float(t.amount)) for t in transactions if t.amount < 0)
        
        if total_income == 0:
            return None
        
        # Средние месячные значения
        monthly_income = total_income / 3
        monthly_expenses = total_expenses / 3
        current_savings = monthly_income - monthly_expenses
        
        if current_savings <= 0:
            return {
                "type": "alert",
                "title": "Расходы превышают доходы",
                "message": f"Дефицит: {abs(current_savings):.2f} ₽/месяц. Рекомендуем пересмотреть бюджет",
                "icon": "🚨",
                "value": current_savings,
                "details": {
                    "monthly_income": monthly_income,
                    "monthly_expenses": monthly_expenses,
                    "deficit": abs(current_savings)
                }
            }
        
        savings_rate = (current_savings / monthly_income * 100)
        
        if savings_rate < 10:
            return {
                "type": "warning",
                "title": "Низкий уровень сбережений",
                "message": f"Сберегаете {savings_rate:.1f}% дохода. Рекомендуемый минимум: 20%",
                "icon": "💡",
                "value": current_savings,
                "details": {
                    "monthly_income": monthly_income,
                    "monthly_expenses": monthly_expenses,
                    "current_savings": current_savings,
                    "savings_rate": savings_rate,
                    "recommended_savings": monthly_income * 0.2
                }
            }
        elif savings_rate >= 20:
            return {
                "type": "success",
                "title": "Отличный уровень сбережений!",
                "message": f"Сберегаете {savings_rate:.1f}% дохода ({current_savings:.2f} ₽/месяц)",
                "icon": "💎",
                "value": current_savings,
                "details": {
                    "monthly_income": monthly_income,
                    "monthly_expenses": monthly_expenses,
                    "current_savings": current_savings,
                    "savings_rate": savings_rate
                }
            }
        else:
            return {
                "type": "info",
                "title": "Хороший уровень сбережений",
                "message": f"Сберегаете {savings_rate:.1f}% дохода. До цели 20%: {(monthly_income * 0.2 - current_savings):.2f} ₽",
                "icon": "💰",
                "value": current_savings,
                "details": {
                    "monthly_income": monthly_income,
                    "monthly_expenses": monthly_expenses,
                    "current_savings": current_savings,
                    "savings_rate": savings_rate,
                    "target_savings": monthly_income * 0.2
                }
            }
    
    @staticmethod
    def _detect_unusual_activity(transactions: List[Transaction]) -> Dict[str, Any]:
        """Обнаруживает необычную активность."""
        # Проверяем крупные транзакции за последние 7 дней
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_transactions = [t for t in transactions if t.created_at >= week_ago]
        
        if not recent_transactions:
            return None
        
        # Средний размер транзакции за 90 дней
        all_amounts = [abs(float(t.amount)) for t in transactions]
        avg_amount = sum(all_amounts) / len(all_amounts) if all_amounts else 0
        
        # Ищем транзакции > 3x среднего
        large_transactions = [t for t in recent_transactions if abs(float(t.amount)) > avg_amount * 3]
        
        if large_transactions:
            largest = max(large_transactions, key=lambda t: abs(float(t.amount)))
            category_name = largest.category.name if largest.category else "Другое"

            return {
                "type": "warning",
                "title": "Крупная транзакция обнаружена",
                "message": f"{abs(float(largest.amount)):.2f} ₽ - в {abs(float(largest.amount)) / avg_amount:.1f}x раз больше обычной",
                "icon": "🔍",
                "value": abs(float(largest.amount)),
                "details": {
                    "amount": abs(float(largest.amount)),
                    "category": category_name,
                    "date": largest.created_at.strftime("%d.%m.%Y"),
                    "times_larger": abs(float(largest.amount)) / avg_amount
                }
            }
        
        return None
    
    @staticmethod
    def _generate_optimization_tip(transactions: List[Transaction]) -> Dict[str, Any]:
        """Генерирует рекомендацию по оптимизации."""
        # Анализируем регулярные мелкие расходы (кофе, такси и т.д.)
        small_frequent_categories = defaultdict(int)
        
        for t in transactions:
            if t.amount < 0 and abs(float(t.amount)) < 1000:  # Мелкие расходы
                category = t.category.name if t.category else "Другое"
                small_frequent_categories[category] += 1
        
        if not small_frequent_categories:
            return None
        
        # Находим самую частую категорию
        top_category = max(small_frequent_categories, key=small_frequent_categories.get)
        count = small_frequent_categories[top_category]
        
        if count >= 20:  # Более 20 транзакций за 90 дней
            # Подсчитываем общую сумму
            total = sum(abs(float(t.amount)) for t in transactions 
                       if t.amount < 0 and (t.category.name if t.category else "Другое") == top_category)
            
            potential_savings = total * 0.3  # 30% потенциальной экономии
            
            return {
                "type": "info",
                "title": f"Оптимизируйте расходы: {top_category}",
                "message": f"{count} транзакций на сумму {total:.2f} ₽. Экономия 30% = {potential_savings:.2f} ₽",
                "icon": "💡",
                "value": potential_savings,
                "details": {
                    "category": top_category,
                    "transaction_count": count,
                    "total_spent": total,
                    "potential_savings": potential_savings
                }
            }
        
        return None
    
    @staticmethod
    def get_financial_health_score(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Рассчитывает финансовое здоровье пользователя (0-100).
        
        Учитывает:
        - Уровень сбережений (40%)
        - Стабильность расходов (30%)
        - Разнообразие доходов (20%)
        - Отсутствие долгов (10%)
        """
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        user_accounts = db.query(Account).join(BankConnection).filter(
            BankConnection.user_id == user_id
        ).all()
        
        account_ids = [acc.id for acc in user_accounts]
        
        if not account_ids:
            return {
                "score": 0,
                "grade": "N/A",
                "message": "Недостаточно данных для оценки"
            }
        
        transactions = db.query(Transaction).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.created_at >= ninety_days_ago
        ).all()
        
        if not transactions:
            return {
                "score": 0,
                "grade": "N/A",
                "message": "Недостаточно данных для оценки"
            }
        
        score = 0
        
        # 1. Уровень сбережений (40 баллов)
        total_income = sum(float(t.amount) for t in transactions if t.amount > 0)
        total_expenses = sum(abs(float(t.amount)) for t in transactions if t.amount < 0)
        
        if total_income > 0:
            savings_rate = ((total_income - total_expenses) / total_income)
            if savings_rate >= 0.3:
                score += 40
            elif savings_rate >= 0.2:
                score += 30
            elif savings_rate >= 0.1:
                score += 20
            elif savings_rate >= 0:
                score += 10
        
        # 2. Стабильность расходов (30 баллов)
        monthly_expenses = []
        for month_offset in range(3):
            month_start = datetime.utcnow() - timedelta(days=30 * (month_offset + 1))
            month_end = datetime.utcnow() - timedelta(days=30 * month_offset)
            month_trans = [t for t in transactions if month_start <= t.created_at < month_end and t.amount < 0]
            monthly_expenses.append(sum(abs(float(t.amount)) for t in month_trans))
        
        if monthly_expenses and max(monthly_expenses) > 0:
            variation = (max(monthly_expenses) - min(monthly_expenses)) / max(monthly_expenses)
            if variation < 0.2:
                score += 30
            elif variation < 0.4:
                score += 20
            elif variation < 0.6:
                score += 10
        
        # 3. Баланс счетов (30 баллов)
        total_balance = sum(float(acc.balance) for acc in user_accounts)
        monthly_expenses_avg = sum(monthly_expenses) / len(monthly_expenses) if monthly_expenses else 0
        
        if monthly_expenses_avg > 0:
            months_of_runway = total_balance / monthly_expenses_avg
            if months_of_runway >= 6:
                score += 30
            elif months_of_runway >= 3:
                score += 20
            elif months_of_runway >= 1:
                score += 10
        
        # Определяем оценку
        if score >= 90:
            grade = "A+"
            message = "Отличное финансовое здоровье!"
        elif score >= 80:
            grade = "A"
            message = "Очень хорошее управление финансами"
        elif score >= 70:
            grade = "B"
            message = "Хорошее финансовое состояние"
        elif score >= 60:
            grade = "C"
            message = "Удовлетворительно, есть что улучшить"
        else:
            grade = "D"
            message = "Требуется работа над бюджетом"
        
        return {
            "score": score,
            "grade": grade,
            "message": message,
            "details": {
                "savings_rate": ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0,
                "expense_stability": (1 - variation) * 100 if 'variation' in locals() else 0,
                "months_of_runway": months_of_runway if 'months_of_runway' in locals() else 0
            }
        }



