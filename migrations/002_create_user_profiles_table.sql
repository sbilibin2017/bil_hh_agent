CREATE TABLE IF NOT EXISTS user_profiles (
    user_profile_uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_uuid UUID REFERENCES users(user_uuid),
    experience TEXT,       -- одно поле для опыта пользователя
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
