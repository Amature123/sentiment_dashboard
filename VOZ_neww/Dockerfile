# Use Python 3.11 as base image
FROM python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    curl \
    pkg-config \
    libssl-dev

# Install Rust (required for maturin)
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy Python requirements first
COPY requirements.txt .

# Install maturin first
RUN pip install --no-cache-dir maturin

# Install underthesea explicitly with version
RUN pip install --no-cache-dir underthesea==6.8.4

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose ports for FastAPI
EXPOSE 8000

# Set environment variables for underthesea
ENV PYTHONPATH="${PYTHONPATH}:/app"