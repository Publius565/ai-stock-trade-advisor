"""
Alpaca Integration Validation Script
Part of Phase 4B: Broker Integration validation
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.execution.alpaca_broker import AlpacaBroker
from src.execution.trading_types import TradeOrder, OrderType, OrderStatus
from config.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL


def validate_alpaca_integration():
    """Validate Alpaca integration with real API calls"""
    print("=== Alpaca Integration Validation ===")
    print(f"API Key: {'*' * 10 if ALPACA_API_KEY else 'NOT SET'}")
    print(f"Secret Key: {'*' * 10 if ALPACA_SECRET_KEY else 'NOT SET'}")
    print(f"Base URL: {ALPACA_BASE_URL}")
    print()
    
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        print("❌ Alpaca API credentials not configured")
        print("Please set ALPACA_API_KEY and ALPACA_SECRET_KEY in your environment or .env file")
        return False
    
    try:
        # Initialize Alpaca broker
        print("🔌 Initializing Alpaca broker...")
        broker = AlpacaBroker(
            api_key=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY,
            base_url=ALPACA_BASE_URL,
            paper_trading=True
        )
        
        if not broker.is_connected():
            print("❌ Failed to connect to Alpaca API")
            return False
        
        print("✅ Successfully connected to Alpaca API")
        
        # Get account information
        print("\n📊 Getting account information...")
        account_info = broker.get_account_info()
        if account_info:
            print(f"✅ Account ID: {account_info['account_id']}")
            print(f"✅ Status: {account_info['status']}")
            print(f"✅ Buying Power: ${account_info['buying_power']:,.2f}")
            print(f"✅ Cash: ${account_info['cash']:,.2f}")
            print(f"✅ Portfolio Value: ${account_info['portfolio_value']:,.2f}")
        else:
            print("❌ Failed to get account information")
            return False
        
        # Get current positions
        print("\n📈 Getting current positions...")
        positions = broker.get_positions()
        if positions:
            print(f"✅ Found {len(positions)} positions:")
            for pos in positions:
                print(f"   - {pos['symbol']}: {pos['qty']} shares @ ${pos['avg_entry_price']:.2f}")
        else:
            print("✅ No current positions")
        
        # Test market data retrieval
        print("\n📊 Testing market data retrieval...")
        test_symbol = "AAPL"
        market_data = broker.get_market_data(test_symbol)
        if market_data:
            print(f"✅ {test_symbol} market data retrieved:")
            print(f"   - Price: ${market_data['price']:.2f}")
            print(f"   - Volume: {market_data['volume']:,}")
            print(f"   - Bid: ${market_data['bid']:.2f}" if market_data['bid'] else "   - Bid: N/A")
            print(f"   - Ask: ${market_data['ask']:.2f}" if market_data['ask'] else "   - Ask: N/A")
        else:
            print(f"❌ Failed to get market data for {test_symbol}")
            return False
        
        # Test order creation (without placing)
        print("\n📝 Testing order creation...")
        test_order = TradeOrder(
            uid="test-order-123",
            user_id=1,
            symbol="AAPL",
            order_type=OrderType.MARKET,
            quantity=1,  # Just 1 share for testing
            price=150.00
        )
        
        print(f"✅ Test order created:")
        print(f"   - Symbol: {test_order.symbol}")
        print(f"   - Type: {test_order.order_type.value}")
        print(f"   - Quantity: {test_order.quantity}")
        print(f"   - Price: ${test_order.price:.2f}")
        
        print("\n⚠️  Note: Order placement is disabled for safety")
        print("   To test real order placement, modify this script")
        
        print("\n🎉 Alpaca integration validation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return False


if __name__ == "__main__":
    success = validate_alpaca_integration()
    sys.exit(0 if success else 1) 