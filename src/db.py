"""
Database module for IndiePilot
Handles SQLite database initialization, connections, and seeding
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Database file path
DB_PATH = "indiepilot.db"

def get_db_connection() -> sqlite3.Connection:
    """Get a database connection with proper configuration"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn

def init_db():
    """Initialize the database with schema"""
    schema_path = Path("db/schema.sql")
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    conn = get_db_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

def seed_database():
    """Seed the database with initial data"""
    conn = get_db_connection()
    try:
        # Check if already seeded
        cursor = conn.execute("SELECT COUNT(*) FROM quest")
        if cursor.fetchone()[0] > 0:
            return  # Already seeded
        
        # Seed quests
        seed_quests(conn)
        
        # Seed scenarios (stored in JSON for now)
        # Scenarios are loaded dynamically from JSON files
        
        # Seed board posts
        seed_board_posts(conn)
        
        # Seed IndieGraph data
        # Graph data is loaded dynamically from JSON files
        
        conn.commit()
        
    finally:
        conn.close()

def seed_quests(conn: sqlite3.Connection):
    """Seed quest data"""
    quests_data = [
        {
            'id': 'quest_laundry',
            'title': 'Do Your Own Laundry',
            'description': 'Learn to sort, wash, dry, and fold your clothes independently',
            'difficulty': 1,
            'xp': 50,
            'est_minutes': 45,
            'materials': 'Dirty clothes, laundry detergent, washing machine'
        },
        {
            'id': 'quest_meal_prep',
            'title': 'Cook a $10 Meal',
            'description': 'Plan and cook a nutritious meal within a $10 budget',
            'difficulty': 2,
            'xp': 75,
            'est_minutes': 60,
            'materials': 'Ingredients, cooking utensils, recipe'
        },
        {
            'id': 'quest_library_booking',
            'title': 'Book a Study Room',
            'description': 'Navigate the library website and reserve a study space',
            'difficulty': 1,
            'xp': 30,
            'est_minutes': 15,
            'materials': 'Computer/phone, library card'
        },
        {
            'id': 'quest_appointment_reschedule',
            'title': 'Reschedule an Appointment',
            'description': 'Call and reschedule a medical or academic appointment',
            'difficulty': 2,
            'xp': 60,
            'est_minutes': 20,
            'materials': 'Phone, appointment details'
        },
        {
            'id': 'quest_solo_transit',
            'title': 'First Solo Transit Ride',
            'description': 'Plan and take a public transit trip independently (simulated)',
            'difficulty': 3,
            'xp': 100,
            'est_minutes': 90,
            'materials': 'Transit card, route planning app'
        },
        {
            'id': 'quest_grocery_budget',
            'title': 'Grocery Shopping on Budget',
            'description': 'Create a shopping list and stick to a budget at the grocery store',
            'difficulty': 2,
            'xp': 70,
            'est_minutes': 45,
            'materials': 'Shopping list, budget, grocery store'
        },
        {
            'id': 'quest_time_management',
            'title': 'Create a Weekly Schedule',
            'description': 'Plan your week with time blocks for study, activities, and rest',
            'difficulty': 1,
            'xp': 40,
            'est_minutes': 30,
            'materials': 'Calendar, planner, or digital tool'
        },
        {
            'id': 'quest_emergency_contact',
            'title': 'Set Up Emergency Contacts',
            'description': 'Program important phone numbers and emergency contacts in your phone',
            'difficulty': 1,
            'xp': 25,
            'est_minutes': 15,
            'materials': 'Phone, contact information'
        },
        {
            'id': 'quest_basic_first_aid',
            'title': 'Learn Basic First Aid',
            'description': 'Complete a basic first aid course or learn essential skills',
            'difficulty': 2,
            'xp': 80,
            'est_minutes': 120,
            'materials': 'First aid kit, online course or instructor'
        },
        {
            'id': 'quest_public_speaking',
            'title': 'Present to a Small Group',
            'description': 'Prepare and deliver a short presentation to classmates or family',
            'difficulty': 3,
            'xp': 90,
            'est_minutes': 60,
            'materials': 'Presentation materials, audience'
        },
        {
            'id': 'quest_job_interview',
            'title': 'Practice Job Interview',
            'description': 'Conduct a mock job interview with a family member or mentor',
            'difficulty': 3,
            'xp': 85,
            'est_minutes': 45,
            'materials': 'Resume, interview questions, practice partner'
        },
        {
            'id': 'quest_community_service',
            'title': 'Volunteer in Community',
            'description': 'Find and participate in a local community service opportunity',
            'difficulty': 2,
            'xp': 75,
            'est_minutes': 180,
            'materials': 'Transportation, appropriate clothing'
        }
    ]
    
    for quest in quests_data:
        conn.execute("""
            INSERT OR REPLACE INTO quest (id, title, description, difficulty, xp, est_minutes, materials)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            quest['id'], quest['title'], quest['description'], 
            quest['difficulty'], quest['xp'], quest['est_minutes'], quest['materials']
        ))

def seed_board_posts(conn: sqlite3.Connection):
    """Seed sample board posts"""
    posts_data = [
        {
            'id': 'post_study_1',
            'user_id': 'demo_user_1',
            'kind': 'study',
            'title': 'Math Study Group',
            'detail': 'Looking for study partners for Algebra 2. Meet at library 3-5pm weekdays.',
            'share_code': 'STDY-A9F4'
        },
        {
            'id': 'post_carpool_1',
            'user_id': 'demo_user_2',
            'kind': 'carpool',
            'title': 'School Carpool',
            'detail': 'Need ride to school from downtown area. Can contribute to gas.',
            'share_code': 'CARP-B7E2'
        },
        {
            'id': 'post_swap_1',
            'user_id': 'demo_user_3',
            'kind': 'swap',
            'title': 'Guitar Lessons for Math Help',
            'detail': 'I can teach guitar basics in exchange for math tutoring.',
            'share_code': 'SWAP-C3D8'
        }
    ]
    
    for post in posts_data:
        conn.execute("""
            INSERT OR REPLACE INTO board_post (id, user_id, kind, title, detail, share_code)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            post['id'], post['user_id'], post['kind'], 
            post['title'], post['detail'], post['share_code']
        ))

