-- Fix Supabase RLS Policies for Auto Documentation Generator
-- Run this script in your Supabase SQL editor to fix permission issues

-- First, drop all existing policies that might be causing conflicts
DROP POLICY IF EXISTS "Allow service role full access" ON prompts;
DROP POLICY IF EXISTS "Allow authenticated users access" ON prompts;
DROP POLICY IF EXISTS "Allow service role full access" ON template_variables;
DROP POLICY IF EXISTS "Allow authenticated users access" ON template_variables;
DROP POLICY IF EXISTS "Allow service role full access" ON generation_sessions;
DROP POLICY IF EXISTS "Allow authenticated users access" ON generation_sessions;

-- Drop policies for coordinator tables if they exist
DROP POLICY IF EXISTS "Allow service role full access" ON coordinator_tasks;
DROP POLICY IF EXISTS "Allow authenticated users access" ON coordinator_tasks;
DROP POLICY IF EXISTS "Allow service role full access" ON coordinator_decisions;
DROP POLICY IF EXISTS "Allow authenticated users access" ON coordinator_decisions;
DROP POLICY IF EXISTS "Allow service role full access" ON component_interactions;
DROP POLICY IF EXISTS "Allow authenticated users access" ON component_interactions;
DROP POLICY IF EXISTS "Allow service role full access" ON execution_workflows;
DROP POLICY IF EXISTS "Allow authenticated users access" ON execution_workflows;

-- Create new policies with explicit permissions for service_role
-- These policies allow service_role to bypass RLS completely

-- Policies for prompts table
CREATE POLICY "service_role_full_access_prompts" ON prompts
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_access_prompts" ON prompts
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Policies for template_variables table
CREATE POLICY "service_role_full_access_template_variables" ON template_variables
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_access_template_variables" ON template_variables
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Policies for generation_sessions table
CREATE POLICY "service_role_full_access_generation_sessions" ON generation_sessions
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_access_generation_sessions" ON generation_sessions
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Apply policies to coordinator tables if they exist
-- Policies for coordinator_tasks table
CREATE POLICY "service_role_full_access_coordinator_tasks" ON coordinator_tasks
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_access_coordinator_tasks" ON coordinator_tasks
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Policies for coordinator_decisions table
CREATE POLICY "service_role_full_access_coordinator_decisions" ON coordinator_decisions
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_access_coordinator_decisions" ON coordinator_decisions
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Policies for component_interactions table
CREATE POLICY "service_role_full_access_component_interactions" ON component_interactions
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_access_component_interactions" ON component_interactions
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Policies for execution_workflows table
CREATE POLICY "service_role_full_access_execution_workflows" ON execution_workflows
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_access_execution_workflows" ON execution_workflows
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Verify the policies were created successfully
SELECT 
    schemaname,
    tablename,
    policyname,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename IN ('prompts', 'template_variables', 'generation_sessions', 'coordinator_tasks', 'coordinator_decisions', 'component_interactions', 'execution_workflows')
ORDER BY tablename, policyname;
