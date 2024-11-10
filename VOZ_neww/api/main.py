# api/main.py
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
import time
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="VOZ Analytics API")
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    "dbname": "vozdb",
    "user": "postgres",
    "password": "postgres",
    "host": "db",
    "port": "5432"
}

def wait_for_db(max_retries=30, delay_seconds=2):
    """Wait for database to be ready"""
    retries = 0
    while retries < max_retries:
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            logger.info("Successfully connected to the database")
            return True
        except psycopg2.Error as e:
            retries += 1
            logger.warning(f"Attempt {retries}/{max_retries} to connect to database failed: {str(e)}")
            logger.warning("Retrying in %s seconds...", delay_seconds)
            time.sleep(delay_seconds)
    
    raise Exception("Could not connect to the database after multiple attempts")

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")

def get_db():
    """Database dependency for FastAPI"""
    with get_db_connection() as conn:
        yield conn

# Analytics queries
def get_sentiment_stats(conn):
    try:
        with conn.cursor() as cur:
            query = """
                SELECT 
                    DATE_TRUNC('hour', analyzed_at) as time_bucket,
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(*) as message_count
                FROM voz_messages
                GROUP BY time_bucket
                ORDER BY time_bucket DESC
                LIMIT 24
            """
            cur.execute(query)
            results = cur.fetchall()
            return list(results)
    except psycopg2.Error as e:
        logger.error(f"Error fetching sentiment stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")

def get_emotion_stats(conn):
    try:
        with conn.cursor() as cur:
            query = """
                SELECT emotion, score FROM (
                    SELECT 
                        'anger' as emotion, AVG(anger) as score
                    FROM voz_messages
                    WHERE analyzed_at >= NOW() - INTERVAL '24 hours'
                    UNION ALL
                    SELECT 'joy' as emotion, AVG(joy) as score
                    FROM voz_messages
                    WHERE analyzed_at >= NOW() - INTERVAL '24 hours'
                    UNION ALL
                    SELECT 'sadness' as emotion, AVG(sadness) as score
                    FROM voz_messages
                    WHERE analyzed_at >= NOW() - INTERVAL '24 hours'
                    UNION ALL
                    SELECT 'fear' as emotion, AVG(fear) as score
                    FROM voz_messages
                    WHERE analyzed_at >= NOW() - INTERVAL '24 hours'
                    UNION ALL
                    SELECT 'trust' as emotion, AVG(trust) as score
                    FROM voz_messages
                    WHERE analyzed_at >= NOW() - INTERVAL '24 hours'
                ) subquery
            """
            cur.execute(query)
            results = cur.fetchall()
            return list(results)
    except psycopg2.Error as e:
        logger.error(f"Error fetching emotion stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting up FastAPI application")
    try:
        wait_for_db()
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint that also verifies database connection"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return {
                    "status": "healthy",
                    "database": "connected",
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# API endpoints
@app.get("/stats/sentiment")
def sentiment_stats(conn = Depends(get_db)):
    return get_sentiment_stats(conn)

@app.get("/stats/emotions")
def emotion_stats(conn = Depends(get_db)):
    return get_emotion_stats(conn)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")