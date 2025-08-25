import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
import numpy as np
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
import os
from pathlib import Path as PathLib

# Import our modules
from src.db import init_db, get_db_connection, seed_database
from src.budget import BudgetManager
from src.quests import QuestManager
from src.board import BoardManager
from src.sim import SimManager
from src.autonomy import AutonomyIndex
from src.indiegraph import IndieGraph
from src.utils import export_data, import_data, generate_id

# Page config
st.set_page_config(
    page_title="IndiePilot - Independence Copilot for Teens",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .streak-badge {
        background-color: #ffd700;
        color: #000;
        padding: 0.25rem 0.5rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .jar-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .spend-jar { background-color: #ffebee; border-left: 4px solid #f44336; }
    .save-jar { background-color: #e8f5e8; border-left: 4px solid #4caf50; }
    .share-jar { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = generate_id()
if 'user_name' not in st.session_state:
    st.session_state.user_name = "Teen Explorer"

# Initialize database and managers
@st.cache_resource
def initialize_app():
    """Initialize database and all managers"""
    init_db()
    seed_database()
    
    return {
        'budget': BudgetManager(),
        'quests': QuestManager(),
        'board': BoardManager(),
        'sim': SimManager(),
        'autonomy': AutonomyIndex(),
        'indiegraph': IndieGraph()
    }

# Initialize app
managers = initialize_app()

# Main app header
st.markdown('<h1 class="main-header">🚀 IndiePilot</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Your offline, privacy-first independence copilot</p>', unsafe_allow_html=True)

# Navigation tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Dashboard", "💸 Budget", "🧭 Quests", "🤝 Youth Board", "🎯 IndieSim", "⚙️ Settings"
])

# Dashboard Tab
with tab1:
    st.header("🏠 Your Independence Dashboard")
    
    # Get current user data
    autonomy_score = managers['autonomy'].compute_autonomy_index(st.session_state.user_id)
    
    # Welcome section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Welcome back, {st.session_state.user_name}! 👋")
        
        # Get today's streak
        streak = managers['budget'].get_current_streak(st.session_state.user_id)
        if streak > 0:
            st.markdown(f'<div class="streak-badge">🔥 {streak} day streak!</div>', unsafe_allow_html=True)
        else:
            st.markdown("Start your independence journey today!")
    
    with col2:
        st.metric("Autonomy Index", f"{autonomy_score:.1f}/100")
    
    # Autonomy Radar Chart
    st.subheader("🎯 Your Independence Radar")
    radar_fig = managers['autonomy'].plot_radar(st.session_state.user_id)
    st.pyplot(radar_fig)
    
    # IndieGraph Recommendations
    st.subheader("🧠 IndieGraph™ - Skill Dependencies")
    recommendations = managers['indiegraph'].get_next_skills(st.session_state.user_id)
    
    if recommendations:
        st.write("**Recommended next skills to unlock:**")
        for i, skill in enumerate(recommendations[:3], 1):
            st.write(f"{i}. **{skill['title']}** - {skill['description']}")
    else:
        st.write("Complete some quests to get personalized skill recommendations!")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start a Quest", use_container_width=True):
            st.switch_page("🧭 Quests")
    
    with col2:
        if st.button("💰 Log Expense", use_container_width=True):
            st.switch_page("💸 Budget")
    
    with col3:
        if st.button("🎯 Run IndieSim", use_container_width=True):
            st.switch_page("🎯 IndieSim")

# Budget Tab
with tab2:
    st.header("💸 Three-Jar Budget System")
    
    # Budget overview
    budget_data = managers['budget'].get_budget_overview(st.session_state.user_id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="jar-card spend-jar">
            <h4>💸 Spend Jar</h4>
            <h3>${budget_data['spend']:.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="jar-card save-jar">
            <h4>💰 Save Jar</h4>
            <h3>${budget_data['save']:.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="jar-card share-jar">
            <h4>🤝 Share Jar</h4>
            <h3>${budget_data['share']:.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Add income/allowance
    st.subheader("💰 Add Income/Allowance")
    with st.form("income_form"):
        income_amount = st.number_input("Amount ($)", min_value=0.01, value=20.0, step=0.01)
        income_note = st.text_input("Note (e.g., 'Weekly allowance')", value="Weekly allowance")
        
        if st.form_submit_button("Add Income"):
            managers['budget'].add_income(st.session_state.user_id, income_amount, income_note)
            st.success(f"Added ${income_amount:.2f} to your budget!")
            st.rerun()
    
    # Add expense
    st.subheader("💸 Log an Expense")
    with st.form("expense_form"):
        expense_amount = st.number_input("Amount ($)", min_value=0.01, value=5.0, step=0.01)
        expense_jar = st.selectbox("Jar", ["spend", "save", "share"])
        expense_note = st.text_input("What was this for?", value="Lunch")
        
        if st.form_submit_button("Log Expense"):
            managers['budget'].add_expense(st.session_state.user_id, expense_amount, expense_jar, expense_note)
            st.success(f"Logged ${expense_amount:.2f} expense!")
            st.rerun()
    
    # Recent transactions
    st.subheader("📊 Recent Transactions")
    transactions = managers['budget'].get_recent_transactions(st.session_state.user_id, limit=10)
    
    if transactions:
        df = pd.DataFrame(transactions)
        df['amount'] = df['amount'].apply(lambda x: f"${x:.2f}")
        df['ts'] = pd.to_datetime(df['ts']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(df[['ts', 'amount', 'jar', 'note']], hide_index=True)
    else:
        st.write("No transactions yet. Start by adding some income!")
    
    # Streaks and badges
    st.subheader("🏆 Your Achievements")
    streak = managers['budget'].get_current_streak(st.session_state.user_id)
    badges = managers['budget'].get_user_badges(st.session_state.user_id)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Current Streak", f"{streak} days")
    
    with col2:
        if badges:
            st.write("**Badges earned:**")
            for badge in badges:
                st.write(f"🏅 {badge['name']} - {badge['description']}")
        else:
            st.write("Complete 7 days of logging to earn your first badge!")

# Quests Tab
with tab3:
    st.header("🧭 Life Skills Quests")
    
    # Quest categories
    quests = managers['quests'].get_all_quests()
    
    # Filter by difficulty
    difficulty_filter = st.selectbox("Filter by difficulty:", ["All", "Beginner", "Intermediate", "Advanced"])
    
    if difficulty_filter != "All":
        difficulty_map = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
        quests = [q for q in quests if q['difficulty'] == difficulty_map[difficulty_filter]]
    
    # Display quests
    for quest in quests:
        with st.expander(f"🎯 {quest['title']} (XP: {quest['xp']})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Description:** {quest['description']}")
                st.write(f"**Estimated time:** {quest['est_minutes']} minutes")
                st.write(f"**Materials needed:** {quest['materials']}")
                
                # Difficulty indicator
                difficulty_stars = "⭐" * quest['difficulty']
                st.write(f"**Difficulty:** {difficulty_stars}")
            
            with col2:
                # Check if completed
                is_completed = managers['quests'].is_quest_completed(st.session_state.user_id, quest['id'])
                
                if is_completed:
                    st.success("✅ Completed!")
                else:
                    if st.button(f"Start Quest", key=f"start_{quest['id']}"):
                        managers['quests'].start_quest(st.session_state.user_id, quest['id'])
                        st.success("Quest started! Complete it when you're ready.")
                        st.rerun()
                    
                    if st.button(f"Complete Quest", key=f"complete_{quest['id']}"):
                        managers['quests'].complete_quest(st.session_state.user_id, quest['id'])
                        st.success(f"🎉 Quest completed! You earned {quest['xp']} XP!")
                        st.rerun()
    
    # Quest progress
    st.subheader("📈 Your Progress")
    completed_quests = managers['quests'].get_completed_quests(st.session_state.user_id)
    total_xp = sum(q['xp'] for q in completed_quests)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Quests Completed", len(completed_quests))
    
    with col2:
        st.metric("Total XP Earned", total_xp)
    
    if completed_quests:
        st.write("**Recently completed:**")
        for quest in completed_quests[-3:]:
            st.write(f"✅ {quest['title']} (+{quest['xp']} XP)")

# Youth Board Tab
with tab4:
    st.header("🤝 Youth Board")
    st.write("Connect with other teens safely using Share Codes - no personal info needed!")
    
    # Create new post
    st.subheader("📝 Create a Post")
    with st.form("post_form"):
        post_kind = st.selectbox("Type", ["study", "carpool", "swap"])
        post_title = st.text_input("Title")
        post_detail = st.text_area("Details")
        
        if st.form_submit_button("Create Post"):
            if post_title and post_detail:
                share_code = managers['board'].create_post(post_kind, post_title, post_detail)
                st.success(f"Post created! Share Code: **{share_code}**")
                st.rerun()
            else:
                st.error("Please fill in all fields.")
    
    # View posts
    st.subheader("📋 Available Posts")
    
    # Filter posts
    kind_filter = st.selectbox("Filter by type:", ["All", "study", "carpool", "swap"])
    posts = managers['board'].get_posts()
    
    if kind_filter != "All":
        posts = [p for p in posts if p['kind'] == kind_filter]
    
    for post in posts:
        with st.expander(f"📌 {post['title']} ({post['kind'].title()})"):
            st.write(f"**Details:** {post['detail']}")
            st.write(f"**Share Code:** `{post['share_code']}`")
            st.write(f"**Posted:** {post['created_at']}")
            
            if post['status'] == 'available':
                if st.button(f"Claim Post", key=f"claim_{post['id']}"):
                    contact_info = managers['board'].claim_post(post['id'])
                    st.success("Post claimed! Here's the contact info:")
                    st.json(contact_info)
                    st.rerun()
            else:
                st.info("This post has been claimed.")
    
    # My posts
    st.subheader("📤 My Posts")
    my_posts = managers['board'].get_my_posts(st.session_state.user_id)
    
    if my_posts:
        for post in my_posts:
            st.write(f"📌 **{post['title']}** ({post['kind']}) - {post['status']}")
    else:
        st.write("You haven't created any posts yet.")

# IndieSim Tab
with tab5:
    st.header("🎯 IndieSim - Scenario Simulator")
    st.write("Practice real-life decisions in a safe environment!")
    
    # Get available scenarios
    scenarios = managers['sim'].get_available_scenarios()
    
    if 'current_scenario' not in st.session_state:
        st.session_state.current_scenario = None
        st.session_state.current_step = 0
        st.session_state.scenario_choices = []
    
    if st.session_state.current_scenario is None:
        st.subheader("Choose a Scenario")
        
        for scenario in scenarios:
            with st.expander(f"🎭 {scenario['title']}"):
                st.write(f"**Description:** {scenario['description']}")
                st.write(f"**Estimated time:** {scenario['est_time']} minutes")
                
                if st.button(f"Start Scenario", key=f"start_sim_{scenario['id']}"):
                    st.session_state.current_scenario = scenario
                    st.session_state.current_step = 0
                    st.session_state.scenario_choices = []
                    st.rerun()
    
    else:
        # Run scenario
        scenario = st.session_state.current_scenario
        st.subheader(f"🎭 {scenario['title']}")
        
        if st.session_state.current_step < len(scenario['steps']):
            step = scenario['steps'][st.session_state.current_step]
            
            st.write(f"**Step {st.session_state.current_step + 1}:** {step['question']}")
            
            # Show choices
            for i, choice in enumerate(step['choices']):
                if st.button(f"{choice['text']}", key=f"choice_{st.session_state.current_step}_{i}"):
                    st.session_state.scenario_choices.append(choice)
                    st.session_state.current_step += 1
                    st.rerun()
        
        else:
            # Scenario complete - show results
            st.success("🎉 Scenario completed!")
            
            # Calculate score
            score, breakdown = managers['sim'].calculate_score(scenario, st.session_state.scenario_choices)
            
            st.subheader("📊 Your Results")
            st.metric("Overall Score", f"{score}/100")
            
            st.write("**Breakdown:**")
            for category, cat_score in breakdown.items():
                st.write(f"• {category.title()}: {cat_score}/100")
            
            # Debrief
            st.subheader("💡 Debrief")
            debrief = managers['sim'].generate_debrief(scenario, st.session_state.scenario_choices, score)
            st.write(debrief)
            
            # Save results
            if st.button("Save Results"):
                managers['sim'].save_run(st.session_state.user_id, scenario['id'], score, breakdown)
                st.success("Results saved! Your Autonomy Index has been updated.")
                st.session_state.current_scenario = None
                st.session_state.current_step = 0
                st.session_state.scenario_choices = []
                st.rerun()
            
            if st.button("Try Again"):
                st.session_state.current_scenario = None
                st.session_state.current_step = 0
                st.session_state.scenario_choices = []
                st.rerun()

# Settings Tab
with tab6:
    st.header("⚙️ Settings & Safety")
    
    # User settings
    st.subheader("👤 User Settings")
    new_name = st.text_input("Your name", value=st.session_state.user_name)
    if new_name != st.session_state.user_name:
        st.session_state.user_name = new_name
        st.success("Name updated!")
    
    # Budget settings
    st.subheader("💰 Budget Settings")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        spend_ratio = st.slider("Spend Jar %", 0, 100, 60)
    
    with col2:
        save_ratio = st.slider("Save Jar %", 0, 100, 30)
    
    with col3:
        share_ratio = st.slider("Share Jar %", 0, 100, 10)
    
    if spend_ratio + save_ratio + share_ratio != 100:
        st.warning("Ratios must add up to 100%")
    else:
        managers['budget'].update_ratios(st.session_state.user_id, spend_ratio, save_ratio, share_ratio)
        st.success("Budget ratios updated!")
    
    # Autonomy Index weights
    st.subheader("🎯 Autonomy Index Weights")
    col1, col2 = st.columns(2)
    
    with col1:
        skills_weight = st.slider("Skills Weight", 0.0, 1.0, 0.30, 0.05)
        budgeting_weight = st.slider("Budgeting Weight", 0.0, 1.0, 0.30, 0.05)
    
    with col2:
        community_weight = st.slider("Community Weight", 0.0, 1.0, 0.15, 0.05)
        judgment_weight = st.slider("Judgment Weight", 0.0, 1.0, 0.25, 0.05)
    
    total_weight = skills_weight + budgeting_weight + community_weight + judgment_weight
    if abs(total_weight - 1.0) > 0.01:
        st.warning(f"Weights must add up to 1.0 (current: {total_weight:.2f})")
    else:
        managers['autonomy'].update_weights(skills_weight, budgeting_weight, community_weight, judgment_weight)
        st.success("Weights updated!")
    
    # Safety features
    st.subheader("🛡️ Safety Features")
    
    if 'checkin_timer' not in st.session_state:
        st.session_state.checkin_timer = None
    
    if st.session_state.checkin_timer is None:
        if st.button("Start Safety Check-in Timer"):
            st.session_state.checkin_timer = datetime.now()
            st.success("Timer started! Check back in 30 minutes.")
    else:
        elapsed = datetime.now() - st.session_state.checkin_timer
        if elapsed.total_seconds() < 1800:  # 30 minutes
            remaining = 1800 - elapsed.total_seconds()
            st.write(f"⏰ Safety timer: {int(remaining // 60)}m {int(remaining % 60)}s remaining")
            
            if st.button("I'm Safe - Stop Timer"):
                st.session_state.checkin_timer = None
                st.success("Timer stopped. Stay safe!")
                st.rerun()
        else:
            st.warning("⚠️ Safety check-in overdue!")
            if st.button("I'm Safe - Stop Timer"):
                st.session_state.checkin_timer = None
                st.success("Timer stopped. Stay safe!")
                st.rerun()
    
    # Data management
    st.subheader("📊 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Export Data"):
            data = export_data(st.session_state.user_id)
            st.download_button(
                label="Download JSON",
                data=json.dumps(data, indent=2),
                file_name=f"indiepilot_data_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_file = st.file_uploader("📥 Import Data", type=['json'])
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                import_data(st.session_state.user_id, data)
                st.success("Data imported successfully!")
            except Exception as e:
                st.error(f"Import failed: {str(e)}")
    
    # Reset demo data
    st.subheader("🔄 Demo Data")
    if st.button("Reset Demo Data"):
        seed_database()
        st.success("Demo data reset! Refresh the page to see changes.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>🚀 IndiePilot - Empowering teens to build independence safely and positively</p>
    <p>Built with ❤️ for high school hackathons | Offline-first | Privacy-focused</p>
</div>
""", unsafe_allow_html=True)
