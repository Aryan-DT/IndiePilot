"""
Simulation module for IndiePilot
Handles IndieSim scenarios, scoring, and debriefing
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from .db import safe_query, safe_execute
from .utils import generate_id

class SimManager:
    """Manages IndieSim scenarios and scoring"""
    
    def __init__(self):
        self.scenarios = self._load_scenarios()
        self.scoring_weights = {
            'frugality': 0.25,
            'safety': 0.30,
            'time': 0.20,
            'initiative': 0.25
        }
    
    def _load_scenarios(self) -> List[Dict[str, Any]]:
        """Load scenarios from embedded data (in real app, this would be from JSON file)"""
        return [
            {
                'id': 'scenario_budget_shopping',
                'title': 'Budget Shopping Challenge',
                'description': 'You have $50 to buy groceries for the week. How do you approach this?',
                'est_time': 5,
                'steps': [
                    {
                        'question': 'You arrive at the grocery store with $50. What\'s your first step?',
                        'choices': [
                            {
                                'text': 'Grab a cart and start shopping',
                                'scores': {'frugality': 20, 'safety': 80, 'time': 60, 'initiative': 40}
                            },
                            {
                                'text': 'Make a list and check prices first',
                                'scores': {'frugality': 90, 'safety': 90, 'time': 80, 'initiative': 70}
                            },
                            {
                                'text': 'Buy whatever looks good',
                                'scores': {'frugality': 30, 'safety': 70, 'time': 40, 'initiative': 30}
                            }
                        ]
                    },
                    {
                        'question': 'You find some items are more expensive than expected. What do you do?',
                        'choices': [
                            {
                                'text': 'Buy them anyway and hope for the best',
                                'scores': {'frugality': 20, 'safety': 60, 'time': 50, 'initiative': 40}
                            },
                            {
                                'text': 'Look for cheaper alternatives or sales',
                                'scores': {'frugality': 95, 'safety': 85, 'time': 70, 'initiative': 80}
                            },
                            {
                                'text': 'Skip those items entirely',
                                'scores': {'frugality': 80, 'safety': 90, 'time': 60, 'initiative': 60}
                            }
                        ]
                    },
                    {
                        'question': 'You\'re at the checkout and realize you\'re over budget. What\'s your approach?',
                        'choices': [
                            {
                                'text': 'Put back the most expensive items',
                                'scores': {'frugality': 90, 'safety': 95, 'time': 80, 'initiative': 85}
                            },
                            {
                                'text': 'Ask to borrow money from a friend',
                                'scores': {'frugality': 40, 'safety': 70, 'time': 60, 'initiative': 50}
                            },
                            {
                                'text': 'Use a credit card (even though you don\'t have one)',
                                'scores': {'frugality': 10, 'safety': 30, 'time': 40, 'initiative': 20}
                            }
                        ]
                    }
                ]
            },
            {
                'id': 'scenario_transportation',
                'title': 'First Solo Transportation',
                'description': 'You need to get to a new location across town. How do you plan your journey?',
                'est_time': 4,
                'steps': [
                    {
                        'question': 'How do you start planning your route?',
                        'choices': [
                            {
                                'text': 'Ask a friend to drive you',
                                'scores': {'frugality': 60, 'safety': 85, 'time': 70, 'initiative': 40}
                            },
                            {
                                'text': 'Research public transit options online',
                                'scores': {'frugality': 90, 'safety': 80, 'time': 85, 'initiative': 85}
                            },
                            {
                                'text': 'Just start walking and figure it out',
                                'scores': {'frugality': 95, 'safety': 40, 'time': 30, 'initiative': 60}
                            }
                        ]
                    },
                    {
                        'question': 'You discover the bus route has changed. What\'s your next move?',
                        'choices': [
                            {
                                'text': 'Call a rideshare service',
                                'scores': {'frugality': 30, 'safety': 90, 'time': 80, 'initiative': 70}
                            },
                            {
                                'text': 'Check for alternative routes or ask for help',
                                'scores': {'frugality': 85, 'safety': 85, 'time': 70, 'initiative': 90}
                            },
                            {
                                'text': 'Give up and go home',
                                'scores': {'frugality': 80, 'safety': 95, 'time': 50, 'initiative': 20}
                            }
                        ]
                    },
                    {
                        'question': 'You arrive at your destination 15 minutes early. What do you do?',
                        'choices': [
                            {
                                'text': 'Find a nearby cafe to wait',
                                'scores': {'frugality': 40, 'safety': 90, 'time': 85, 'initiative': 70}
                            },
                            {
                                'text': 'Walk around and explore the area',
                                'scores': {'frugality': 90, 'safety': 70, 'time': 80, 'initiative': 85}
                            },
                            {
                                'text': 'Stand outside and wait',
                                'scores': {'frugality': 95, 'safety': 80, 'time': 60, 'initiative': 50}
                            }
                        ]
                    }
                ]
            },
            {
                'id': 'scenario_emergency',
                'title': 'Emergency Situation',
                'description': 'You\'re home alone and encounter an unexpected situation. How do you respond?',
                'est_time': 3,
                'steps': [
                    {
                        'question': 'You hear a strange noise in the house. What\'s your first reaction?',
                        'choices': [
                            {
                                'text': 'Investigate the noise immediately',
                                'scores': {'frugality': 80, 'safety': 30, 'time': 60, 'initiative': 70}
                            },
                            {
                                'text': 'Call a parent or trusted adult',
                                'scores': {'frugality': 90, 'safety': 95, 'time': 80, 'initiative': 80}
                            },
                            {
                                'text': 'Ignore it and continue what you\'re doing',
                                'scores': {'frugality': 70, 'safety': 40, 'time': 90, 'initiative': 30}
                            }
                        ]
                    },
                    {
                        'question': 'You discover a small kitchen fire. What do you do?',
                        'choices': [
                            {
                                'text': 'Try to put it out yourself',
                                'scores': {'frugality': 80, 'safety': 20, 'time': 50, 'initiative': 60}
                            },
                            {
                                'text': 'Call 911 immediately',
                                'scores': {'frugality': 90, 'safety': 95, 'time': 70, 'initiative': 90}
                            },
                            {
                                'text': 'Run outside and call for help',
                                'scores': {'frugality': 90, 'safety': 90, 'time': 60, 'initiative': 80}
                            }
                        ]
                    },
                    {
                        'question': 'The emergency is resolved. What\'s your next step?',
                        'choices': [
                            {
                                'text': 'Document what happened for future reference',
                                'scores': {'frugality': 90, 'safety': 95, 'time': 80, 'initiative': 90}
                            },
                            {
                                'text': 'Forget about it and move on',
                                'scores': {'frugality': 70, 'safety': 60, 'time': 90, 'initiative': 40}
                            },
                            {
                                'text': 'Tell everyone you know about it',
                                'scores': {'frugality': 80, 'safety': 70, 'time': 60, 'initiative': 60}
                            }
                        ]
                    }
                ]
            },
            {
                'id': 'scenario_social_conflict',
                'title': 'Social Conflict Resolution',
                'description': 'You\'re in a group situation where there\'s disagreement. How do you handle it?',
                'est_time': 4,
                'steps': [
                    {
                        'question': 'Two friends are arguing about where to eat. What do you do?',
                        'choices': [
                            {
                                'text': 'Stay quiet and let them figure it out',
                                'scores': {'frugality': 80, 'safety': 90, 'time': 40, 'initiative': 30}
                            },
                            {
                                'text': 'Suggest a compromise or alternative',
                                'scores': {'frugality': 85, 'safety': 95, 'time': 70, 'initiative': 90}
                            },
                            {
                                'text': 'Pick a side and join the argument',
                                'scores': {'frugality': 70, 'safety': 40, 'time': 30, 'initiative': 50}
                            }
                        ]
                    },
                    {
                        'question': 'The argument escalates. How do you respond?',
                        'choices': [
                            {
                                'text': 'Try to mediate and calm everyone down',
                                'scores': {'frugality': 90, 'safety': 85, 'time': 60, 'initiative': 85}
                            },
                            {
                                'text': 'Leave the situation entirely',
                                'scores': {'frugality': 85, 'safety': 95, 'time': 80, 'initiative': 60}
                            },
                            {
                                'text': 'Get involved and take sides',
                                'scores': {'frugality': 60, 'safety': 30, 'time': 40, 'initiative': 40}
                            }
                        ]
                    },
                    {
                        'question': 'The conflict is resolved. What\'s your approach going forward?',
                        'choices': [
                            {
                                'text': 'Suggest establishing ground rules for future decisions',
                                'scores': {'frugality': 90, 'safety': 95, 'time': 80, 'initiative': 90}
                            },
                            {
                                'text': 'Avoid similar situations in the future',
                                'scores': {'frugality': 80, 'safety': 85, 'time': 70, 'initiative': 50}
                            },
                            {
                                'text': 'Act like nothing happened',
                                'scores': {'frugality': 70, 'safety': 60, 'time': 90, 'initiative': 40}
                            }
                        ]
                    }
                ]
            },
            {
                'id': 'scenario_time_management',
                'title': 'Time Management Challenge',
                'description': 'You have multiple commitments and deadlines approaching. How do you prioritize?',
                'est_time': 4,
                'steps': [
                    {
                        'question': 'You have homework, a part-time job, and a social event all due today. What\'s your first step?',
                        'choices': [
                            {
                                'text': 'Start with whatever feels easiest',
                                'scores': {'frugality': 60, 'safety': 70, 'time': 40, 'initiative': 50}
                            },
                            {
                                'text': 'Make a priority list and timeline',
                                'scores': {'frugality': 90, 'safety': 95, 'time': 90, 'initiative': 85}
                            },
                            {
                                'text': 'Try to do everything at once',
                                'scores': {'frugality': 40, 'safety': 30, 'time': 20, 'initiative': 60}
                            }
                        ]
                    },
                    {
                        'question': 'You realize you can\'t complete everything on time. What do you do?',
                        'choices': [
                            {
                                'text': 'Communicate with relevant people and ask for extensions',
                                'scores': {'frugality': 90, 'safety': 95, 'time': 80, 'initiative': 90}
                            },
                            {
                                'text': 'Work through the night to finish everything',
                                'scores': {'frugality': 70, 'safety': 40, 'time': 60, 'initiative': 70}
                            },
                            {
                                'text': 'Give up on some commitments',
                                'scores': {'frugality': 60, 'safety': 70, 'time': 80, 'initiative': 40}
                            }
                        ]
                    },
                    {
                        'question': 'You successfully manage your time. What\'s your reflection?',
                        'choices': [
                            {
                                'text': 'Analyze what worked and plan better for next time',
                                'scores': {'frugality': 95, 'safety': 95, 'time': 90, 'initiative': 95}
                            },
                            {
                                'text': 'Feel relieved it\'s over',
                                'scores': {'frugality': 70, 'safety': 80, 'time': 60, 'initiative': 50}
                            },
                            {
                                'text': 'Take on even more commitments',
                                'scores': {'frugality': 40, 'safety': 30, 'time': 20, 'initiative': 60}
                            }
                        ]
                    }
                ]
            }
        ]
    
    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """Get all available scenarios"""
        return self.scenarios
    
    def get_scenario_by_id(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario['id'] == scenario_id:
                return scenario
        return None
    
    def calculate_score(self, scenario: Dict[str, Any], choices: List[Dict[str, Any]]) -> Tuple[int, Dict[str, int]]:
        """Calculate overall score and breakdown based on choices"""
        if not choices or len(choices) != len(scenario['steps']):
            return 0, {}
        
        # Calculate scores for each category
        category_scores = {'frugality': 0, 'safety': 0, 'time': 0, 'initiative': 0}
        
        for choice in choices:
            for category, score in choice['scores'].items():
                category_scores[category] += score
        
        # Average scores across steps
        num_steps = len(choices)
        for category in category_scores:
            category_scores[category] = round(category_scores[category] / num_steps)
        
        # Calculate weighted overall score
        overall_score = 0
        for category, score in category_scores.items():
            overall_score += score * self.scoring_weights[category]
        
        return round(overall_score), category_scores
    
    def generate_debrief(self, scenario: Dict[str, Any], choices: List[Dict[str, Any]], score: int) -> str:
        """Generate debrief text based on scenario and choices"""
        debriefs = {
            'scenario_budget_shopping': {
                'high': "Excellent job! You demonstrated strong planning skills and financial awareness. Your approach of making a list and checking prices shows mature decision-making.",
                'medium': "Good effort! You showed some planning but could improve by being more systematic about budgeting and preparation.",
                'low': "This was a learning opportunity! Consider planning ahead, making lists, and being more mindful of spending in future situations."
            },
            'scenario_transportation': {
                'high': "Outstanding! You showed excellent planning skills and safety awareness. Researching options and having backup plans demonstrates real independence.",
                'medium': "Good start! You're thinking about safety and planning, but could improve by being more thorough in your preparation.",
                'low': "Remember that transportation planning is about safety first. Always research options, have backup plans, and prioritize getting to your destination safely."
            },
            'scenario_emergency': {
                'high': "Perfect response! You prioritized safety and knew when to seek help. This is exactly how to handle emergency situations.",
                'medium': "You showed some good instincts, but remember that in emergencies, safety should always come first. Don't hesitate to call for help.",
                'low': "In emergency situations, your first priority should always be safety. Call for help immediately rather than trying to handle everything yourself."
            },
            'scenario_social_conflict': {
                'high': "Excellent conflict resolution skills! You showed maturity by staying calm, mediating, and finding solutions that work for everyone.",
                'medium': "You handled the situation reasonably well. Consider being more proactive in finding compromises and preventing escalation.",
                'low': "Social conflicts require patience and communication. Focus on listening, staying calm, and finding solutions that work for everyone involved."
            },
            'scenario_time_management': {
                'high': "Outstanding time management! You showed excellent planning, prioritization, and communication skills. This approach will serve you well.",
                'medium': "Good effort on time management. Consider being more systematic about planning and communicating with others about your commitments.",
                'low': "Time management is a crucial life skill. Focus on planning ahead, setting priorities, and communicating with others about your schedule."
            }
        }
        
        # Determine score category
        if score >= 80:
            category = 'high'
        elif score >= 60:
            category = 'medium'
        else:
            category = 'low'
        
        scenario_debriefs = debriefs.get(scenario['id'], {
            'high': "Great job! You showed excellent judgment and decision-making skills.",
            'medium': "Good effort! You demonstrated some good instincts but there's room for improvement.",
            'low': "This was a learning experience. Focus on planning, safety, and making thoughtful decisions."
        })
        
        return scenario_debriefs[category]
    
    def save_run(self, user_id: str, scenario_id: str, score: int, breakdown: Dict[str, int]) -> bool:
        """Save a simulation run to the database"""
        breakdown_json = json.dumps(breakdown)
        
        safe_execute("""
            INSERT INTO sim_run (id, user_id, scenario_id, score, breakdown)
            VALUES (?, ?, ?, ?, ?)
        """, (generate_id(), user_id, scenario_id, score, breakdown_json))
        
        return True
    
    def get_user_runs(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent simulation runs for a user"""
        runs = safe_query("""
            SELECT scenario_id, score, breakdown, ran_at
            FROM sim_run
            WHERE user_id = ?
            ORDER BY ran_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        # Parse breakdown JSON
        for run in runs:
            try:
                run['breakdown'] = json.loads(run['breakdown'])
            except:
                run['breakdown'] = {}
        
        return runs
    
    def get_judgment_score(self, user_id: str) -> float:
        """Calculate judgment score based on recent simulation runs (0-100)"""
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
    
    def get_scenario_stats(self) -> Dict[str, Any]:
        """Get statistics about scenario usage"""
        total_runs = safe_query("SELECT COUNT(*) as count FROM sim_run")
        total_runs = total_runs[0]['count'] if total_runs else 0
        
        avg_score = safe_query("SELECT AVG(score) as avg_score FROM sim_run")
        avg_score = avg_score[0]['avg_score'] if avg_score and avg_score[0]['avg_score'] else 0
        
        scenario_counts = safe_query("""
            SELECT scenario_id, COUNT(*) as count
            FROM sim_run
            GROUP BY scenario_id
            ORDER BY count DESC
        """)
        
        return {
            'total_runs': total_runs,
            'average_score': round(avg_score, 1) if avg_score else 0,
            'scenario_popularity': {row['scenario_id']: row['count'] for row in scenario_counts}
        } 