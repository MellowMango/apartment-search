FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (needed for dynamic scraping)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY lynnapse/ ./lynnapse/
COPY seeds/ ./seeds/
COPY tests/ ./tests/

# Create necessary directories
RUN mkdir -p output logs data

# Set environment variables
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_HEADLESS=true
ENV LYNNAPSE_ENV=production

# Create non-root user for security
RUN groupadd -r lynnapse && useradd -r -g lynnapse lynnapse
RUN chown -R lynnapse:lynnapse /app
USER lynnapse

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from lynnapse.cli import app; print('OK')" || exit 1

# Expose port (for future API)
EXPOSE 8000

# Default command - show help
CMD ["python", "-m", "lynnapse.cli", "--help"] 