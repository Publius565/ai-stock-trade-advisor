# AI-Driven Stock Trade Advisor - UI Guide

## Quick Start

The application now has a simple UI that allows you to test all the core functionality with a test user.

### Running the Application

1. **Launch the UI:**
   ```bash
   python run_ui.py
   ```

2. **Test the UI Components:**
   ```bash
   python test_ui_simple.py
   ```

## UI Features

The application provides a tabbed interface with the following sections:

### 1. User Profile Tab
- **Create Profile**: Set up a new test user with username, email, and risk profile
- **Load Profile**: Load an existing user profile
- **Update Profile**: Modify user information and risk assessment
- **Risk Assessment**: Configure investment timeline, risk tolerance, experience level, and goals

### 2. Market Scanner Tab
- **Top Movers Scan**: View the top gainers and losers in the market
- **Intelligent Suggestions**: Get personalized symbol suggestions based on your risk profile
- **Real-time Data**: View current prices, volume, and sector information

### 3. Watchlist Tab
- **Create Watchlist**: Set up a personal watchlist for tracking specific symbols
- **Add Symbols**: Add stocks to your watchlist with priority and notes
- **Manage Symbols**: View and remove symbols from your watchlist

### 4. Dashboard Tab
- **Quick Statistics**: View scan counts, symbols tracked, and watchlist information
- **Recent Activity**: Monitor application activity and user actions
- **Quick Actions**: Perform common tasks like quick market scans

## Testing Workflow

### Step 1: Create a Test User
1. Go to the "User Profile" tab
2. Enter a username (e.g., "test_user")
3. Enter an email (e.g., "test@example.com")
4. Select a risk profile (conservative, moderate, or aggressive)
5. Click "Create Profile"

### Step 2: Configure Risk Assessment
1. In the "Risk Assessment" section, set your preferences:
   - Investment Timeline: short, medium, or long
   - Risk Tolerance: low, medium, or high
   - Experience Level: beginner, intermediate, or expert
   - Investment Goals: conservative, balanced, or aggressive
2. Click "Update Risk Assessment"

### Step 3: Test Market Scanning
1. Go to the "Market Scanner" tab
2. Select "Top Movers" or "Intelligent Suggestions"
3. Set the limit (number of symbols to scan)
4. Click "Start Scan"
5. View results in the table below

### Step 4: Create a Watchlist
1. Go to the "Watchlist" tab
2. Enter a watchlist name and description
3. Click "Create Watchlist"
4. Add symbols like "AAPL", "MSFT", "GOOGL"
5. Set priority and add notes
6. Click "Add Symbol"

### Step 5: Monitor Dashboard
1. Go to the "Dashboard" tab
2. View your statistics and recent activity
3. Use quick actions for common tasks

## Features Tested

The UI allows you to test all the core systems we've built:

- ✅ **User Profile Management**: Create, load, and update user profiles
- ✅ **Risk Assessment**: Configure personalized risk preferences
- ✅ **Market Scanning**: Top movers and intelligent symbol suggestions
- ✅ **Watchlist Management**: Create and manage personal watchlists
- ✅ **Database Integration**: All data is stored and retrieved from SQLite
- ✅ **API Integration**: Real-time market data from Yahoo Finance
- ✅ **Background Processing**: Market scans run in background threads

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed:
   ```bash
   pip install PyQt6 pandas numpy requests python-dotenv yfinance
   ```

2. **Database Errors**: The application will create the database automatically. If you get database errors, check that the `data/` directory exists.

3. **API Errors**: The application uses Yahoo Finance API which doesn't require an API key. If you see API warnings, they're normal and the app will still work.

4. **UI Not Responding**: Market scans run in the background. The UI will show a progress bar during scans.

### Logs

Check the `logs/ui.log` file for detailed error information if you encounter issues.

## Next Steps

Once you've tested the UI and confirmed everything works:

1. **Phase 3**: We can move on to implementing the trading engine
2. **Enhanced UI**: Add charts, real-time updates, and more advanced features
3. **Backtesting**: Implement strategy testing and validation
4. **Paper Trading**: Add simulated trading capabilities

## Technical Details

- **Framework**: PyQt6 for the desktop UI
- **Database**: SQLite with optimized schema
- **APIs**: Yahoo Finance for market data
- **Architecture**: Modular design with separate components for profiles, scanning, and UI
- **Threading**: Background workers for non-blocking operations

The UI provides a solid foundation for testing and demonstrates all the core functionality we've built so far. 