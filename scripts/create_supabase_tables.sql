-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing table if it exists
DROP TABLE IF EXISTS sap_kb CASCADE;

-- Create main table
CREATE TABLE sap_kb (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inc_number TEXT,
    module TEXT,
    error_text TEXT,
    root_cause TEXT,
    resolution TEXT,
    transaction_code TEXT,
    resolution_category TEXT,
    embedding VECTOR(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_sap_kb_module ON sap_kb(module);
CREATE INDEX idx_sap_kb_inc_number ON sap_kb(inc_number);
CREATE INDEX idx_sap_kb_created_at ON sap_kb(created_at);
CREATE INDEX idx_sap_kb_resolution_category ON sap_kb(resolution_category);

-- Create vector similarity search index (IVFFlat for better performance)
CREATE INDEX idx_sap_kb_embedding ON sap_kb USING ivfflat (embedding vector_cosine_ops);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Attach trigger to table
CREATE TRIGGER update_sap_kb_updated_at 
    BEFORE UPDATE ON sap_kb 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create vector search function
CREATE OR REPLACE FUNCTION match_sap_kb(
    query_embedding VECTOR(768),
    match_threshold FLOAT,
    match_count INT
)
RETURNS TABLE(
    id UUID,
    inc_number TEXT,
    module TEXT,
    error_text TEXT,
    root_cause TEXT,
    resolution TEXT,
    transaction_code TEXT,
    resolution_category TEXT,
    similarity FLOAT
)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        sap_kb.id,
        sap_kb.inc_number,
        sap_kb.module,
        sap_kb.error_text,
        sap_kb.root_cause,
        sap_kb.resolution,
        sap_kb.transaction_code,
        sap_kb.resolution_category,
        1 - (sap_kb.embedding <=> query_embedding) as similarity
    FROM sap_kb
    WHERE 1 - (sap_kb.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
$$;

-- Grant permissions (adjust as needed)
GRANT ALL ON sap_kb TO authenticated;
GRANT ALL ON sap_kb TO service_role;
GRANT EXECUTE ON FUNCTION match_sap_kb TO authenticated;
GRANT EXECUTE ON FUNCTION match_sap_kb TO service_role;

-- Create a view for easy reporting
CREATE VIEW sap_kb_stats AS
SELECT 
    module,
    resolution_category,
    COUNT(*) as incident_count,
    MIN(created_at) as first_incident,
    MAX(created_at) as last_incident
FROM sap_kb
GROUP BY module, resolution_category
ORDER BY module, incident_count DESC;

-- Create a function to get module distribution
CREATE OR REPLACE FUNCTION get_module_distribution()
RETURNS TABLE(module TEXT, count BIGINT)
LANGUAGE SQL
AS $$
    SELECT module, COUNT(*) as count
    FROM sap_kb
    GROUP BY module
    ORDER BY count DESC;
$$;
