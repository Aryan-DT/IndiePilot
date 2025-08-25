-- IndiePilot Database Schema
-- SQLite database for offline-first teen independence app

-- User table
CREATE TABLE IF NOT EXISTS user (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Budget logging table
CREATE TABLE IF NOT EXISTS budget_log (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    amount REAL NOT NULL,
    jar TEXT NOT NULL CHECK(jar IN ('spend', 'save', 'share')),
    note TEXT,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- Quest definitions
CREATE TABLE IF NOT EXISTS quest (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    difficulty INTEGER NOT NULL CHECK(difficulty BETWEEN 1 AND 3),
    xp INTEGER NOT NULL,
    est_minutes INTEGER NOT NULL,
    materials TEXT
);

-- Quest progress tracking
CREATE TABLE IF NOT EXISTS quest_progress (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    quest_id TEXT NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (quest_id) REFERENCES quest(id)
);

-- Youth board posts
CREATE TABLE IF NOT EXISTS board_post (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('study', 'carpool', 'swap')),
    title TEXT NOT NULL,
    detail TEXT NOT NULL,
    share_code TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'available' CHECK(status IN ('available', 'claimed')),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- Board post claims
CREATE TABLE IF NOT EXISTS board_claim (
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    claimed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    mock_contact TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES board_post(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- IndieSim runs
CREATE TABLE IF NOT EXISTS sim_run (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100),
    breakdown TEXT NOT NULL, -- JSON string of category scores
    ran_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- User settings
CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY,
    spend_ratio REAL DEFAULT 60.0,
    save_ratio REAL DEFAULT 30.0,
    share_ratio REAL DEFAULT 10.0,
    skills_weight REAL DEFAULT 0.30,
    budgeting_weight REAL DEFAULT 0.30,
    community_weight REAL DEFAULT 0.15,
    judgment_weight REAL DEFAULT 0.25,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_budget_log_user_ts ON budget_log(user_id, ts);
CREATE INDEX IF NOT EXISTS idx_quest_progress_user ON quest_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_quest_progress_completed ON quest_progress(completed_at);
CREATE INDEX IF NOT EXISTS idx_board_post_status ON board_post(status);
CREATE INDEX IF NOT EXISTS idx_board_post_share_code ON board_post(share_code);
CREATE INDEX IF NOT EXISTS idx_sim_run_user ON sim_run(user_id);
CREATE INDEX IF NOT EXISTS idx_sim_run_ts ON sim_run(ran_at); 