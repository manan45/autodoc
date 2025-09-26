# Quick Setup Guide for Supabase Integration

## 1. Set Environment Variables

Based on your terminal output, you have a Supabase project. Set these environment variables:

```bash
export SUPABASE_URL="https://cwhvaojtdpqczdqzxtpb.supabase.co"
export SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIs..."  # Your full key here
```

Or create a `.env` file in the project root:

```bash
# Create .env file
cat > .env << 'EOF'
SUPABASE_URL=https://cwhvaojtdpqczdqzxtpb.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
EOF
```

## 2. Create Database Schema

Go to your Supabase project dashboard:
1. Click "SQL Editor" in the left sidebar
2. Create a new query
3. Paste and run this SQL:

```sql
-- Analysis Steps Table
CREATE TABLE IF NOT EXISTS analysis_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step_name TEXT NOT NULL,
    step_type TEXT NOT NULL,
    data JSONB,
    metadata JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    session_id TEXT NOT NULL
);

-- LLM Interactions Table
CREATE TABLE IF NOT EXISTS llm_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    model TEXT NOT NULL,
    context JSONB,
    metrics JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    session_id TEXT NOT NULL,
    prompt_hash TEXT
);

-- Vector Embeddings Table
CREATE TABLE IF NOT EXISTS vector_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding JSONB NOT NULL,
    content_type TEXT NOT NULL,
    metadata JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    content_hash TEXT
);

-- Quality Assessments Table
CREATE TABLE IF NOT EXISTS quality_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_path TEXT NOT NULL,
    quality_metrics JSONB,
    llm_assessment JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    session_id TEXT NOT NULL
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_analysis_steps_session ON analysis_steps(session_id);
CREATE INDEX IF NOT EXISTS idx_analysis_steps_timestamp ON analysis_steps(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_llm_interactions_session ON llm_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_llm_interactions_timestamp ON llm_interactions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_type ON vector_embeddings(content_type);
CREATE INDEX IF NOT EXISTS idx_quality_assessments_session ON quality_assessments(session_id);
CREATE INDEX IF NOT EXISTS idx_quality_assessments_timestamp ON quality_assessments(timestamp DESC);

-- Grant access to anonymous users for development
GRANT ALL ON analysis_steps TO anon;
GRANT ALL ON llm_interactions TO anon;
GRANT ALL ON vector_embeddings TO anon;
GRANT ALL ON quality_assessments TO anon;

-- Grant usage on sequences
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon;
```

## 3. Test Connection

```bash
# Test the connection
python3 test_supabase_connection.py

# Should show:
# ✅ All 4 tables found and accessible!
# 🎉 Supabase connection test passed!
```

## 4. Run with Supabase Logging

```bash
# Run analysis with Supabase logging
python3 -m auto_doc_generator.main --analyze --generate

# Start debug interface
python3 -m auto_doc_generator.main --debug
# Then visit: http://localhost:5001
```

## 5. Check Your Data

Go to your Supabase dashboard → Table Editor to see the logged data:
- `analysis_steps` - Each step of the documentation process
- `llm_interactions` - All OpenAI API calls with metrics
- `vector_embeddings` - Semantic embeddings of code components
- `quality_assessments` - Quality analysis results

## Troubleshooting

### Connection Issues
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Test Python imports
python3 -c "from supabase import create_client; print('Supabase client available')"
```

### Table Issues
- Make sure you ran the SQL schema in Supabase SQL Editor
- Check that tables exist in your Supabase dashboard → Table Editor
- Verify the `anon` role has permissions on the tables

### Permission Issues
If you get permission errors, you may need to adjust RLS policies or use a different key.

The integration is now ready to use! 🚀
