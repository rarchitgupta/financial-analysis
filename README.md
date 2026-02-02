# Financial Analysis Tool

A FastAPI backend service for fetching, storing, and analyzing financial market data.

## Why

Building financial applications requires reliable access to market data. This project provides a clean REST API that wraps third-party financial data sources, handling authentication, rate limiting, and error management automatically.

## What

The Financial Analysis Tool is a Python backend that connects to AlphaVantage for real-time stock data. It currently provides:

- Current stock quotes and metadata
- Historical price data for technical analysis
- Symbol search by company name

Future versions will add data persistence, user portfolios, and aggregated analytics.

## How

Built with FastAPI for high performance and async support. Each endpoint wraps AlphaVantage API calls with proper error handling, validation, and response formatting. The service layer abstracts API complexity, making it easy to extend with new data sources or modify behavior.

## Setup

```bash
uv sync
export ALPHAVANTAGE_API_KEY=your_key_here
uv run uvicorn app.main:app --reload
```

API documentation at http://localhost:8000/docs

## Endpoints

- GET /api/stock/quote/{symbol}: Get current stock quote
- GET /api/stock/history/{symbol}?days=30: Get daily price history
- GET /api/stock/search?q=tesla: Search for stock symbols

## Roadmap

Week 1: Complete - Project setup and basic API
Week 2: In Progress - External API integration and error handling
Week 3: Data persistence with database or files
Week 4: User data models and CRUD operations
Week 5: Analytics and aggregation endpoints
Week 6: Dashboards and deployment
