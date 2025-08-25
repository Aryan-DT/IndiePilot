"""
Utils module for IndiePilot
Helper functions for IDs, dates, validation, and export/import
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from .db import safe_query, safe_execute

def generate_id() -> str:
    """Generate a unique ID for database records"""
    return str(uuid.uuid4())

def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string"""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except:
        return datetime.now()

def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Basic phone number validation"""
    import re
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 10

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def calculate_age(birth_date: datetime) -> int:
    """Calculate age from birth date"""
    today = datetime.now()
    age = today.year - birth_date.year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    return age

def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:.2f}"

def format_percentage(value: float, total: float) -> str:
    """Format value as percentage of total"""
    if total == 0:
        return "0%"
    percentage = (value / total) * 100
    return f"{percentage:.1f}%"

def export_data(user_id: str) -> Dict[str, Any]:
    """
    Export user data as JSON for portability.
    Includes all user data except sensitive information.
    """
    export_data = {
        'export_date': datetime.now().isoformat(),
        'user_id': user_id,
        'version': '1.0'
    }
    
    # Export budget data
    budget_logs = safe_query("""
        SELECT ts, amount, jar, note
        FROM budget_log
        WHERE user_id = ?
        ORDER BY ts
    """, (user_id,))
    
    export_data['budget'] = {
        'transactions': [dict(log) for log in budget_logs]
    }
    
    # Export quest progress
    quest_progress = safe_query("""
        SELECT qp.quest_id, qp.started_at, qp.completed_at,
               q.title, q.description, q.difficulty, q.xp
        FROM quest_progress qp
        JOIN quest q ON qp.quest_id = q.id
        WHERE qp.user_id = ?
        ORDER BY qp.started_at
    """, (user_id,))
    
    export_data['quests'] = {
        'progress': [dict(progress) for progress in quest_progress]
    }
    
    # Export board activity
    board_posts = safe_query("""
        SELECT kind, title, detail, share_code, created_at, status
        FROM board_post
        WHERE user_id = ?
        ORDER BY created_at
    """, (user_id,))
    
    board_claims = safe_query("""
        SELECT bc.claimed_at, bp.kind, bp.title, bp.share_code
        FROM board_claim bc
        JOIN board_post bp ON bc.post_id = bp.id
        WHERE bc.user_id = ?
        ORDER BY bc.claimed_at
    """, (user_id,))
    
    export_data['board'] = {
        'posts': [dict(post) for post in board_posts],
        'claims': [dict(claim) for claim in board_claims]
    }
    
    # Export simulation runs
    sim_runs = safe_query("""
        SELECT scenario_id, score, breakdown, ran_at
        FROM sim_run
        WHERE user_id = ?
        ORDER BY ran_at
    """, (user_id,))
    
    export_data['simulations'] = {
        'runs': [dict(run) for run in sim_runs]
    }
    
    # Export user settings
    user_settings = safe_query("""
        SELECT spend_ratio, save_ratio, share_ratio,
               skills_weight, budgeting_weight, community_weight, judgment_weight
        FROM user_settings
        WHERE user_id = ?
    """, (user_id,))
    
    if user_settings:
        export_data['settings'] = dict(user_settings[0])
    
    return export_data

def import_data(user_id: str, data: Dict[str, Any]) -> bool:
    """
    Import user data from JSON export.
    Validates data structure and imports safely.
    """
    try:
        # Validate export format
        if not isinstance(data, dict) or 'version' not in data:
            raise ValueError("Invalid export format")
        
        # Import budget data
        if 'budget' in data and 'transactions' in data['budget']:
            for transaction in data['budget']['transactions']:
                safe_execute("""
                    INSERT INTO budget_log (id, user_id, ts, amount, jar, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    generate_id(), user_id,
                    transaction.get('ts', datetime.now().isoformat()),
                    transaction.get('amount', 0),
                    transaction.get('jar', 'spend'),
                    transaction.get('note', 'Imported transaction')
                ))
        
        # Import quest progress
        if 'quests' in data and 'progress' in data['quests']:
            for progress in data['quests']['progress']:
                # Check if quest exists
                quest_exists = safe_query("SELECT id FROM quest WHERE id = ?", (progress.get('quest_id'),))
                if quest_exists:
                    safe_execute("""
                        INSERT INTO quest_progress (id, user_id, quest_id, started_at, completed_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        generate_id(), user_id,
                        progress.get('quest_id'),
                        progress.get('started_at', datetime.now().isoformat()),
                        progress.get('completed_at')
                    ))
        
        # Import board posts
        if 'board' in data and 'posts' in data['board']:
            for post in data['board']['posts']:
                safe_execute("""
                    INSERT INTO board_post (id, user_id, kind, title, detail, share_code, created_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    generate_id(), user_id,
                    post.get('kind', 'study'),
                    post.get('title', 'Imported post'),
                    post.get('detail', ''),
                    post.get('share_code', f"IMP-{generate_id()[:8]}"),
                    post.get('created_at', datetime.now().isoformat()),
                    post.get('status', 'available')
                ))
        
        # Import simulation runs
        if 'simulations' in data and 'runs' in data['simulations']:
            for run in data['simulations']['runs']:
                safe_execute("""
                    INSERT INTO sim_run (id, user_id, scenario_id, score, breakdown, ran_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    generate_id(), user_id,
                    run.get('scenario_id', 'unknown'),
                    run.get('score', 50),
                    run.get('breakdown', '{}'),
                    run.get('ran_at', datetime.now().isoformat())
                ))
        
        # Import user settings
        if 'settings' in data:
            settings = data['settings']
            safe_execute("""
                INSERT OR REPLACE INTO user_settings 
                (user_id, spend_ratio, save_ratio, share_ratio,
                 skills_weight, budgeting_weight, community_weight, judgment_weight)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                settings.get('spend_ratio', 60.0),
                settings.get('save_ratio', 30.0),
                settings.get('share_ratio', 10.0),
                settings.get('skills_weight', 0.30),
                settings.get('budgeting_weight', 0.30),
                settings.get('community_weight', 0.15),
                settings.get('judgment_weight', 0.25)
            ))
        
        return True
        
    except Exception as e:
        print(f"Import failed: {str(e)}")
        return False

