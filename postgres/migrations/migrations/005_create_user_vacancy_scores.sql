CREATE TABLE IF NOT EXISTS user_vacancy_scores (
    user_vacancy_score_uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_uuid UUID REFERENCES users(user_uuid),
    vacancy_uuid UUID REFERENCES vacancies(vacancy_uuid),
    score NUMERIC NOT NULL,         -- чем выше, тем более релевантно
    calculated_at TIMESTAMP DEFAULT NOW()
);
