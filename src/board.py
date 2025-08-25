"""
Board module for IndiePilot
Handles Youth Board posts, share codes, and privacy-first community features
"""

import random
import string
from datetime import datetime
from typing import Dict, List, Any, Optional
from .db import safe_query, safe_execute
from .utils import generate_id

class BoardManager:
    """Manages the Youth Board with privacy-first features"""
    
    def __init__(self):
        self.mock_contacts = [
            {
                'name': 'Alex Chen',
                'grade': '11th',
                'school': 'Local High School',
                'contact': 'alex.chen@student.local',
                'availability': 'Weekdays 3-6pm'
            },
            {
                'name': 'Jordan Smith',
                'grade': '12th', 
                'school': 'Local High School',
                'contact': 'jordan.smith@student.local',
                'availability': 'Weekends 10am-2pm'
            },
            {
                'name': 'Taylor Johnson',
                'grade': '10th',
                'school': 'Local High School', 
                'contact': 'taylor.johnson@student.local',
                'availability': 'After school daily'
            },
            {
                'name': 'Casey Williams',
                'grade': '11th',
                'school': 'Local High School',
                'contact': 'casey.williams@student.local', 
                'availability': 'Evenings 7-9pm'
            },
            {
                'name': 'Riley Brown',
                'grade': '12th',
                'school': 'Local High School',
                'contact': 'riley.brown@student.local',
                'availability': 'Flexible schedule'
            }
        ]
    
    def generate_share_code(self, kind: str) -> str:
        """Generate a unique share code for a post"""
        # Format: KIND-XXXX (e.g., STDY-A9F4)
        prefix = kind.upper()[:4]
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{prefix}-{suffix}"
    
    def create_post(self, kind: str, title: str, detail: str, user_id: str = None) -> str:
        """Create a new board post and return the share code"""
        if kind not in ['study', 'carpool', 'swap']:
            raise ValueError("Invalid post kind")
        
        # Generate unique share code
        share_code = self.generate_share_code(kind)
        
        # Ensure uniqueness
        while self._share_code_exists(share_code):
            share_code = self.generate_share_code(kind)
        
        # Create the post
        safe_execute("""
            INSERT INTO board_post (id, user_id, kind, title, detail, share_code)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (generate_id(), user_id or 'demo_user', kind, title, detail, share_code))
        
        return share_code
    
    def _share_code_exists(self, share_code: str) -> bool:
        """Check if a share code already exists"""
        result = safe_query("""
            SELECT id FROM board_post WHERE share_code = ?
        """, (share_code,))
        return bool(result)
    
    def get_posts(self, kind: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get board posts with optional filtering"""
        query = """
            SELECT id, user_id, kind, title, detail, share_code, created_at, status
            FROM board_post
        """
        params = []
        
        conditions = []
        if kind:
            conditions.append("kind = ?")
            params.append(kind)
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        posts = safe_query(query, tuple(params))
        
        # Format dates
        for post in posts:
            post['created_at'] = post['created_at'][:19]  # Remove microseconds
        
        return posts
    
    def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific post by ID"""
        posts = safe_query("""
            SELECT id, user_id, kind, title, detail, share_code, created_at, status
            FROM board_post
            WHERE id = ?
        """, (post_id,))
        
        if not posts:
            return None
        
        post = posts[0]
        post['created_at'] = post['created_at'][:19]
        return post
    
    def get_post_by_share_code(self, share_code: str) -> Optional[Dict[str, Any]]:
        """Get a post by share code"""
        posts = safe_query("""
            SELECT id, user_id, kind, title, detail, share_code, created_at, status
            FROM board_post
            WHERE share_code = ?
        """, (share_code,))
        
        if not posts:
            return None
        
        post = posts[0]
        post['created_at'] = post['created_at'][:19]
        return post
    
    def claim_post(self, post_id: str, user_id: str = None) -> Dict[str, Any]:
        """Claim a post and return mock contact information"""
        # Check if post exists and is available
        post = self.get_post_by_id(post_id)
        if not post or post['status'] != 'available':
            raise ValueError("Post not available for claiming")
        
        # Select a random mock contact
        mock_contact = random.choice(self.mock_contacts)
        
        # Create claim record
        safe_execute("""
            INSERT INTO board_claim (id, post_id, user_id, mock_contact)
            VALUES (?, ?, ?, ?)
        """, (generate_id(), post_id, user_id or 'demo_user', str(mock_contact)))
        
        # Update post status
        safe_execute("""
            UPDATE board_post SET status = 'claimed' WHERE id = ?
        """, (post_id,))
        
        return mock_contact
    
    def get_my_posts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get posts created by a specific user"""
        posts = safe_query("""
            SELECT id, kind, title, detail, share_code, created_at, status
            FROM board_post
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        
        # Format dates
        for post in posts:
            post['created_at'] = post['created_at'][:19]
        
        return posts
    
    def get_my_claims(self, user_id: str) -> List[Dict[str, Any]]:
        """Get posts claimed by a specific user"""
        claims = safe_query("""
            SELECT 
                bc.id, bc.claimed_at, bc.mock_contact,
                bp.kind, bp.title, bp.detail, bp.share_code
            FROM board_claim bc
            JOIN board_post bp ON bc.post_id = bp.id
            WHERE bc.user_id = ?
            ORDER BY bc.claimed_at DESC
        """, (user_id,))
        
        # Format dates
        for claim in claims:
            claim['claimed_at'] = claim['claimed_at'][:19]
        
        return claims
    
    def get_board_stats(self) -> Dict[str, int]:
        """Get board statistics"""
        total_posts = safe_query("SELECT COUNT(*) as count FROM board_post")
        total_posts = total_posts[0]['count'] if total_posts else 0
        
        available_posts = safe_query("""
            SELECT COUNT(*) as count FROM board_post WHERE status = 'available'
        """)
        available_posts = available_posts[0]['count'] if available_posts else 0
        
        claimed_posts = safe_query("""
            SELECT COUNT(*) as count FROM board_post WHERE status = 'claimed'
        """)
        claimed_posts = claimed_posts[0]['count'] if claimed_posts else 0
        
        study_posts = safe_query("""
            SELECT COUNT(*) as count FROM board_post WHERE kind = 'study'
        """)
        study_posts = study_posts[0]['count'] if study_posts else 0
        
        carpool_posts = safe_query("""
            SELECT COUNT(*) as count FROM board_post WHERE kind = 'carpool'
        """)
        carpool_posts = carpool_posts[0]['count'] if carpool_posts else 0
        
        swap_posts = safe_query("""
            SELECT COUNT(*) as count FROM board_post WHERE kind = 'swap'
        """)
        swap_posts = swap_posts[0]['count'] if swap_posts else 0
        
        return {
            'total_posts': total_posts,
            'available_posts': available_posts,
            'claimed_posts': claimed_posts,
            'study_posts': study_posts,
            'carpool_posts': carpool_posts,
            'swap_posts': swap_posts
        }
    
    def get_community_score(self, user_id: str) -> float:
        """Calculate community score based on posts and claims (0-100)"""
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
    
    def search_posts(self, query: str) -> List[Dict[str, Any]]:
        """Search posts by title or detail"""
        posts = safe_query("""
            SELECT id, user_id, kind, title, detail, share_code, created_at, status
            FROM board_post
            WHERE (title LIKE ? OR detail LIKE ?) AND status = 'available'
            ORDER BY created_at DESC
        """, (f'%{query}%', f'%{query}%'))
        
        # Format dates
        for post in posts:
            post['created_at'] = post['created_at'][:19]
        
        return posts
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent board activity"""
        # Combine recent posts and claims
        recent_posts = safe_query("""
            SELECT 
                'post' as type, id, kind, title, created_at, status
            FROM board_post
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        recent_claims = safe_query("""
            SELECT 
                'claim' as type, bc.id, bp.kind, bp.title, bc.claimed_at as created_at
            FROM board_claim bc
            JOIN board_post bp ON bc.post_id = bp.id
            ORDER BY bc.claimed_at DESC
            LIMIT ?
        """, (limit,))
        
        # Combine and sort by date
        all_activity = []
        
        for post in recent_posts:
            post['created_at'] = post['created_at'][:19]
            all_activity.append(post)
        
        for claim in recent_claims:
            claim['created_at'] = claim['created_at'][:19]
            all_activity.append(claim)
        
        # Sort by date and return most recent
        all_activity.sort(key=lambda x: x['created_at'], reverse=True)
        return all_activity[:limit] 