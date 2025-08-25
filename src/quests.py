"""
Quests module for IndiePilot
Handles life skills quests, XP tracking, and completion status
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from .db import safe_query, safe_execute
from .utils import generate_id

class QuestManager:
    """Manages life skills quests and user progress"""
    
    def __init__(self):
        self.difficulty_names = {
            1: "Beginner",
            2: "Intermediate", 
            3: "Advanced"
        }
    
    def get_all_quests(self) -> List[Dict[str, Any]]:
        """Get all available quests"""
        quests = safe_query("""
            SELECT id, title, description, difficulty, xp, est_minutes, materials
            FROM quest
            ORDER BY difficulty, title
        """)
        
        # Add difficulty name
        for quest in quests:
            quest['difficulty_name'] = self.difficulty_names.get(quest['difficulty'], 'Unknown')
        
        return quests
    
    def get_quest_by_id(self, quest_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific quest by ID"""
        quests = safe_query("""
            SELECT id, title, description, difficulty, xp, est_minutes, materials
            FROM quest
            WHERE id = ?
        """, (quest_id,))
        
        if not quests:
            return None
        
        quest = quests[0]
        quest['difficulty_name'] = self.difficulty_names.get(quest['difficulty'], 'Unknown')
        return quest
    
    def start_quest(self, user_id: str, quest_id: str) -> bool:
        """Start a quest for a user"""
        # Check if quest exists
        quest = self.get_quest_by_id(quest_id)
        if not quest:
            return False
        
        # Check if already started
        existing = safe_query("""
            SELECT id FROM quest_progress
            WHERE user_id = ? AND quest_id = ?
        """, (user_id, quest_id))
        
        if existing:
            return False  # Already started
        
        # Start the quest
        safe_execute("""
            INSERT INTO quest_progress (id, user_id, quest_id, started_at)
            VALUES (?, ?, ?, ?)
        """, (generate_id(), user_id, quest_id, datetime.now().isoformat()))
        
        return True
    
    def complete_quest(self, user_id: str, quest_id: str) -> bool:
        """Complete a quest for a user"""
        # Check if quest exists and is started
        progress = safe_query("""
            SELECT id, completed_at FROM quest_progress
            WHERE user_id = ? AND quest_id = ?
        """, (user_id, quest_id))
        
        if not progress:
            return False  # Not started
        
        if progress[0]['completed_at']:
            return False  # Already completed
        
        # Mark as completed
        safe_execute("""
            UPDATE quest_progress
            SET completed_at = ?
            WHERE user_id = ? AND quest_id = ?
        """, (datetime.now().isoformat(), user_id, quest_id))
        
        return True
    
    def is_quest_completed(self, user_id: str, quest_id: str) -> bool:
        """Check if a quest is completed by the user"""
        result = safe_query("""
            SELECT completed_at FROM quest_progress
            WHERE user_id = ? AND quest_id = ?
        """, (user_id, quest_id))
        
        return bool(result and result[0]['completed_at'])
    
    def is_quest_started(self, user_id: str, quest_id: str) -> bool:
        """Check if a quest is started by the user"""
        result = safe_query("""
            SELECT id FROM quest_progress
            WHERE user_id = ? AND quest_id = ?
        """, (user_id, quest_id))
        
        return bool(result)
    
    def get_completed_quests(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all completed quests for a user"""
        completed = safe_query("""
            SELECT 
                q.id, q.title, q.description, q.difficulty, q.xp, q.est_minutes,
                qp.completed_at
            FROM quest_progress qp
            JOIN quest q ON qp.quest_id = q.id
            WHERE qp.user_id = ? AND qp.completed_at IS NOT NULL
            ORDER BY qp.completed_at DESC
        """, (user_id,))
        
        # Add difficulty name
        for quest in completed:
            quest['difficulty_name'] = self.difficulty_names.get(quest['difficulty'], 'Unknown')
        
        return completed
    
    def get_started_quests(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all started but not completed quests for a user"""
        started = safe_query("""
            SELECT 
                q.id, q.title, q.description, q.difficulty, q.xp, q.est_minutes,
                qp.started_at
            FROM quest_progress qp
            JOIN quest q ON qp.quest_id = q.id
            WHERE qp.user_id = ? AND qp.completed_at IS NULL
            ORDER BY qp.started_at DESC
        """, (user_id,))
        
        # Add difficulty name
        for quest in started:
            quest['difficulty_name'] = self.difficulty_names.get(quest['difficulty'], 'Unknown')
        
        return started
    
    def get_quest_progress(self, user_id: str) -> Dict[str, Any]:
        """Get overall quest progress for a user"""
        total_quests = safe_query("SELECT COUNT(*) as count FROM quest")
        total_quests = total_quests[0]['count'] if total_quests else 0
        
        completed_quests = safe_query("""
            SELECT COUNT(*) as count
            FROM quest_progress
            WHERE user_id = ? AND completed_at IS NOT NULL
        """, (user_id,))
        completed_quests = completed_quests[0]['count'] if completed_quests else 0
        
        started_quests = safe_query("""
            SELECT COUNT(*) as count
            FROM quest_progress
            WHERE user_id = ?
        """, (user_id,))
        started_quests = started_quests[0]['count'] if started_quests else 0
        
        total_xp = safe_query("""
            SELECT COALESCE(SUM(q.xp), 0) as total_xp
            FROM quest_progress qp
            JOIN quest q ON qp.quest_id = q.id
            WHERE qp.user_id = ? AND qp.completed_at IS NOT NULL
        """, (user_id,))
        total_xp = total_xp[0]['total_xp'] if total_xp else 0
        
        return {
            'total_quests': total_quests,
            'completed_quests': completed_quests,
            'started_quests': started_quests,
            'total_xp': total_xp,
            'completion_rate': (completed_quests / total_quests * 100) if total_quests > 0 else 0
        }
    
    def get_quests_by_difficulty(self, user_id: str, difficulty: int) -> List[Dict[str, Any]]:
        """Get quests by difficulty level with completion status"""
        quests = safe_query("""
            SELECT 
                q.id, q.title, q.description, q.difficulty, q.xp, q.est_minutes,
                qp.started_at, qp.completed_at
            FROM quest q
            LEFT JOIN quest_progress qp ON q.id = qp.quest_id AND qp.user_id = ?
            WHERE q.difficulty = ?
            ORDER BY q.title
        """, (user_id, difficulty))
        
        # Add difficulty name and status
        for quest in quests:
            quest['difficulty_name'] = self.difficulty_names.get(quest['difficulty'], 'Unknown')
            quest['status'] = 'completed' if quest['completed_at'] else 'started' if quest['started_at'] else 'not_started'
        
        return quests
    
    def get_recent_completions(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent quest completions"""
        recent = safe_query("""
            SELECT 
                q.title, q.xp, qp.completed_at
            FROM quest_progress qp
            JOIN quest q ON qp.quest_id = q.id
            WHERE qp.user_id = ? AND qp.completed_at IS NOT NULL
            ORDER BY qp.completed_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        return recent
    
    def get_quest_recommendations(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get quest recommendations based on user's current level"""
        # Get user's completed quests and their difficulties
        completed = safe_query("""
            SELECT q.difficulty
            FROM quest_progress qp
            JOIN quest q ON qp.quest_id = q.id
            WHERE qp.user_id = ? AND qp.completed_at IS NOT NULL
        """, (user_id,))
        
        if not completed:
            # New user - recommend beginner quests
            return self.get_quests_by_difficulty(user_id, 1)[:limit]
        
        # Calculate average difficulty of completed quests
        avg_difficulty = sum(q['difficulty'] for q in completed) / len(completed)
        
        # Recommend quests at or slightly above current level
        target_difficulty = min(3, max(1, round(avg_difficulty + 0.5)))
        
        # Get quests at target difficulty that aren't completed
        recommendations = safe_query("""
            SELECT 
                q.id, q.title, q.description, q.difficulty, q.xp, q.est_minutes
            FROM quest q
            LEFT JOIN quest_progress qp ON q.id = qp.quest_id AND qp.user_id = ?
            WHERE q.difficulty = ? AND (qp.completed_at IS NULL OR qp.completed_at IS NULL)
            ORDER BY q.xp DESC
            LIMIT ?
        """, (user_id, target_difficulty, limit))
        
        # Add difficulty name
        for quest in recommendations:
            quest['difficulty_name'] = self.difficulty_names.get(quest['difficulty'], 'Unknown')
        
        return recommendations
    
    def get_skills_score(self, user_id: str) -> float:
        """Calculate skills score based on completed quests (0-100)"""
        completed = safe_query("""
            SELECT COALESCE(SUM(q.xp), 0) as total_xp
            FROM quest_progress qp
            JOIN quest q ON qp.quest_id = q.id
            WHERE qp.user_id = ? AND qp.completed_at IS NOT NULL
        """, (user_id,))
        
        total_xp = completed[0]['total_xp'] if completed else 0
        
        # Scale XP to 0-100 score (adjust multiplier as needed)
        # Assuming average quest gives 60 XP, 10 quests = 600 XP = 100 score
        score = min(100, total_xp / 6)
        
        return score 