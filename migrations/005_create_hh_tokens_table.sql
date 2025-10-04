CREATE TABLE IF NOT EXISTS hh_tokens (
    hh_token_uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_uuid UUID REFERENCES users(user_uuid) ON DELETE CASCADE,
    hh_access_token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
