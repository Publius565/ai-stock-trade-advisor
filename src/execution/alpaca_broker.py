"""
Alpaca Broker Interface - Real broker integration for paper trading
Part of Phase 4B: Broker Integration implementation
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockLatestTradeRequest
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from ..utils.database_manager import DatabaseManager
from .trading_types import TradeOrder, OrderType, OrderStatus





class AlpacaBroker:
    """Alpaca broker interface for real paper trading"""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str, paper_trading: bool = True):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.paper_trading = paper_trading
        
        # Initialize Alpaca API clients
        self.trading_client = TradingClient(api_key, secret_key, paper=paper_trading)
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
        
        # Connection status
        self.connected = False
        self.account_info = None
        
        # Initialize connection
        self._connect()
    
    def _connect(self) -> bool:
        """Establish connection to Alpaca API"""
        try:
            # Test connection by getting account info
            self.account_info = self.trading_client.get_account()
            self.connected = True
            self.logger.info(f"Connected to Alpaca {'Paper Trading' if self.paper_trading else 'Live Trading'}")
            self.logger.info(f"Account Status: {self.account_info.status}")
            self.logger.info(f"Buying Power: ${float(self.account_info.buying_power):,.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Alpaca API: {e}")
            self.connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to Alpaca API"""
        return self.connected
    
    def get_account_info(self) -> Optional[Dict]:
        """Get current account information"""
        if not self.connected:
            return None
            
        try:
            account = self.trading_client.get_account()
            return {
                'account_id': account.id,
                'status': account.status.value,
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity),
                'daytrade_count': account.daytrade_count,
                'pattern_day_trader': account.pattern_day_trader
            }
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None
    
    def place_order(self, order: TradeOrder) -> bool:
        """Place an order with Alpaca"""
        if not self.connected:
            self.logger.error("Not connected to Alpaca API")
            return False
            
        try:
            # Convert our order type to Alpaca format
            side = OrderSide.BUY if order.quantity > 0 else OrderSide.SELL
            qty = abs(order.quantity)
            
            # Create order request based on type
            if order.order_type == OrderType.MARKET:
                order_request = MarketOrderRequest(
                    symbol=order.symbol,
                    qty=qty,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    client_order_id=order.uid
                )
            elif order.order_type == OrderType.LIMIT:
                order_request = LimitOrderRequest(
                    symbol=order.symbol,
                    qty=qty,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    limit_price=order.limit_price,
                    client_order_id=order.uid
                )
            elif order.order_type == OrderType.STOP:
                order_request = StopOrderRequest(
                    symbol=order.symbol,
                    qty=qty,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    stop_price=order.stop_price,
                    client_order_id=order.uid
                )
            elif order.order_type == OrderType.STOP_LIMIT:
                order_request = StopLimitOrderRequest(
                    symbol=order.symbol,
                    qty=qty,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    limit_price=order.limit_price,
                    stop_price=order.stop_price,
                    client_order_id=order.uid
                )
            else:
                self.logger.error(f"Unsupported order type: {order.order_type}")
                return False
            
            self.logger.info(f"Placing Alpaca order: {order.symbol} {side.value} {qty}")
            
            # Submit order to Alpaca
            alpaca_order = self.trading_client.submit_order(order_request)
            
            # Update our order with Alpaca response
            order.status = self._map_alpaca_status(alpaca_order.status.value)
            if alpaca_order.filled_at:
                order.filled_at = alpaca_order.filled_at.replace(tzinfo=timezone.utc)
            if alpaca_order.filled_qty:
                order.filled_quantity = int(alpaca_order.filled_qty)
            if alpaca_order.filled_avg_price:
                order.filled_price = float(alpaca_order.filled_avg_price)
            
            self.logger.info(f"Alpaca order placed successfully: {alpaca_order.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error placing Alpaca order: {e}")
            order.status = OrderStatus.REJECTED
            return False
    
    def cancel_order(self, order_uid: str) -> bool:
        """Cancel an existing order"""
        if not self.connected:
            return False
            
        try:
            self.logger.info(f"Cancelling Alpaca order: {order_uid}")
            self.trading_client.cancel_order_by_id(order_uid)
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_uid}: {e}")
            return False
    
    def get_order_status(self, order_uid: str) -> Optional[OrderStatus]:
        """Get current status of an order"""
        if not self.connected:
            return None
            
        try:
            alpaca_order = self.trading_client.get_order_by_id(order_uid)
            return self._map_alpaca_status(alpaca_order.status.value)
        except Exception as e:
            self.logger.error(f"Error getting order status for {order_uid}: {e}")
            return None
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        if not self.connected:
            return []
            
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    'symbol': pos.symbol,
                    'qty': int(pos.qty),
                    'avg_entry_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price),
                    'market_value': float(pos.market_value),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'unrealized_plpc': float(pos.unrealized_plpc)
                }
                for pos in positions
            ]
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Get current market data for a symbol"""
        if not self.connected:
            return None
            
        try:
            # Get latest trade
            trade_request = StockLatestTradeRequest(symbol_or_symbols=symbol)
            latest_trade = self.data_client.get_stock_latest_trade(trade_request)
            
            # Get latest quote
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            latest_quote = self.data_client.get_stock_latest_quote(quote_request)
            
            trade_data = latest_trade[symbol]
            quote_data = latest_quote[symbol]
            
            return {
                'symbol': symbol,
                'price': float(trade_data.price),
                'volume': int(trade_data.size),
                'timestamp': trade_data.timestamp,
                'bid': float(quote_data.bid_price) if quote_data.bid_price else None,
                'ask': float(quote_data.ask_price) if quote_data.ask_price else None,
                'bid_size': int(quote_data.bid_size) if quote_data.bid_size else None,
                'ask_size': int(quote_data.ask_size) if quote_data.ask_size else None
            }
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def _map_alpaca_status(self, alpaca_status: str) -> OrderStatus:
        """Map Alpaca order status to our OrderStatus enum"""
        mapping = {
            'new': OrderStatus.PENDING,
            'pending_new': OrderStatus.PENDING,
            'accepted': OrderStatus.PENDING,
            'accepted_for_bidding': OrderStatus.PENDING,
            'partial': OrderStatus.PARTIALLY_FILLED,
            'filled': OrderStatus.FILLED,
            'canceled': OrderStatus.CANCELLED,
            'pending_cancel': OrderStatus.PENDING,
            'rejected': OrderStatus.REJECTED,
            'expired': OrderStatus.CANCELLED
        }
        return mapping.get(alpaca_status.lower(), OrderStatus.PENDING)
    
    def close_connection(self):
        """Close connection to Alpaca API"""
        try:
            self.connected = False
            self.logger.info("Alpaca connection closed")
        except Exception as e:
            self.logger.error(f"Error closing Alpaca connection: {e}") 