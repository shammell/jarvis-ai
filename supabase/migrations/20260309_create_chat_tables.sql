-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create chats table
CREATE TABLE IF NOT EXISTS chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    archived BOOLEAN DEFAULT FALSE
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create chat_runs table (optional observability)
CREATE TABLE IF NOT EXISTS chat_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    model_source TEXT,
    latency_ms INTEGER,
    success BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id);
CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON chats(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_runs_chat_id ON chat_runs(chat_id);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_runs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- RLS Policies for chats
CREATE POLICY "Users can view own chats"
    ON chats FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own chats"
    ON chats FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own chats"
    ON chats FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own chats"
    ON chats FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for messages
CREATE POLICY "Users can view messages in own chats"
    ON messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM chats
            WHERE chats.id = messages.chat_id
            AND chats.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create messages in own chats"
    ON messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM chats
            WHERE chats.id = chat_id
            AND chats.user_id = auth.uid()
        )
    );

-- RLS Policies for chat_runs
CREATE POLICY "Users can view own chat runs"
    ON chat_runs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM chats
            WHERE chats.id = chat_runs.chat_id
            AND chats.user_id = auth.uid()
        )
    );

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for chats updated_at
CREATE TRIGGER update_chats_updated_at
    BEFORE UPDATE ON chats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
