import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import numpy as np
from nrclex import NRCLex
from datetime import datetime
import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FetchMessagePipeline:
    def __init__(self):
        # Initialize NLTK
        nltk.download('vader_lexicon', quiet=True)
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze_sentiment(self, text):
        """Analyze sentiment using VADER"""
        sentences = nltk.sent_tokenize(text)
        compound_scores = []
        for sentence in sentences:
            sentiment = self.analyzer.polarity_scores(sentence)
            compound_scores.append(sentiment['compound'])
        if compound_scores:
            avg_compound_score = np.mean(compound_scores)
        else:
            avg_compound_score = 0
        return avg_compound_score

    def analyze_emotion_nrc(self, text):
        """Analyze emotions using NRC Lexicon"""
        emotions_sum = {
            'anger': 0, 'anticip': 0, 'disgust': 0, 'fear': 0, 
            'joy': 0, 'negative': 0, 'positive': 0,
            'sadness': 0, 'surprise': 0, 'trust': 0
        }
        emotion = NRCLex(text).affect_frequencies
        for key in emotions_sum.keys():
            if key in emotion:
                emotions_sum[key] = emotion[key]
        return emotions_sum

    def process_item(self, item, spider):
        """Process each scraped item"""
        messages = [item['message'] for item in data]
        messages.remove("")
        def split_messages(messages):
            result = []
            for message in messages:
                # Split the message, but keep ellipses intact
                parts = re.split(r'(?<!\.)\.(?!\.)', message)
                # Trim whitespace and add non-empty parts to the result
                result.extend([part.strip() for part in parts if part.strip()])
            return result
        # Get the message content
        message_text = split_messages(messages)

        # Analyze sentiment
        sentiment_score = self.analyze_sentiment(message_text)
        
        # Analyze emotions
        emotion_scores = self.analyze_emotion_nrc(message_text)
        
        # Update the item with sentiment and emotion scores
        item.update({
            'vader_sentiment_score': sentiment_score,
            'sentiment_score': sentiment_score,  # Add this line to match the database field
            **emotion_scores,  # Add all emotion scores
            'processed_at': datetime.now().isoformat()
        })
        logger.info(f"Processed item {item['id']}")
        return item

class SentimentAnalysisPipeline:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                dbname="vozdb",
                user="postgres",
                password="postgres",
                host="db",
            )
            self.cur = self.conn.cursor()
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            
    def process_item(self, item, spider):
        try:
            # Store in database with additional emotion fields
            self.cur.execute("""
                INSERT INTO voz_messages (
                    id, thread_title, thread_date, latest_poster, 
                    latest_post_time, message_content, thread_url,
                    vader_sentiment_score, textblob_sentiment_score,
                    anger, anticip, disgust, fear, joy, negative, 
                    positive, sadness, surprise, trust,
                    analyzed_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    vader_sentiment_score = EXCLUDED.vader_sentiment_score,
                    textblob_sentiment_score = EXCLUDED.textblob_sentiment_score,
                    anger = EXCLUDED.anger,
                    anticip = EXCLUDED.anticip,
                    disgust = EXCLUDED.disgust,
                    fear = EXCLUDED.fear,
                    joy = EXCLUDED.joy,
                    negative = EXCLUDED.negative,
                    positive = EXCLUDED.positive,
                    sadness = EXCLUDED.sadness,
                    surprise = EXCLUDED.surprise,
                    trust = EXCLUDED.trust,
                    analyzed_at = EXCLUDED.analyzed_at
            """, (
                item['id'], item['thread_title'], item['thread_date'],
                item['latest_poster'], item['latest_post_time'],
                item['message_content'], item['thread_url'],
                item['vader_sentiment_score'], item['sentiment_score'],
                item['anger'], item['anticip'], item['disgust'],
                item['fear'], item['joy'], item['negative'],
                item['positive'], item['sadness'], item['surprise'],
                item['trust'], item['processed_at']
            ))
            
            self.conn.commit()
            logger.info(f"Successfully stored item {item['id']} in database")
            
        except Exception as e:
            logger.error(f"Error storing item {item['id']} in database: {str(e)}")
            self.conn.rollback()
            
        return item

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()


        
