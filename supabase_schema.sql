-- Supabase schema for Auto Documentation Generator
-- Optimized for service role access with explicit role targeting in RLS policies
-- Run this entire file in your Supabase SQL editor to create/update the schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table for storing LLM prompts and responses
CREATE TABLE IF NOT EXISTS prompts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    prompt_type VARCHAR(100) NOT NULL,
    prompt_content TEXT NOT NULL,
    context TEXT,
    repository_path TEXT,
    component_id TEXT,
    variables JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_used VARCHAR(100),
    tokens_used INTEGER DEFAULT 0,
    response_content TEXT,
    success BOOLEAN DEFAULT TRUE
);

-- Table for storing template variables and generated content
CREATE TABLE IF NOT EXISTS template_variables (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    template_name VARCHAR(200) NOT NULL,
    template_type VARCHAR(50) DEFAULT 'html',
    repository_path TEXT,
    variables JSONB DEFAULT '{}',
    generated_content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    file_path TEXT,
    generation_time DECIMAL(10,3) DEFAULT 0.0
);

-- Table for storing documentation generation sessions
CREATE TABLE IF NOT EXISTS generation_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    repository_path TEXT NOT NULL,
    session_type VARCHAR(100) DEFAULT 'full_generation',
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    duration DECIMAL(10,3) DEFAULT 0.0,
    total_files_analyzed INTEGER DEFAULT 0,
    total_functions INTEGER DEFAULT 0,
    total_classes INTEGER DEFAULT 0,
    pages_generated INTEGER DEFAULT 0,
    templates_used JSONB DEFAULT '[]',
    prompts_used JSONB DEFAULT '[]',
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    output_format VARCHAR(50) DEFAULT 'html',
    output_path TEXT
);

-- Migration: Handle column name change from duration_seconds to duration
-- This will safely rename the column if it exists with the old name
DO $$
BEGIN
    -- Check if the old column exists and rename it
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'generation_sessions' 
        AND column_name = 'duration_seconds'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE generation_sessions RENAME COLUMN duration_seconds TO duration;
    END IF;
    
    -- If neither column exists, add the duration column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'generation_sessions' 
        AND column_name = 'duration'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE generation_sessions ADD COLUMN duration DECIMAL(10,3) DEFAULT 0.0;
    END IF;
END $$;

-- Performance indexes (grouped by table)
-- Prompts table indexes
CREATE INDEX IF NOT EXISTS idx_prompts_repository_path ON prompts(repository_path);
CREATE INDEX IF NOT EXISTS idx_prompts_created_at ON prompts(created_at);
CREATE INDEX IF NOT EXISTS idx_prompts_type_success ON prompts(prompt_type, success);

-- Template variables indexes  
CREATE INDEX IF NOT EXISTS idx_template_variables_repository_path ON template_variables(repository_path);
CREATE INDEX IF NOT EXISTS idx_template_variables_created_at ON template_variables(created_at);
CREATE INDEX IF NOT EXISTS idx_template_variables_name_type ON template_variables(template_name, template_type);

-- Generation sessions indexes
CREATE INDEX IF NOT EXISTS idx_generation_sessions_repository_path ON generation_sessions(repository_path);
CREATE INDEX IF NOT EXISTS idx_generation_sessions_start_time ON generation_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_generation_sessions_type_success ON generation_sessions(session_type, success);

-- Row Level Security (RLS) policies
ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE template_variables ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_sessions ENABLE ROW LEVEL SECURITY;

-- Function to create standard RLS policies for a table
CREATE OR REPLACE FUNCTION create_standard_rls_policies(table_name TEXT) 
RETURNS void AS $$
BEGIN
    -- Drop existing policies
    EXECUTE format('DROP POLICY IF EXISTS "Allow service role full access" ON %I', table_name);
    EXECUTE format('DROP POLICY IF EXISTS "Allow authenticated users access" ON %I', table_name);
    
    -- Create new policies
    EXECUTE format('CREATE POLICY "Allow service role full access" ON %I FOR ALL TO service_role USING (true)', table_name);
    EXECUTE format('CREATE POLICY "Allow authenticated users access" ON %I FOR ALL TO authenticated USING (true)', table_name);
