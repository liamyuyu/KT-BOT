-- KT-BOT Database Initialization Script
-- This script runs automatically when PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ktbot TO ktbot;

-- Create indexes for better performance (tables will be created by Alembic migrations)
-- These are defensive - they'll be created if tables exist

DO $$
BEGIN
    -- Index for conversations table (if exists)
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'conversations') THEN
        CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
    END IF;

    -- Index for messages table (if exists)
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'messages') THEN
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
    END IF;

    -- Index for sync_tasks table (if exists)
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'sync_tasks') THEN
        CREATE INDEX IF NOT EXISTS idx_sync_tasks_status ON sync_tasks(status);
        CREATE INDEX IF NOT EXISTS idx_sync_tasks_created_at ON sync_tasks(created_at DESC);
    END IF;
END $$;

-- Log initialization
SELECT 'KT-BOT database initialized successfully' AS status;
