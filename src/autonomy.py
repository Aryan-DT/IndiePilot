"""
Autonomy module for IndiePilot
Handles Autonomy Index calculation and radar chart generation
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
import numpy as np
from typing import Dict, List, Any
from .db import safe_query, get_user_settings, update_user_settings
from .budget import BudgetManager
from .quests import QuestManager
from .board import BoardManager
from .sim import SimManager

class AutonomyIndex:
    """Manages Autonomy Index calculation and visualization"""
    
    def __init__(self):
        self.budget_manager = BudgetManager()
        self.quest_manager = QuestManager()
        self.board_manager = BoardManager()
        self.sim_manager = SimManager()
        
        # Default weights for Autonomy Index calculation
        self.default_weights = {
            'skills': 0.30,
            'budgeting': 0.30,
            'community': 0.15,
            'judgment': 0.25
        }
    
    def compute_autonomy_index(self, user_id: str) -> float:
        """
        Compute the Autonomy Index (0-100) based on weighted scores from four areas:
        
        Skills = min(100, completed_quests * 10)
        Budgeting = 100 - overspend_penalty + logging_streak_bonus
        Community = min(100, posts_created*5 + posts_claimed*10)
        Judgment = avg(last_5_sim_scores, default 50 if none)
        
        Returns weighted sum of all four scores.
        """
        # Get user settings for weights
        settings = get_user_settings(user_id)
        weights = {
            'skills': settings['skills_weight'],
            'budgeting': settings['budgeting_weight'],
            'community': settings['community_weight'],
            'judgment': settings['judgment_weight']
        }
        
        # Calculate individual scores
        skills_score = self._calculate_skills_score(user_id)
        budgeting_score = self._calculate_budgeting_score(user_id)
        community_score = self._calculate_community_score(user_id)
        judgment_score = self._calculate_judgment_score(user_id)
        
        # Calculate weighted sum
        autonomy_index = (
            skills_score * weights['skills'] +
            budgeting_score * weights['budgeting'] +
            community_score * weights['community'] +
            judgment_score * weights['judgment']
        )
        
        return round(autonomy_index, 1)
    
    def _calculate_skills_score(self, user_id: str) -> float:
        """Calculate skills score based on completed quests (0-100)"""
        completed_quests = safe_query("""
            SELECT COUNT(*) as count
            FROM quest_progress
            WHERE user_id = ? AND completed_at IS NOT NULL
        """, (user_id,))
        
        count = completed_quests[0]['count'] if completed_quests else 0
        return min(100, count * 10)
    
    def _calculate_budgeting_score(self, user_id: str) -> float:
        """Calculate budgeting score (0-100)"""
        # Get financial health score from budget manager
        base_score = self.budget_manager.get_financial_health_score(user_id)
        
        # Get current streak for bonus
        streak = self.budget_manager.get_current_streak(user_id)
        streak_bonus = min(20, streak * 2)  # Up to 20 points for streaks
        
        # Check for overspending penalty
        overview = self.budget_manager.get_budget_overview(user_id)
        total = overview['total']
        
        if total > 0:
            spend_ratio = overview['spend'] / total
            overspend_penalty = max(0, (spend_ratio - 0.7) * 100)  # Penalty if spending > 70%
        else:
            overspend_penalty = 0
        
        final_score = base_score + streak_bonus - overspend_penalty
        return max(0, min(100, final_score))
    
    def _calculate_community_score(self, user_id: str) -> float:
        """Calculate community score based on board activity (0-100)"""
        # Posts created (5 points each, max 50)
        posts_created = safe_query("""
            SELECT COUNT(*) as count FROM board_post WHERE user_id = ?
        """, (user_id,))
        posts_score = min(50, (posts_created[0]['count'] if posts_created else 0) * 5)
        
        # Posts claimed (10 points each, max 50)
        posts_claimed = safe_query("""
            SELECT COUNT(*) as count FROM board_claim WHERE user_id = ?
        """, (user_id,))
        claims_score = min(50, (posts_claimed[0]['count'] if posts_claimed else 0) * 10)
        
        total_score = posts_score + claims_score
        return min(100, total_score)
    
    def _calculate_judgment_score(self, user_id: str) -> float:
        """Calculate judgment score based on simulation performance (0-100)"""
        # Get last 5 simulation scores
        recent_runs = safe_query("""
            SELECT score FROM sim_run
            WHERE user_id = ?
            ORDER BY ran_at DESC
            LIMIT 5
        """, (user_id,))
        
        if not recent_runs:
            return 50.0  # Default score if no runs
        
        scores = [run['score'] for run in recent_runs]
        avg_score = sum(scores) / len(scores)
        
        return avg_score
    
    def get_individual_scores(self, user_id: str) -> Dict[str, float]:
        """Get individual scores for all four areas"""
        return {
            'skills': self._calculate_skills_score(user_id),
            'budgeting': self._calculate_budgeting_score(user_id),
            'community': self._calculate_community_score(user_id),
            'judgment': self._calculate_judgment_score(user_id)
        }
    
    def plot_radar(self, user_id: str):
        """Create a radar chart showing the four autonomy areas"""
        # Get individual scores
        scores = self.get_individual_scores(user_id)
        
        # Categories for the radar chart
        categories = ['Skills', 'Budgeting', 'Community', 'Judgment']
        values = [scores['skills'], scores['budgeting'], scores['community'], scores['judgment']]
        
        # Number of variables
        N = len(categories)
        
        # Create the angle for each axis
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Complete the circle
        
        # Add the first value to the end to close the plot
        values += values[:1]
        
        # Create the figure
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        
        # Plot the data
        ax.plot(angles, values, 'o-', linewidth=2, color='#1f77b4', label='Your Score')
        ax.fill(angles, values, alpha=0.25, color='#1f77b4')
        
        # Set the labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=12, fontweight='bold')
        
        # Set the y-axis limits
        ax.set_ylim(0, 100)
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Add value labels
        for i, (angle, value) in enumerate(zip(angles[:-1], values[:-1])):
            ax.text(angle, value + 5, f'{value:.0f}', 
                   ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Add title
        plt.title('Your Independence Radar', fontsize=16, fontweight='bold', pad=20)
        
        # Add legend
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        return fig
    
    def update_weights(self, skills_weight: float, budgeting_weight: float, 
                      community_weight: float, judgment_weight: float) -> bool:
        """Update the weights for Autonomy Index calculation"""
        # Validate that weights sum to 1.0
        total_weight = skills_weight + budgeting_weight + community_weight + judgment_weight
        if abs(total_weight - 1.0) > 0.01:
            return False
        
        # Update weights for all users (in a real app, you might want per-user weights)
        # For demo purposes, we'll update the default weights
        self.default_weights = {
            'skills': skills_weight,
            'budgeting': budgeting_weight,
            'community': community_weight,
            'judgment': judgment_weight
        }
        
        return True
    
    def get_autonomy_trend(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get autonomy index trend over time (simplified for demo)"""
        # In a real app, you'd store historical autonomy scores
        # For demo, we'll return a simple trend based on recent activity
        
        current_score = self.compute_autonomy_index(user_id)
        
        # Generate a simple trend (in real app, this would be actual historical data)
        trend = []
        for i in range(days, 0, -1):
            # Simulate some variation in the score
            variation = np.random.normal(0, 2)  # Small random variation
            trend_score = max(0, min(100, current_score + variation))
            
            trend.append({
                'date': f"Day {i}",
                'score': round(trend_score, 1)
            })
        
        return trend
    
    def get_autonomy_insights(self, user_id: str) -> List[str]:
        """Get personalized insights based on autonomy scores"""
        scores = self.get_individual_scores(user_id)
        insights = []
        
        # Skills insights
        if scores['skills'] < 30:
            insights.append("💡 Try completing some beginner quests to build your life skills foundation!")
        elif scores['skills'] < 70:
            insights.append("🎯 Great progress on skills! Consider tackling some intermediate quests.")
        else:
            insights.append("🏆 Excellent skills development! You're ready for advanced challenges.")
        
        # Budgeting insights
        if scores['budgeting'] < 40:
            insights.append("💰 Start logging your expenses regularly to improve your financial awareness.")
        elif scores['budgeting'] < 80:
            insights.append("📊 Good budgeting habits! Try to increase your savings ratio.")
        else:
            insights.append("💎 Outstanding financial management! You're building great money habits.")
        
        # Community insights
        if scores['community'] < 20:
            insights.append("🤝 Connect with others on the Youth Board to build your community score.")
        elif scores['community'] < 60:
            insights.append("👥 Nice community engagement! Try both creating and responding to posts.")
        else:
            insights.append("🌟 Excellent community participation! You're a great team player.")
        
        # Judgment insights
        if scores['judgment'] < 50:
            insights.append("🎯 Practice decision-making with IndieSim scenarios to improve your judgment.")
        elif scores['judgment'] < 80:
            insights.append("🧠 Good judgment skills! Keep practicing different scenarios.")
        else:
            insights.append("🧠 Outstanding decision-making! You show excellent judgment in complex situations.")
        
        return insights
    
    def get_next_milestones(self, user_id: str) -> List[Dict[str, Any]]:
        """Get next milestones for the user to achieve"""
        scores = self.get_individual_scores(user_id)
        milestones = []
        
        # Skills milestones
        current_quests = safe_query("""
            SELECT COUNT(*) as count
            FROM quest_progress
            WHERE user_id = ? AND completed_at IS NOT NULL
        """, (user_id,))
        quest_count = current_quests[0]['count'] if current_quests else 0
        
        next_quest_milestone = ((quest_count // 5) + 1) * 5
        if next_quest_milestone <= 20:  # Cap at 20 quests
            milestones.append({
                'area': 'Skills',
                'milestone': f'Complete {next_quest_milestone} quests',
                'current': quest_count,
                'target': next_quest_milestone,
                'reward': f'+{next_quest_milestone * 2} XP'
            })
        
        # Budgeting milestones
        streak = self.budget_manager.get_current_streak(user_id)
        next_streak_milestone = ((streak // 7) + 1) * 7
        if next_streak_milestone <= 30:  # Cap at 30 days
            milestones.append({
                'area': 'Budgeting',
                'milestone': f'{next_streak_milestone}-day logging streak',
                'current': streak,
                'target': next_streak_milestone,
                'reward': '+15 Autonomy Points'
            })
        
        # Community milestones
        posts_created = safe_query("""
            SELECT COUNT(*) as count FROM board_post WHERE user_id = ?
        """, (user_id,))
        posts_count = posts_created[0]['count'] if posts_created else 0
        
        next_post_milestone = ((posts_count // 3) + 1) * 3
        if next_post_milestone <= 15:  # Cap at 15 posts
            milestones.append({
                'area': 'Community',
                'milestone': f'Create {next_post_milestone} board posts',
                'current': posts_count,
                'target': next_post_milestone,
                'reward': '+10 Community Points'
            })
        
        # Judgment milestones
        sim_runs = safe_query("""
            SELECT COUNT(*) as count FROM sim_run WHERE user_id = ?
        """, (user_id,))
        runs_count = sim_runs[0]['count'] if sim_runs else 0
        
        next_sim_milestone = ((runs_count // 2) + 1) * 2
        if next_sim_milestone <= 10:  # Cap at 10 runs
            milestones.append({
                'area': 'Judgment',
                'milestone': f'Complete {next_sim_milestone} IndieSim scenarios',
                'current': runs_count,
                'target': next_sim_milestone,
                'reward': '+20 Judgment Points'
            })
        
        return milestones 