END;
$$ LANGUAGE plpgsql;

-- Apply standard RLS policies to core tables
SELECT create_standard_rls_policies('prompts');
SELECT create_standard_rls_policies('template_variables');
SELECT create_standard_rls_policies('generation_sessions');

-- Function to automatically update end_time and calculate duration for generation sessions
CREATE OR REPLACE FUNCTION update_generation_session_end_time()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.end_time IS NOT NULL AND OLD.end_time IS NULL THEN
        NEW.duration = EXTRACT(EPOCH FROM (NEW.end_time - NEW.start_time));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically calculate duration when end_time is set
DROP TRIGGER IF EXISTS trigger_update_generation_session_end_time ON generation_sessions;
CREATE TRIGGER trigger_update_generation_session_end_time
    BEFORE UPDATE ON generation_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_generation_session_end_time();

-- Function to clean up old data (can be called periodically)
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INTEGER DEFAULT 90)
RETURNS TABLE(
    prompts_deleted INTEGER,
    template_variables_deleted INTEGER,
    generation_sessions_deleted INTEGER
) AS $$
DECLARE
    cutoff_date TIMESTAMP WITH TIME ZONE;
    prompts_count INTEGER;
    templates_count INTEGER;
    sessions_count INTEGER;
BEGIN
    cutoff_date := NOW() - INTERVAL '1 day' * days_to_keep;
    
    -- Count records to be deleted
    SELECT COUNT(*) INTO prompts_count FROM prompts WHERE created_at < cutoff_date;
    SELECT COUNT(*) INTO templates_count FROM template_variables WHERE created_at < cutoff_date;
    SELECT COUNT(*) INTO sessions_count FROM generation_sessions WHERE start_time < cutoff_date;
    
    -- Delete old records
    DELETE FROM prompts WHERE created_at < cutoff_date;
    DELETE FROM template_variables WHERE created_at < cutoff_date;
    DELETE FROM generation_sessions WHERE start_time < cutoff_date;
    
    -- Return counts
    RETURN QUERY SELECT prompts_count, templates_count, sessions_count;
END;
$$ LANGUAGE plpgsql;

-- View for analytics dashboard
CREATE OR REPLACE VIEW analytics_summary AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_prompts,
    COUNT(*) FILTER (WHERE success = true) as successful_prompts,
    COUNT(*) FILTER (WHERE success = false) as failed_prompts,
    SUM(tokens_used) as total_tokens,
    COUNT(DISTINCT repository_path) as unique_repositories,
    COUNT(DISTINCT prompt_type) as unique_prompt_types
FROM prompts 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- View for generation session analytics
CREATE OR REPLACE VIEW session_analytics AS
SELECT 
    DATE(start_time) as date,
    COUNT(*) as total_sessions,
    COUNT(*) FILTER (WHERE success = true) as successful_sessions,
    COUNT(*) FILTER (WHERE success = false) as failed_sessions,
    AVG(duration) as avg_duration_seconds,
    SUM(total_files_analyzed) as total_files_processed,
    SUM(pages_generated) as total_pages_generated,
    COUNT(DISTINCT repository_path) as unique_repositories
FROM generation_sessions 
WHERE start_time >= NOW() - INTERVAL '30 days'
GROUP BY DATE(start_time)
ORDER BY date DESC;

-- Table for storing coordinator tasks and execution plans
CREATE TABLE IF NOT EXISTS coordinator_tasks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES generation_sessions(id),
    task_type VARCHAR(100) NOT NULL,
    task_description TEXT NOT NULL,
    task_priority INTEGER DEFAULT 1,
    task_status VARCHAR(50) DEFAULT 'pending',
    parent_task_id UUID REFERENCES coordinator_tasks(id),
    dependencies JSONB DEFAULT '[]',
    assigned_component VARCHAR(100),
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    execution_plan JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Table for storing coordinator decisions and reasoning
CREATE TABLE IF NOT EXISTS coordinator_decisions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES generation_sessions(id),
    task_id UUID REFERENCES coordinator_tasks(id),
    decision_type VARCHAR(100) NOT NULL,
    decision_prompt TEXT NOT NULL,
    decision_response TEXT,
    reasoning TEXT,
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    alternatives_considered JSONB DEFAULT '[]',
    context JSONB DEFAULT '{}',
    model_used VARCHAR(100),
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    execution_time_ms INTEGER DEFAULT 0
);

