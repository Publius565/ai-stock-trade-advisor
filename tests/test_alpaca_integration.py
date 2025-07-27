"""
Test Alpaca Broker Integration
Part of Phase 4B: Broker Integration testing
"""

import pytest
import unittest.mock as mock
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.execution.alpaca_broker import AlpacaBroker
from src.execution.trade_executor import TradeExecutor
from src.execution.trading_types import TradeOrder, OrderType, OrderStatus
from src.strategy.trading_engine import TradingSignal, SignalType
from src.utils.database_manager import DatabaseManager
from src.profile.profile_manager import ProfileManager


class TestAlpacaBroker:
    """Test Alpaca broker functionality"""
    
    @pytest.fixture
    def mock_alpaca_api(self):
        """Mock Alpaca API responses"""
        with patch('src.execution.alpaca_broker.TradingClient') as mock_trading_client, \
             patch('src.execution.alpaca_broker.StockHistoricalDataClient') as mock_data_client:
            
            # Mock account info
            mock_account = Mock()
            mock_account.id = "test-account-id"
            mock_account.status.value = "ACTIVE"
            mock_account.buying_power = "100000.00"
            mock_account.cash = "50000.00"
            mock_account.portfolio_value = "100000.00"
            mock_account.equity = "100000.00"
            mock_account.daytrade_count = 0
            mock_account.pattern_day_trader = False
            
            mock_trading_client.return_value.get_account.return_value = mock_account
            
            # Mock order submission
            mock_order = Mock()
            mock_order.id = "test-order-id"
            mock_order.status.value = "filled"
            mock_order.filled_at = datetime.now(timezone.utc)
            mock_order.filled_qty = 100
            mock_order.filled_avg_price = 150.50
            
            mock_trading_client.return_value.submit_order.return_value = mock_order
            
            yield mock_trading_client
    
    @pytest.fixture
    def alpaca_broker(self, mock_alpaca_api):
        """Create Alpaca broker instance with mocked API"""
        return AlpacaBroker(
            api_key="test-key",
            secret_key="test-secret",
            base_url="https://paper-api.alpaca.markets",
            paper_trading=True
        )
    
    def test_alpaca_broker_initialization(self, alpaca_broker):
        """Test Alpaca broker initialization"""
        assert alpaca_broker.api_key == "test-key"
        assert alpaca_broker.secret_key == "test-secret"
        assert alpaca_broker.base_url == "https://paper-api.alpaca.markets"
        assert alpaca_broker.paper_trading is True
        assert alpaca_broker.is_connected() is True
    
    def test_get_account_info(self, alpaca_broker):
        """Test getting account information"""
        account_info = alpaca_broker.get_account_info()
        
        assert account_info is not None
        assert account_info['account_id'] == "test-account-id"
        assert account_info['status'] == "ACTIVE"
        assert account_info['buying_power'] == 100000.00
        assert account_info['cash'] == 50000.00
        assert account_info['portfolio_value'] == 100000.00
    
    def test_place_market_order(self, alpaca_broker):
        """Test placing a market order"""
        order = TradeOrder(
            uid="test-order-123",
            user_id=1,
            symbol="AAPL",
            order_type=OrderType.MARKET,
            quantity=100,
            price=150.00
        )
        
        success = alpaca_broker.place_order(order)
        
        assert success is True
        assert order.status == OrderStatus.FILLED
        assert order.filled_quantity == 100
        assert order.filled_price == 150.50
    
    def test_place_limit_order(self, alpaca_broker):
        """Test placing a limit order"""
        order = TradeOrder(
            uid="test-order-124",
            user_id=1,
            symbol="AAPL",
            order_type=OrderType.LIMIT,
            quantity=100,
            price=150.00,
            limit_price=145.00
        )
        
        success = alpaca_broker.place_order(order)
        
        assert success is True
        assert order.status == OrderStatus.FILLED
    

    
    def test_status_mapping(self, alpaca_broker):
        """Test status mapping"""
        assert alpaca_broker._map_alpaca_status("filled") == OrderStatus.FILLED
        assert alpaca_broker._map_alpaca_status("partial") == OrderStatus.PARTIALLY_FILLED
        assert alpaca_broker._map_alpaca_status("canceled") == OrderStatus.CANCELLED
        assert alpaca_broker._map_alpaca_status("rejected") == OrderStatus.REJECTED
        assert alpaca_broker._map_alpaca_status("new") == OrderStatus.PENDING
    
    def test_get_positions(self, alpaca_broker, mock_alpaca_api):
        """Test getting positions"""
        # Mock position data
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.qty = 100
        mock_position.avg_entry_price = 150.00
        mock_position.current_price = 155.00
        mock_position.market_value = 15500.00
        mock_position.unrealized_pl = 500.00
        mock_position.unrealized_plpc = 0.033
        
        mock_alpaca_api.return_value.get_all_positions.return_value = [mock_position]
        
        positions = alpaca_broker.get_positions()
        
        assert len(positions) == 1
        assert positions[0]['symbol'] == "AAPL"
        assert positions[0]['qty'] == 100
        assert positions[0]['avg_entry_price'] == 150.00
        assert positions[0]['current_price'] == 155.00
    
    def test_get_market_data(self, alpaca_broker, mock_alpaca_api):
        """Test getting market data"""
        # Mock trade data
        mock_trade = Mock()
        mock_trade.price = 155.00
        mock_trade.size = 1000
        mock_trade.timestamp = datetime.now(timezone.utc)
        
        # Mock quote data
        mock_quote = Mock()
        mock_quote.bid_price = 154.95
        mock_quote.ask_price = 155.05
        mock_quote.bid_size = 500
        mock_quote.ask_size = 500
        
        # Mock the data client methods
        with patch.object(alpaca_broker, 'data_client') as mock_data_client:
            mock_data_client.get_stock_latest_trade.return_value = {"AAPL": mock_trade}
            mock_data_client.get_stock_latest_quote.return_value = {"AAPL": mock_quote}
            
            market_data = alpaca_broker.get_market_data("AAPL")
            
            assert market_data is not None
            assert market_data['symbol'] == "AAPL"
            assert market_data['price'] == 155.00
            assert market_data['volume'] == 1000
            assert market_data['bid'] == 154.95
            assert market_data['ask'] == 155.05


