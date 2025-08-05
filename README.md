# Deribit API Integration - Python Developer Workout

A Python application that connects to the Deribit Testnet, fetches option instrument data via REST API, subscribes to real-time WebSocket updates, and stores the data in a SQLite database.

## Features

-  **REST API Integration**: Fetches option instruments data
-  **WebSocket Real-time Data**: Subscribes to ticker updates for multiple instruments
-  **Database Storage**: Stores instrument data with price, volatility, delta, and timestamps
-  **Async/Await Support**: Uses asyncio for efficient concurrent operations
-  **Configuration Management**: Uses .env files for secure credential storage
-  **Comprehensive Logging**: Detailed logging with file and console output
-  **Error Handling**: Robust error handling with reconnection capabilities
-  **Database Utilities**: Functions to query and display stored data
-  **Modular Architecture**: Clean, maintainable code structure

## Project Structure

```
├── main.py                 # Main application entry point
├── config.py              # Configuration management
├── deribit_client.py      # REST and WebSocket API clients
├── database.py            # Database operations and management
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment configuration
├── README.md             # This file
└── deribit_data.db       # SQLite database (created automatically)
```

## Prerequisites

1. **Python 3.8+** installed on your system
2. **Deribit Test Account**: Sign up at [https://test.deribit.com](https://test.deribit.com)
3. **API Credentials**: Generate API keys from your account settings

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
# Clone the repository (or download the files)
cd deribit-api-integration

# Install required packages
pip install -r requirements.txt
```

### 2. Configure API Credentials

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Update the `.env` file with your Deribit API credentials:

```env
DERIBIT_CLIENT_ID=your_client_id_here
DERIBIT_CLIENT_SECRET=your_client_secret_here
DERIBIT_BASE_URL=https://test.deribit.com
DERIBIT_WS_URL=wss://test.deribit.com/ws/api/v2
DATABASE_PATH=deribit_data.db
LOG_LEVEL=INFO
LOG_FILE=deribit_app.log
```

### 3. Generate Deribit API Keys

1. Go to [https://test.deribit.com](https://test.deribit.com)
2. Sign up or log into your test account
3. Navigate to **Account Settings** → **API** → **Create New API Key**
4. Enable required scopes (at minimum: **read** permissions)
5. Copy the Client ID and Client Secret to your `.env` file

## Usage

### Running the Main Application

```bash
# Start the data collector
python main.py
```

The application will:
1. Authenticate with Deribit API
2. Fetch available option instruments via REST API
3. Select 5 instruments for WebSocket subscription
4. Start collecting real-time ticker data
5. Store data continuously in the SQLite database

### Viewing Stored Data

```bash
# Show last 10 records
python main.py show-records

# Show last 20 records
python main.py show-records 20

# Show database statistics
python main.py show-stats
```



## Database Schema

The application creates a SQLite database with the following schema:

```sql
CREATE TABLE option_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_name TEXT NOT NULL,
    price REAL,                    -- Mark price or last price
    volatility REAL,               -- Implied volatility
    delta REAL,                    -- Delta from Greeks
    timestamp DATETIME,            -- Data timestamp
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `DERIBIT_CLIENT_ID` | Your Deribit API Client ID | Required |
| `DERIBIT_CLIENT_SECRET` | Your Deribit API Client Secret | Required |
| `DERIBIT_BASE_URL` | Deribit REST API base URL | `https://test.deribit.com` |
| `DERIBIT_WS_URL` | Deribit WebSocket URL | `wss://test.deribit.com/ws/api/v2` |
| `DATABASE_PATH` | SQLite database file path | `deribit_data.db` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `LOG_FILE` | Log file path | `deribit_app.log` |

## Advanced Features

### Asynchronous Operations
- Uses `asyncio` and `websockets` for efficient concurrent operations
- Non-blocking database operations
- Automatic reconnection handling

### Error Handling
- Comprehensive try-catch blocks throughout the application
- Graceful handling of network interruptions
- Detailed error logging

### Database Utilities
- Query last N records
- Get data for specific instruments
- Database statistics and health checks
- Automatic table creation and indexing

### Logging
- Configurable log levels
- Both file and console logging
- Structured log messages with timestamps

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify your API credentials in the `.env` file
   - Ensure your Deribit test account is active
   - Check that API key has proper permissions

2. **No Instruments Found**
   - Check if there are active option instruments on the testnet
   - Verify your network connection
   - Review the instrument filtering logic in `fetch_instruments()`

3. **WebSocket Connection Issues**
   - Check your internet connection
   - Verify WebSocket URL in configuration
   - Review firewall settings

4. **Database Errors**
   - Ensure write permissions in the application directory
   - Check disk space availability
   - Verify SQLite installation

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file:

```env
LOG_LEVEL=DEBUG
```

This will provide detailed information about API requests, WebSocket messages, and database operations.

## API Rate Limits

Deribit has rate limits for API calls:
- REST API: 20 requests per second
- WebSocket: 50 messages per second

The application is designed to stay within these limits through:
- Efficient WebSocket subscriptions
- Minimal REST API calls
- Built-in connection management

## Security Considerations

- Never commit your `.env` file to version control
- Store API credentials securely
- Use test environment credentials only
- Monitor API usage to avoid rate limits

## Development and Extension

The modular architecture makes it easy to extend:

### Adding New Data Fields
1. Update the database schema in `database.py`
2. Modify the data processing in `deribit_client.py`
3. Update the callback function in `main.py`

### Supporting Additional Instruments
1. Modify the instrument filtering logic in `fetch_instruments()`
2. Add new subscription channels in WebSocket client
3. Update database schema if needed

### Adding New API Endpoints
1. Extend the `DeribitRestClient` class
2. Add new methods for additional endpoints
3. Implement proper error handling

---
