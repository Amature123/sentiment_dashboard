# Use Python 3.8 as base image
FROM python:3.11.5

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
        postgresql-client

# Copy Python requirements and install Python dependencies

COPY . .

COPY start.sh /start.sh

RUN chmod +x /start.sh

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Download NLTK data
RUN python -m nltk.downloader vader_lexicon punkt


# Expose ports for FastAPI and React
EXPOSE 8000

