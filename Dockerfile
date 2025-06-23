FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY lynnapse/ ./lynnapse/
COPY seeds/ ./seeds/

# Create output and logs directories
RUN mkdir -p output logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_HEADLESS=true

# Expose port (if needed for API in future)
EXPOSE 8000

# Default command
CMD ["python", "-m", "lynnapse.cli", "version"] 