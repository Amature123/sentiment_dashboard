CREATE TABLE IF NOT EXISTS voz_messages (
    id TEXT PRIMARY KEY,
    thread_title TEXT,
    thread_date TIMESTAMP,
    latest_poster TEXT,
    latest_post_time TIMESTAMP,
    message_content TEXT,
    thread_url TEXT,
    positive_count FLOAT,
    negative_count FLOAT,
    neutral_count FLOAT,
    analyzed_at TIMESTAMP
);