def safe_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a safe parameterized query and return results as list of dicts"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def safe_execute(query: str, params: tuple = ()) -> int:
    """Execute a safe parameterized query and return number of affected rows"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

def safe_execute_many(query: str, params_list: List[tuple]) -> int:
    """Execute multiple safe parameterized queries"""
    conn = get_db_connection()
    try:
        cursor = conn.executemany(query, params_list)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

def get_user_or_create(user_id: str, name: str = "Teen Explorer") -> Dict[str, Any]:
    """Get user or create if doesn't exist"""
    users = safe_query("SELECT * FROM user WHERE id = ?", (user_id,))
    
    if not users:
        safe_execute("INSERT INTO user (id, name) VALUES (?, ?)", (user_id, name))
        return {'id': user_id, 'name': name, 'created_at': datetime.now().isoformat()}
    
    return dict(users[0])

def get_user_settings(user_id: str) -> Dict[str, Any]:
    """Get user settings or create defaults"""
    settings = safe_query("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    
    if not settings:
        # Create default settings
        safe_execute("""
            INSERT INTO user_settings (user_id, spend_ratio, save_ratio, share_ratio,
                                     skills_weight, budgeting_weight, community_weight, judgment_weight)
            VALUES (?, 60.0, 30.0, 10.0, 0.30, 0.30, 0.15, 0.25)
        """, (user_id,))
        
        return {
            'user_id': user_id,
            'spend_ratio': 60.0,
            'save_ratio': 30.0,
            'share_ratio': 10.0,
            'skills_weight': 0.30,
            'budgeting_weight': 0.30,
            'community_weight': 0.15,
            'judgment_weight': 0.25
        }
    
    return dict(settings[0])

def update_user_settings(user_id: str, **kwargs) -> bool:
    """Update user settings"""
    valid_fields = {
        'spend_ratio', 'save_ratio', 'share_ratio',
        'skills_weight', 'budgeting_weight', 'community_weight', 'judgment_weight'
    }
    
    updates = []
    params = []
    
    for key, value in kwargs.items():
        if key in valid_fields:
            updates.append(f"{key} = ?")
            params.append(value)
    
    if not updates:
        return False
    
    params.append(user_id)
    query = f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?"
    
    return safe_execute(query, tuple(params)) > 0 