# AutoCoach

Sports science training analytics and planning platform with TrainingPeaks integration.

## Features

- **Training Load Analytics**: Compute ATL, CTL, TSB using pandas-based exponential weighted moving averages
- **TrainingPeaks Integration**: OAuth 2.0 API client for fetching workout data and metrics
- **RESTful API**: FastAPI endpoints for metrics computation and training data
- **Comprehensive Testing**: Unit tests for core functionality and API endpoints

## Setup

### 1. Environment Setup

```bash
python3 -m venv eve_env
source eve_env/bin/activate  # On Windows: eve_env\Scripts\activate
pip install -r requirements.txt
```

### 2. TrainingPeaks API Setup (Optional)

1. Request API access: https://api.trainingpeaks.com/request-access
2. Copy `env.template` to `.env` and fill in your credentials:
   ```bash
   cp env.template .env
   # Edit .env with your TrainingPeaks client_id and client_secret
   ```

### 3. Run Development Server

```bash
eve_env/bin/uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

### 4. Run Tests

```bash
eve_env/bin/pytest -q
```

## API Endpoints

### Core Metrics
- `POST /metrics/daily` - Compute training metrics from activity data

### TrainingPeaks Integration
- `GET /auth/trainingpeaks` - Initiate OAuth flow
- `GET /auth/callback` - OAuth callback handler
- `GET /trainingpeaks/profile` - Get athlete profile
- `GET /trainingpeaks/activities` - Fetch activities for date range
- `POST /trainingpeaks/metrics` - Compute metrics from TrainingPeaks data

## Development

The project follows these principles:
- Pandas-first approach for data analysis over SQL
- Comprehensive unit testing with pytest
- FastAPI for modern async API development
- OAuth 2.0 for secure third-party integrations
