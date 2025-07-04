# 🤖 OpenAI API Setup for Lynnapse

## Quick Setup

1. **Copy the environment template:**
   ```bash
   cp env.template .env
   ```

2. **Get your OpenAI API key:**
   - Go to https://platform.openai.com/api-keys
   - Create a new API key
   - Copy the key (starts with `sk-`)

3. **Update your `.env` file:**
   ```bash
   # OpenAI API Configuration (Required for LLM-assisted discovery)
   OPENAI_API_KEY=sk-your-actual-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_MAX_TOKENS=1000
   OPENAI_TEMPERATURE=0.1
   OPENAI_TIMEOUT=30
   
   # LLM Configuration
   LLM_CACHE_ENABLED=true
   LLM_CACHE_TTL=86400
   LLM_MAX_RETRIES=3
   LLM_COST_TRACKING=true
   ```

4. **Install the OpenAI dependency:**
   ```bash
   pip install openai==1.51.2
   ```

## What This Enables

✅ **Fully Dynamic University Discovery** - The scraper can now adapt to ANY university site by name
✅ **Intelligent Faculty Directory Finding** - LLM analyzes university websites to find faculty pages
✅ **Cost-Effective** - Uses GPT-4o-mini (cheap) with caching to minimize API calls
✅ **Smart Caching** - Stores LLM responses for 24 hours to avoid repeated calls

## How It Works

1. **First Time**: When scraping a new university, the LLM analyzes the site structure
2. **Cache Hit**: Subsequent runs use cached results (no LLM call needed)
3. **Fallback Chain**: sitemap → navigation → common paths → subdomain → **LLM** → firecrawl

## Cost Estimation

- **GPT-4o-mini**: ~$0.0001 per university discovery
- **With caching**: Most universities cost $0 after first discovery
- **Budget**: ~$1-5 for discovering 100+ new universities

## Next Steps

After setting up your `.env` file, the LLM integration will be automatically available in the `UniversityAdapter` for fully dynamic university discovery. 