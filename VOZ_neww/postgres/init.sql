CREATE TABLE IF NOT EXISTS voz_messages (
    id TEXT PRIMARY KEY,
    thread_title TEXT,
    thread_date TIMESTAMP,
    latest_poster TEXT,
    latest_post_time TIMESTAMP,
    message_content TEXT,
    thread_url TEXT,
    vader_sentiment_score FLOAT,
    textblob_sentiment_score FLOAT,
    anger FLOAT,
    anticip FLOAT,
    disgust FLOAT,
    fear FLOAT,
    joy FLOAT,
    negative FLOAT,
    positive FLOAT,
    sadness FLOAT,
    surprise FLOAT,
    trust FLOAT,
    analyzed_at TIMESTAMP
);