-- Table for storing component interactions and communications
CREATE TABLE IF NOT EXISTS component_interactions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES generation_sessions(id),
    task_id UUID REFERENCES coordinator_tasks(id),
    from_component VARCHAR(100) NOT NULL,
    to_component VARCHAR(100) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    message_content TEXT,
    request_data JSONB DEFAULT '{}',
    response_data JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    execution_time_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing execution workflows and plans
CREATE TABLE IF NOT EXISTS execution_workflows (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES generation_sessions(id),
    workflow_name VARCHAR(200) NOT NULL,
    workflow_description TEXT,
    workflow_steps JSONB NOT NULL,
    current_step INTEGER DEFAULT 0,
    workflow_status VARCHAR(50) DEFAULT 'pending',
    input_requirements JSONB DEFAULT '{}',
    output_expectations JSONB DEFAULT '{}',
    estimated_duration_seconds INTEGER DEFAULT 0,
    actual_duration_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Coordinator system indexes (optimized composite indexes)
CREATE INDEX IF NOT EXISTS idx_coordinator_tasks_session_status ON coordinator_tasks(session_id, task_status);
CREATE INDEX IF NOT EXISTS idx_coordinator_tasks_parent_priority ON coordinator_tasks(parent_task_id, task_priority);

CREATE INDEX IF NOT EXISTS idx_coordinator_decisions_session_task ON coordinator_decisions(session_id, task_id);
CREATE INDEX IF NOT EXISTS idx_coordinator_decisions_created_at ON coordinator_decisions(created_at);

CREATE INDEX IF NOT EXISTS idx_component_interactions_session_task ON component_interactions(session_id, task_id);
CREATE INDEX IF NOT EXISTS idx_component_interactions_components ON component_interactions(from_component, to_component);

CREATE INDEX IF NOT EXISTS idx_execution_workflows_session_status ON execution_workflows(session_id, workflow_status);

-- RLS policies for new tables
ALTER TABLE coordinator_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE coordinator_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE component_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE execution_workflows ENABLE ROW LEVEL SECURITY;

-- Apply standard RLS policies to coordinator tables
SELECT create_standard_rls_policies('coordinator_tasks');
SELECT create_standard_rls_policies('coordinator_decisions');
SELECT create_standard_rls_policies('component_interactions');
SELECT create_standard_rls_policies('execution_workflows');

-- Function to automatically update task completion times
CREATE OR REPLACE FUNCTION update_task_completion()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.task_status = 'completed' AND OLD.task_status != 'completed' THEN
        NEW.completed_at = NOW();
    ELSIF NEW.task_status = 'in_progress' AND OLD.task_status = 'pending' THEN
        NEW.started_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_task_completion ON coordinator_tasks;
CREATE TRIGGER trigger_update_task_completion
    BEFORE UPDATE ON coordinator_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_task_completion();

-- View for coordinator analytics
CREATE OR REPLACE VIEW coordinator_analytics AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE task_status = 'completed') as completed_tasks,
    COUNT(*) FILTER (WHERE task_status = 'failed') as failed_tasks,
    COUNT(*) FILTER (WHERE task_status = 'in_progress') as in_progress_tasks,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_execution_time_seconds,
    COUNT(DISTINCT assigned_component) as unique_components_used
FROM coordinator_tasks 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Table comments (essential documentation only)
COMMENT ON TABLE prompts IS 'LLM prompts, responses, and execution metadata';
COMMENT ON TABLE template_variables IS 'Template variables and generated HTML content';  
COMMENT ON TABLE generation_sessions IS 'Documentation generation session tracking';
COMMENT ON TABLE coordinator_tasks IS 'Coordinator system task management';
COMMENT ON TABLE coordinator_decisions IS 'AI coordinator decision tracking with reasoning';
COMMENT ON TABLE component_interactions IS 'Inter-component communication logs';
COMMENT ON TABLE execution_workflows IS 'High-level workflow definitions and status';