def validate_export_data(data: Dict[str, Any]) -> List[str]:
    """Validate export data structure and return list of errors"""
    errors = []
    
    if not isinstance(data, dict):
        errors.append("Data must be a dictionary")
        return errors
    
    required_fields = ['version', 'user_id', 'export_date']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if 'version' in data and data['version'] != '1.0':
        errors.append("Unsupported export version")
    
    # Validate budget data
    if 'budget' in data:
        if not isinstance(data['budget'], dict):
            errors.append("Budget data must be a dictionary")
        elif 'transactions' in data['budget']:
            if not isinstance(data['budget']['transactions'], list):
                errors.append("Budget transactions must be a list")
    
    # Validate quest data
    if 'quests' in data:
        if not isinstance(data['quests'], dict):
            errors.append("Quest data must be a dictionary")
        elif 'progress' in data['quests']:
            if not isinstance(data['quests']['progress'], list):
                errors.append("Quest progress must be a list")
    
    return errors

def get_data_summary(user_id: str) -> Dict[str, Any]:
    """Get a summary of user's data for export preview"""
    summary = {
        'user_id': user_id,
        'export_date': datetime.now().isoformat()
    }
    
    # Budget summary
    budget_count = safe_query("""
        SELECT COUNT(*) as count FROM budget_log WHERE user_id = ?
    """, (user_id,))
    summary['budget_transactions'] = budget_count[0]['count'] if budget_count else 0
    
    # Quest summary
    quest_count = safe_query("""
        SELECT COUNT(*) as count FROM quest_progress WHERE user_id = ?
    """, (user_id,))
    summary['quests_started'] = quest_count[0]['count'] if quest_count else 0
    
    completed_count = safe_query("""
        SELECT COUNT(*) as count FROM quest_progress 
        WHERE user_id = ? AND completed_at IS NOT NULL
    """, (user_id,))
    summary['quests_completed'] = completed_count[0]['count'] if completed_count else 0
    
    # Board summary
    posts_count = safe_query("""
        SELECT COUNT(*) as count FROM board_post WHERE user_id = ?
    """, (user_id,))
    summary['board_posts'] = posts_count[0]['count'] if posts_count else 0
    
    claims_count = safe_query("""
        SELECT COUNT(*) as count FROM board_claim WHERE user_id = ?
    """, (user_id,))
    summary['board_claims'] = claims_count[0]['count'] if claims_count else 0
    
    # Simulation summary
    sim_count = safe_query("""
        SELECT COUNT(*) as count FROM sim_run WHERE user_id = ?
    """, (user_id,))
    summary['simulation_runs'] = sim_count[0]['count'] if sim_count else 0
    
    return summary

def backup_database() -> str:
    """Create a backup of the database (simplified for demo)"""
    import shutil
    from pathlib import Path
    
    backup_path = f"backup_indiepilot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        shutil.copy2("indiepilot.db", backup_path)
        return backup_path
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        return ""

def restore_database(backup_path: str) -> bool:
    """Restore database from backup (simplified for demo)"""
    import shutil
    
    try:
        shutil.copy2(backup_path, "indiepilot.db")
        return True
    except Exception as e:
        print(f"Restore failed: {str(e)}")
        return False 