class TestTradeExecutorAlpacaIntegration:
    """Test TradeExecutor with Alpaca integration"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager"""
        return Mock(spec=DatabaseManager)
    
    @pytest.fixture
    def mock_profile_manager(self):
        """Mock profile manager"""
        profile_manager = Mock(spec=ProfileManager)
        profile_manager.get_user_profile.return_value = {
            'max_position_pct': 0.1,
            'risk_tolerance': 'medium'
        }
        return profile_manager
    
    @pytest.fixture
    def trade_executor(self, mock_db_manager, mock_profile_manager):
        """Create TradeExecutor instance"""
        return TradeExecutor(mock_db_manager, mock_profile_manager)
    
    @patch('src.execution.trade_executor.AlpacaBroker')
    def test_initialize_alpaca_broker(self, mock_alpaca_broker, trade_executor):
        """Test Alpaca broker initialization in TradeExecutor"""
        # Mock successful connection
        mock_broker_instance = Mock()
        mock_broker_instance.is_connected.return_value = True
        mock_alpaca_broker.return_value = mock_broker_instance
        
        # Mock config
        with patch('config.config.ALPACA_API_KEY', 'test-key'), \
             patch('config.config.ALPACA_SECRET_KEY', 'test-secret'), \
             patch('config.config.ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'):
            
            trade_executor.enable_execution(enabled=True, paper_trading=True, use_alpaca=True)
            
            assert trade_executor.broker is not None
            assert isinstance(trade_executor.broker, Mock)
            mock_alpaca_broker.assert_called_once()
    
    @patch('src.execution.trade_executor.AlpacaBroker')
    def test_fallback_to_mock_broker(self, mock_alpaca_broker, trade_executor):
        """Test fallback to MockBroker when Alpaca fails"""
        # Mock failed connection
        mock_broker_instance = Mock()
        mock_broker_instance.is_connected.return_value = False
        mock_alpaca_broker.return_value = mock_broker_instance
        
        # Mock config
        with patch('config.config.ALPACA_API_KEY', 'test-key'), \
             patch('config.config.ALPACA_SECRET_KEY', 'test-secret'), \
             patch('config.config.ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'):
            
            trade_executor.enable_execution(enabled=True, paper_trading=True, use_alpaca=True)
            
            # Should fall back to MockBroker
            assert trade_executor.broker is not None
            assert hasattr(trade_executor.broker, 'commission_rate')  # MockBroker attribute
    
    def test_get_broker_info_alpaca(self, trade_executor):
        """Test getting broker info for Alpaca"""
        # Mock Alpaca broker
        mock_broker = Mock()
        mock_broker.get_account_info.return_value = {
            'account_id': 'test-id',
            'buying_power': 100000.00
        }
        mock_broker.is_connected.return_value = True
        mock_broker.paper_trading = True
        
        trade_executor.broker = mock_broker
        
        # Mock isinstance check
        with patch('src.execution.trade_executor.isinstance', return_value=True):
            broker_info = trade_executor.get_broker_info()
            
            assert broker_info['type'] == 'alpaca'
            assert broker_info['connected'] is True
            assert broker_info['paper_trading'] is True
            assert broker_info['account_info'] is not None
    
    def test_get_broker_info_mock(self, trade_executor):
        """Test getting broker info for MockBroker"""
        # Mock broker (not Alpaca)
        mock_broker = Mock()
        mock_broker.commission_rate = 0.005  # MockBroker attribute
        
        trade_executor.broker = mock_broker
        
        # Mock isinstance check to return False (not Alpaca)
        with patch('src.execution.trade_executor.isinstance', return_value=False):
            broker_info = trade_executor.get_broker_info()
            
            assert broker_info['type'] == 'mock'
            assert broker_info['connected'] is True
            assert broker_info['status'] == 'simulation_mode'
    
    def test_get_broker_info_none(self, trade_executor):
        """Test getting broker info when no broker is initialized"""
        trade_executor.broker = None
        
        broker_info = trade_executor.get_broker_info()
        
        assert broker_info['type'] == 'none'
        assert broker_info['connected'] is False
        assert broker_info['status'] == 'not_initialized'





if __name__ == "__main__":
    pytest.main([__file__]) 