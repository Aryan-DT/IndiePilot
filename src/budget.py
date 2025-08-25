"""
Budget module for IndiePilot
Handles three-jar budgeting system, streaks, badges, and financial tracking
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .db import safe_query, safe_execute, get_user_settings, update_user_settings
from .utils import generate_id

class BudgetManager:
    """Manages the three-jar budgeting system"""
    
    def __init__(self):
        self.badges = {
            'first_log': {'name': 'First Steps', 'description': 'Logged your first transaction'},
            'week_streak': {'name': 'Week Warrior', 'description': '7-day logging streak'},
            'month_streak': {'name': 'Monthly Master', 'description': '30-day logging streak'},
            'save_milestone': {'name': 'Saver', 'description': 'Saved $100 total'},
            'share_milestone': {'name': 'Giver', 'description': 'Shared $50 total'}
        }
    
    def add_income(self, user_id: str, amount: float, note: str) -> bool:
        """Add income and distribute to jars based on user settings"""
        settings = get_user_settings(user_id)
        
        # Calculate jar allocations
        spend_amount = amount * (settings['spend_ratio'] / 100)
        save_amount = amount * (settings['save_ratio'] / 100)
        share_amount = amount * (settings['share_ratio'] / 100)
        
        # Add to spend jar
        safe_execute("""
            INSERT INTO budget_log (id, user_id, amount, jar, note)
            VALUES (?, ?, ?, 'spend', ?)
        """, (generate_id(), user_id, spend_amount, f"Income: {note}"))
        
        # Add to save jar
        safe_execute("""
            INSERT INTO budget_log (id, user_id, amount, jar, note)
            VALUES (?, ?, ?, 'save', ?)
        """, (generate_id(), user_id, save_amount, f"Income: {note}"))
        
        # Add to share jar
        safe_execute("""
            INSERT INTO budget_log (id, user_id, amount, jar, note)
            VALUES (?, ?, ?, 'share', ?)
        """, (generate_id(), user_id, share_amount, f"Income: {note}"))
        
        return True
    
    def add_expense(self, user_id: str, amount: float, jar: str, note: str) -> bool:
        """Add an expense to a specific jar"""
        if jar not in ['spend', 'save', 'share']:
            return False
        
        # Check if user has enough in the jar
        jar_balance = self.get_jar_balance(user_id, jar)
        if jar_balance < amount:
            return False  # Insufficient funds
        
        safe_execute("""
            INSERT INTO budget_log (id, user_id, amount, jar, note)
            VALUES (?, ?, ?, ?, ?)
        """, (generate_id(), user_id, -amount, jar, note))
        
        return True
    
    def get_budget_overview(self, user_id: str) -> Dict[str, float]:
        """Get current balance for each jar"""
        spend_balance = self.get_jar_balance(user_id, 'spend')
        save_balance = self.get_jar_balance(user_id, 'save')
        share_balance = self.get_jar_balance(user_id, 'share')
        
        return {
            'spend': spend_balance,
            'save': save_balance,
            'share': share_balance,
            'total': spend_balance + save_balance + share_balance
        }
    
    def get_jar_balance(self, user_id: str, jar: str) -> float:
        """Get current balance for a specific jar"""
        result = safe_query("""
            SELECT COALESCE(SUM(amount), 0) as balance
            FROM budget_log
            WHERE user_id = ? AND jar = ?
        """, (user_id, jar))
        
        return float(result[0]['balance']) if result else 0.0
    
    def get_recent_transactions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions for the user"""
        return safe_query("""
            SELECT ts, amount, jar, note
            FROM budget_log
            WHERE user_id = ?
            ORDER BY ts DESC
            LIMIT ?
        """, (user_id, limit))
    
    def get_current_streak(self, user_id: str) -> int:
        """Calculate current logging streak in days"""
        # Get all unique dates with transactions
        dates = safe_query("""
            SELECT DISTINCT DATE(ts) as log_date
            FROM budget_log
            WHERE user_id = ?
            ORDER BY log_date DESC
        """, (user_id,))
        
        if not dates:
            return 0
        
        # Convert to date objects
        log_dates = [datetime.strptime(row['log_date'], '%Y-%m-%d').date() for row in dates]
        
        # Calculate streak
        streak = 0
        current_date = datetime.now().date()
        
        for i, log_date in enumerate(log_dates):
            if i == 0:
                # Check if first log is today or yesterday
                if log_date == current_date or log_date == current_date - timedelta(days=1):
                    streak = 1
                else:
                    break
            else:
                # Check if consecutive
                expected_date = current_date - timedelta(days=i)
                if log_date == expected_date:
                    streak += 1
                else:
                    break
        
        return streak
    
    def get_user_badges(self, user_id: str) -> List[Dict[str, str]]:
        """Get badges earned by the user"""
        earned_badges = []
        
        # Check first log badge
        first_log = safe_query("""
            SELECT COUNT(*) as count
            FROM budget_log
            WHERE user_id = ?
        """, (user_id,))
        
        if first_log[0]['count'] > 0:
            earned_badges.append(self.badges['first_log'])
        
        # Check streak badges
        streak = self.get_current_streak(user_id)
        if streak >= 7:
            earned_badges.append(self.badges['week_streak'])
        if streak >= 30:
            earned_badges.append(self.badges['month_streak'])
        
        # Check save milestone
        total_saved = self.get_jar_balance(user_id, 'save')
        if total_saved >= 100:
            earned_badges.append(self.badges['save_milestone'])
        
        # Check share milestone
        total_shared = self.get_jar_balance(user_id, 'share')
        if total_shared >= 50:
            earned_badges.append(self.badges['share_milestone'])
        
        return earned_badges
    
    def update_ratios(self, user_id: str, spend_ratio: float, save_ratio: float, share_ratio: float) -> bool:
        """Update budget allocation ratios"""
        return update_user_settings(
            user_id, 
            spend_ratio=spend_ratio,
            save_ratio=save_ratio,
            share_ratio=share_ratio
        )
    
    def get_weekly_spending(self, user_id: str, weeks: int = 4) -> List[Dict[str, Any]]:
        """Get weekly spending data for charts"""
        weekly_data = []
        
        for i in range(weeks):
            week_start = datetime.now() - timedelta(weeks=i+1)
            week_end = datetime.now() - timedelta(weeks=i)
            
            result = safe_query("""
                SELECT 
                    jar,
                    COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) as income,
                    COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as expenses
                FROM budget_log
                WHERE user_id = ? 
                AND ts >= ? 
                AND ts < ?
                GROUP BY jar
            """, (user_id, week_start.isoformat(), week_end.isoformat()))
            
            week_data = {
                'week': f"Week {weeks-i}",
                'spend_income': 0,
                'spend_expenses': 0,
                'save_income': 0,
                'save_expenses': 0,
                'share_income': 0,
                'share_expenses': 0
            }
            
            for row in result:
                jar = row['jar']
                week_data[f'{jar}_income'] = float(row['income'])
                week_data[f'{jar}_expenses'] = float(row['expenses'])
            
            weekly_data.append(week_data)
        
        return weekly_data
    
    def get_spending_breakdown(self, user_id: str, days: int = 30) -> Dict[str, float]:
        """Get spending breakdown by category for the last N days"""
        since_date = datetime.now() - timedelta(days=days)
        
        result = safe_query("""
            SELECT 
                jar,
                COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as total_spent
            FROM budget_log
            WHERE user_id = ? 
            AND ts >= ?
            AND amount < 0
            GROUP BY jar
        """, (user_id, since_date.isoformat()))
        
        breakdown = {'spend': 0.0, 'save': 0.0, 'share': 0.0}
        
        for row in result:
            breakdown[row['jar']] = float(row['total_spent'])
        
        return breakdown
    
    def get_financial_health_score(self, user_id: str) -> float:
        """Calculate financial health score (0-100)"""
        overview = self.get_budget_overview(user_id)
        streak = self.get_current_streak(user_id)
        
        # Base score from savings ratio
        total = overview['total']
        if total == 0:
            return 0.0
        
        savings_ratio = overview['save'] / total
        savings_score = min(100, savings_ratio * 200)  # 50% savings = 100 points
        
        # Streak bonus (up to 20 points)
        streak_bonus = min(20, streak * 2)
        
        # Spending control bonus (up to 30 points)
        spend_ratio = overview['spend'] / total if total > 0 else 1
        spending_score = max(0, 30 - (spend_ratio * 30))
        
        total_score = savings_score + streak_bonus + spending_score
        return min(100, total_score) 