# API Key Configuration Guide

## Overview
The AI-Driven Stock Trade Advisor can work without API keys using built-in data sources, but some features are enhanced with API keys.

## Current Status
✅ **Application Status**: Fully functional with Alpha Vantage API configured
✅ **Alpha Vantage API**: Configured and working (100 data points available)
✅ **Yahoo Finance**: Working as fallback data source (250 data points, no API key required)

## Optional API Keys

### Alpha Vantage API (Recommended)
- **Purpose**: Enhanced market data and technical indicators
- **Cost**: Free tier available (5 calls/minute, 500 calls/day)
- **Setup**: 
  1. Visit https://www.alphavantage.co/support/#api-key
  2. Get your free API key
  3. Edit `config/api_keys.env`
  4. Replace `your_alpha_vantage_api_key_here` with your actual key

### Alpaca Trading API (Optional)
- **Purpose**: Paper trading and real trading execution
- **Cost**: Free for paper trading
- **Setup**: 
  1. Visit https://app.alpaca.markets/paper/dashboard/overview
  2. Create account and get API keys
  3. Edit `config/api_keys.env`
  4. Replace placeholder values with your keys

### News API (Optional)
- **Purpose**: News sentiment analysis and market events
- **Cost**: Free tier available (1,000 requests/day)
- **Setup**: 
  1. Visit https://newsapi.org/register
  2. Get your free API key
  3. Edit `config/api_keys.env`
  4. Replace `your_news_api_key_here` with your actual key

## Configuration File
Edit `config/api_keys.env`:
```env
# Alpha Vantage API - Market Data Provider
ALPHA_VANTAGE_API_KEY=your_actual_key_here

# Alpaca Trading API - Paper Trading and Real Trading
ALPHA_API_KEY=your_actual_key_here
ALPACA_SECRET_KEY=your_actual_secret_here

# News API - Sentiment Analysis
NEWS_API_KEY=your_actual_key_here
```

## Security Notes
- ✅ API keys are stored in `config/api_keys.env` (excluded from Git)
- ✅ No hardcoded secrets in source code
- ✅ Environment variables used for secure loading
- ✅ Previous exposed keys have been sanitized

## Testing API Configuration
Run this command to test your API keys:
```bash
python -c "from src.data_layer.api_client import APIClient; client = APIClient(); print('Alpha Vantage:', 'Configured' if client.alpha_vantage_key and client.alpha_vantage_key != 'your_alpha_vantage_api_key_here' else 'Not Configured')"
```

## Current Functionality
- ✅ Market data retrieval (Alpha Vantage + Yahoo Finance)
- ✅ Enhanced market data with technical indicators
- ✅ User profile management
- ✅ Market scanner and watchlists
- ✅ Database operations
- ✅ UI functionality
- ⚠️ Trading execution (requires Alpaca API keys)
- ⚠️ News sentiment analysis (requires News API key)

The application is fully functional without API keys, but adding them enhances specific features. 