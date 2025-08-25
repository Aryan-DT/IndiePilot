"""
IndieGraph module for IndiePilot
Handles skill dependency graph and next-best-skill recommendations
"""

import json
from typing import Dict, List, Any, Optional, Set
from .db import safe_query

class IndieGraph:
    """Manages the skill dependency graph and recommendations"""
    
    def __init__(self):
        # Load the skill dependency graph
        self.graph = self._load_indiegraph()
        self.nodes = self.graph['nodes']
        self.edges = self.graph['edges']
        
        # Build adjacency lists for efficient traversal
        self.adjacency_list = self._build_adjacency_list()
        self.reverse_adjacency = self._build_reverse_adjacency()
    
    def _load_indiegraph(self) -> Dict[str, Any]:
        """Load the skill dependency graph from embedded data"""
        return {
            'nodes': [
                {
                    'id': 'basic_laundry',
                    'title': 'Basic Laundry',
                    'description': 'Sort, wash, dry, and fold clothes',
                    'difficulty': 1,
                    'category': 'household',
                    'prerequisites': []
                },
                {
                    'id': 'meal_planning',
                    'title': 'Meal Planning',
                    'description': 'Plan meals and create shopping lists',
                    'difficulty': 2,
                    'category': 'cooking',
                    'prerequisites': []
                },
                {
                    'id': 'grocery_shopping',
                    'title': 'Grocery Shopping',
                    'description': 'Navigate stores and stick to budget',
                    'difficulty': 2,
                    'category': 'shopping',
                    'prerequisites': ['meal_planning']
                },
                {
                    'id': 'budget_tracking',
                    'title': 'Budget Tracking',
                    'description': 'Track income and expenses',
                    'difficulty': 2,
                    'category': 'finance',
                    'prerequisites': []
                },
                {
                    'id': 'time_management',
                    'title': 'Time Management',
                    'description': 'Plan and prioritize daily activities',
                    'difficulty': 2,
                    'category': 'planning',
                    'prerequisites': []
                },
                {
                    'id': 'public_transport',
                    'title': 'Public Transportation',
                    'description': 'Navigate buses, trains, and schedules',
                    'difficulty': 2,
                    'category': 'transportation',
                    'prerequisites': ['time_management']
                },
                {
                    'id': 'appointment_booking',
                    'title': 'Appointment Booking',
                    'description': 'Schedule and manage appointments',
                    'difficulty': 1,
                    'category': 'communication',
                    'prerequisites': ['time_management']
                },
                {
                    'id': 'emergency_preparedness',
                    'title': 'Emergency Preparedness',
                    'description': 'Handle emergency situations safely',
                    'difficulty': 3,
                    'category': 'safety',
                    'prerequisites': ['basic_laundry', 'budget_tracking']
                },
                {
                    'id': 'cooking_basics',
                    'title': 'Cooking Basics',
                    'description': 'Prepare simple meals safely',
                    'difficulty': 2,
                    'category': 'cooking',
                    'prerequisites': ['grocery_shopping']
                },
                {
                    'id': 'financial_planning',
                    'title': 'Financial Planning',
                    'description': 'Set financial goals and save money',
                    'difficulty': 3,
                    'category': 'finance',
                    'prerequisites': ['budget_tracking', 'time_management']
                },
                {
                    'id': 'conflict_resolution',
                    'title': 'Conflict Resolution',
                    'description': 'Handle disagreements constructively',
                    'difficulty': 3,
                    'category': 'social',
                    'prerequisites': ['appointment_booking']
                },
                {
                    'id': 'job_interview',
                    'title': 'Job Interview Skills',
                    'description': 'Prepare for and conduct interviews',
                    'difficulty': 3,
                    'category': 'career',
                    'prerequisites': ['conflict_resolution', 'financial_planning']
                },
                {
                    'id': 'community_service',
                    'title': 'Community Service',
                    'description': 'Volunteer and give back to community',
                    'difficulty': 2,
                    'category': 'social',
                    'prerequisites': ['time_management', 'budget_tracking']
                },
                {
                    'id': 'public_speaking',
                    'title': 'Public Speaking',
                    'description': 'Present confidently to groups',
                    'difficulty': 3,
                    'category': 'communication',
                    'prerequisites': ['conflict_resolution']
                },
                {
                    'id': 'first_aid',
                    'title': 'Basic First Aid',
                    'description': 'Provide basic medical assistance',
                    'difficulty': 2,
                    'category': 'safety',
                    'prerequisites': ['emergency_preparedness']
                }
            ],
            'edges': [
                {'from': 'meal_planning', 'to': 'grocery_shopping'},
                {'from': 'time_management', 'to': 'public_transport'},
                {'from': 'time_management', 'to': 'appointment_booking'},
                {'from': 'basic_laundry', 'to': 'emergency_preparedness'},
                {'from': 'budget_tracking', 'to': 'emergency_preparedness'},
                {'from': 'grocery_shopping', 'to': 'cooking_basics'},
                {'from': 'budget_tracking', 'to': 'financial_planning'},
                {'from': 'time_management', 'to': 'financial_planning'},
                {'from': 'appointment_booking', 'to': 'conflict_resolution'},
                {'from': 'conflict_resolution', 'to': 'job_interview'},
                {'from': 'financial_planning', 'to': 'job_interview'},
                {'from': 'time_management', 'to': 'community_service'},
                {'from': 'budget_tracking', 'to': 'community_service'},
                {'from': 'conflict_resolution', 'to': 'public_speaking'},
                {'from': 'emergency_preparedness', 'to': 'first_aid'}
            ]
        }
    
    def _build_adjacency_list(self) -> Dict[str, List[str]]:
        """Build adjacency list for forward traversal"""
        adjacency = {node['id']: [] for node in self.nodes}
        
        for edge in self.edges:
            if edge['from'] in adjacency:
                adjacency[edge['from']].append(edge['to'])
        
        return adjacency
    
    def _build_reverse_adjacency(self) -> Dict[str, List[str]]:
        """Build reverse adjacency list for backward traversal"""
        reverse = {node['id']: [] for node in self.nodes}
        
        for edge in self.edges:
            if edge['to'] in reverse:
                reverse[edge['to']].append(edge['from'])
        
        return reverse
    
    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by its ID"""
        for node in self.nodes:
            if node['id'] == node_id:
                return node
        return None
    
    def get_prerequisites(self, skill_id: str) -> List[str]:
        """Get all prerequisites for a skill"""
        node = self.get_node_by_id(skill_id)
        if not node:
            return []
        
        return node.get('prerequisites', [])
    
    def get_dependents(self, skill_id: str) -> List[str]:
        """Get all skills that depend on this skill"""
        return self.adjacency_list.get(skill_id, [])
    
    def is_available(self, skill_id: str, completed_skills: Set[str]) -> bool:
        """Check if a skill is available given completed skills"""
        prerequisites = self.get_prerequisites(skill_id)
        return all(prereq in completed_skills for prereq in prerequisites)
    
    def get_available_skills(self, completed_skills: Set[str]) -> List[Dict[str, Any]]:
        """Get all skills that are available to learn"""
        available = []
        
        for node in self.nodes:
            if node['id'] not in completed_skills and self.is_available(node['id'], completed_skills):
                available.append(node)
        
        return available
    
    def calculate_centrality(self, skill_id: str) -> float:
        """
        Calculate centrality score for a skill using a simple heuristic:
        - Number of skills that depend on this skill (out-degree)
        - Number of skills this skill depends on (in-degree)
        - Higher centrality = more important in the skill tree
        """
        dependents = len(self.get_dependents(skill_id))
        prerequisites = len(self.get_prerequisites(skill_id))
        
        # Centrality = out-degree - in-degree (favors skills that unlock many others)
        centrality = dependents - prerequisites
        
        return centrality
    
    def calculate_coverage(self, skill_id: str, completed_skills: Set[str]) -> float:
        """
        Calculate coverage score for a skill:
        - How many new skills would be unlocked by completing this skill
        - Higher coverage = more immediate impact
        """
        if skill_id in completed_skills:
            return 0.0
        
        # Get skills that would become available
        potential_skills = set()
        for node in self.nodes:
            if (node['id'] not in completed_skills and 
                node['id'] != skill_id and
                self.is_available(node['id'], completed_skills | {skill_id})):
                potential_skills.add(node['id'])
        
        return len(potential_skills)
    
    def get_next_skills(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get recommended next skills using centrality and coverage heuristics.
        
        Algorithm:
        1. Get user's completed skills
        2. Find all available skills
        3. Calculate centrality and coverage for each
        4. Rank by combined score (centrality + coverage)
        5. Return top recommendations
        """
        # Get user's completed skills
        completed_quests = safe_query("""
            SELECT q.id
            FROM quest_progress qp
            JOIN quest q ON qp.quest_id = q.id
            WHERE qp.user_id = ? AND qp.completed_at IS NOT NULL
        """, (user_id,))
        
        completed_skills = {row['id'] for row in completed_quests}
        
        # Get available skills
        available_skills = self.get_available_skills(completed_skills)
        
        if not available_skills:
            # If no skills are available, recommend basic skills
            return [node for node in self.nodes if not node['prerequisites']][:limit]
        
        # Calculate scores for each available skill
        scored_skills = []
        for skill in available_skills:
            centrality = self.calculate_centrality(skill['id'])
            coverage = self.calculate_coverage(skill['id'], completed_skills)
            
            # Combined score (can be adjusted based on preference)
            combined_score = centrality + coverage
            
            scored_skills.append({
                **skill,
                'centrality': centrality,
                'coverage': coverage,
                'combined_score': combined_score
            })
        
        # Sort by combined score (descending)
        scored_skills.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Return top recommendations
        return scored_skills[:limit]
    
    def get_skill_path(self, target_skill_id: str, completed_skills: Set[str]) -> List[Dict[str, Any]]:
        """Get the optimal path to learn a target skill"""
        if target_skill_id in completed_skills:
            return []
        
        # Use breadth-first search to find shortest path
        queue = [(target_skill_id, [])]
        visited = set()
        
        while queue:
            current_skill, path = queue.pop(0)
            
            if current_skill in visited:
                continue
            
            visited.add(current_skill)
            
            # Check if this skill is available
            if self.is_available(current_skill, completed_skills):
                return path + [self.get_node_by_id(current_skill)]
            
            # Add prerequisites to queue
            prerequisites = self.get_prerequisites(current_skill)
            for prereq in prerequisites:
                if prereq not in completed_skills and prereq not in visited:
                    queue.append((prereq, path + [self.get_node_by_id(current_skill)]))
        
        return []
    
    def get_skill_tree(self, completed_skills: Set[str]) -> Dict[str, Any]:
        """Get the complete skill tree with completion status"""
        tree = {
            'nodes': [],
            'edges': self.edges,
            'completed': list(completed_skills)
        }
        
        for node in self.nodes:
            node_data = {
                **node,
                'completed': node['id'] in completed_skills,
                'available': self.is_available(node['id'], completed_skills),
                'centrality': self.calculate_centrality(node['id'])
            }
            tree['nodes'].append(node_data)
        
        return tree
    
    def get_skill_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about the user's skill progress"""
        # Get completed skills
        completed_quests = safe_query("""
            SELECT q.id, q.title, q.difficulty
            FROM quest_progress qp
            JOIN quest q ON qp.quest_id = q.id
            WHERE qp.user_id = ? AND qp.completed_at IS NOT NULL
        """, (user_id,))
        
        completed_skills = {row['id'] for row in completed_quests}
        
        # Calculate statistics
        total_skills = len(self.nodes)
        completed_count = len(completed_skills)
        completion_rate = (completed_count / total_skills) * 100 if total_skills > 0 else 0
        
        # Available skills
        available_skills = self.get_available_skills(completed_skills)
        available_count = len(available_skills)
        
        # Skills by difficulty
        difficulty_counts = {1: 0, 2: 0, 3: 0}
        for quest in completed_quests:
            difficulty = quest['difficulty']
            if difficulty in difficulty_counts:
                difficulty_counts[difficulty] += 1
        
        # Next milestones
        next_skills = self.get_next_skills(user_id, 3)
        
        return {
            'total_skills': total_skills,
            'completed_skills': completed_count,
            'available_skills': available_count,
            'completion_rate': round(completion_rate, 1),
            'difficulty_breakdown': difficulty_counts,
            'next_recommendations': next_skills
        }
    
    def search_skills(self, query: str) -> List[Dict[str, Any]]:
        """Search skills by title or description"""
        query_lower = query.lower()
        results = []
        
        for node in self.nodes:
            if (query_lower in node['title'].lower() or 
                query_lower in node['description'].lower() or
                query_lower in node['category'].lower()):
                results.append(node)
        
        return results 