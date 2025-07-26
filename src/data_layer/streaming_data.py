"""
Streaming Data Manager Module

Provides real-time data streaming capabilities for continuous market monitoring.
Handles WebSocket connections, data buffering, and real-time analytics.
"""

import logging
import threading
import time
import queue
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from .market_data import MarketDataManager

logger = logging.getLogger(__name__)


@dataclass
class StreamingDataPoint:
    """Data structure for streaming data points."""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    change: float
    change_percent: float
    source: str


class StreamingDataManager:
    """
    Real-time streaming data management system.
    
    Features:
    - Continuous data monitoring
    - Real-time price alerts
    - Data buffering and aggregation
    - WebSocket connection management
    - Streaming analytics
    """
    
    def __init__(self, market_data_manager: MarketDataManager, buffer_size: int = 1000):
        """
        Initialize the streaming data manager.
        
        Args:
            market_data_manager: Market data manager instance
            buffer_size: Size of data buffer
        """
        self.market_data_manager = market_data_manager
        self.buffer_size = buffer_size
        
        # Data buffers
        self.data_buffer = queue.Queue(maxsize=buffer_size)
        self.alert_buffer = queue.Queue(maxsize=100)
        
        # Streaming state
        self.is_streaming = False
        self.streaming_symbols = set()
        
        # Threading
        self._stream_thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # Callbacks
        self.data_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        # Price alerts
        self.price_alerts: Dict[str, Dict[str, float]] = {}
        
        # Statistics
        self.stats = {
            'data_points_received': 0,
            'alerts_triggered': 0,
            'buffer_overflows': 0,
            'last_update': None
        }
        
        logger.info("Streaming data manager initialized")
    
    def start_streaming(self, symbols: List[str], interval_seconds: int = 30):
        """
        Start real-time data streaming for specified symbols.
        
        Args:
            symbols: List of symbols to stream
            interval_seconds: Update interval in seconds
        """
        with self._lock:
            if self.is_streaming:
                logger.warning("Streaming already active")
                return
            
            self.streaming_symbols = set(symbols)
            self.is_streaming = True
            self._stop_event.clear()
            
            # Start streaming thread
            self._stream_thread = threading.Thread(
                target=self._streaming_loop,
                args=(interval_seconds,),
                daemon=True
            )
            self._stream_thread.start()
            
            logger.info(f"Started streaming for {len(symbols)} symbols, interval: {interval_seconds}s")
    
    def stop_streaming(self):
        """Stop real-time data streaming."""
        with self._lock:
            if not self.is_streaming:
                return
            
            self.is_streaming = False
            self._stop_event.set()
            
            if self._stream_thread and self._stream_thread.is_alive():
                self._stream_thread.join(timeout=5)
            
            logger.info("Stopped streaming")
    
    def _streaming_loop(self, interval_seconds: int):
        """Main streaming loop."""
        while not self._stop_event.is_set():
            try:
                # Get latest data for all streaming symbols
                symbols_list = list(self.streaming_symbols)
                if symbols_list:
                    latest_data = self.market_data_manager.get_multiple_symbols(
                        symbols_list, force_refresh=True
                    )
                    
                    # Process each symbol's data
                    for symbol, data in latest_data.items():
                        if data and data.get('data'):
                            # Get the most recent data point
                            latest_point = data['data'][-1]
                            
                            # Create streaming data point
                            streaming_point = self._create_streaming_point(symbol, latest_point, data['source'])
                            
                            # Add to buffer
                            try:
                                self.data_buffer.put_nowait(streaming_point)
                                self.stats['data_points_received'] += 1
                            except queue.Full:
                                self.stats['buffer_overflows'] += 1
                                logger.warning("Data buffer overflow")
                            
                            # Check price alerts
                            self._check_price_alerts(streaming_point)
                            
                            # Notify callbacks
                            self._notify_data_callbacks(streaming_point)
                
                self.stats['last_update'] = datetime.now().isoformat()
                
                # Wait for next update
                self._stop_event.wait(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}")
                self._stop_event.wait(60)  # Wait 1 minute on error
    
    def _create_streaming_point(self, symbol: str, data_point: Dict[str, Any], source: str) -> StreamingDataPoint:
        """Create a streaming data point from market data."""
        current_price = data_point['close']
        
        # Calculate price change (would need previous price for accurate calculation)
        # For now, we'll use a placeholder
        change = 0.0
        change_percent = 0.0
        
        return StreamingDataPoint(
            symbol=symbol,
            timestamp=datetime.strptime(data_point['date'], '%Y-%m-%d'),
            price=current_price,
            volume=data_point['volume'],
            change=change,
            change_percent=change_percent,
            source=source
        )
    
    def _check_price_alerts(self, data_point: StreamingDataPoint):
        """Check if price alerts should be triggered."""
        symbol = data_point.symbol
        current_price = data_point.price
        
        if symbol not in self.price_alerts:
            return
        
        alerts = self.price_alerts[symbol]
        triggered_alerts = []
        
        for alert_type, threshold in alerts.items():
            if alert_type == 'above' and current_price > threshold:
                triggered_alerts.append(f"Price above ${threshold:.2f}")
            elif alert_type == 'below' and current_price < threshold:
                triggered_alerts.append(f"Price below ${threshold:.2f}")
        
        if triggered_alerts:
            alert_data = {
                'symbol': symbol,
                'current_price': current_price,
                'timestamp': data_point.timestamp,
                'alerts': triggered_alerts
            }
            
            try:
                self.alert_buffer.put_nowait(alert_data)
                self.stats['alerts_triggered'] += 1
                
                # Notify alert callbacks
                self._notify_alert_callbacks(alert_data)
                
            except queue.Full:
                logger.warning("Alert buffer overflow")
    
    def _notify_data_callbacks(self, data_point: StreamingDataPoint):
        """Notify data callbacks with new streaming data."""
        for callback in self.data_callbacks:
            try:
                callback(data_point)
            except Exception as e:
                logger.error(f"Error in data callback: {e}")
    
    def _notify_alert_callbacks(self, alert_data: Dict[str, Any]):
        """Notify alert callbacks with triggered alerts."""
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def add_price_alert(self, symbol: str, alert_type: str, threshold: float):
        """
        Add a price alert for a symbol.
        
        Args:
            symbol: Stock symbol
            alert_type: 'above' or 'below'
            threshold: Price threshold
        """
        symbol = symbol.upper()
        
        if symbol not in self.price_alerts:
            self.price_alerts[symbol] = {}
        
        self.price_alerts[symbol][alert_type] = threshold
        logger.info(f"Added {alert_type} alert for {symbol} at ${threshold:.2f}")
    
    def remove_price_alert(self, symbol: str, alert_type: str):
        """
        Remove a price alert for a symbol.
        
        Args:
            symbol: Stock symbol
            alert_type: 'above' or 'below'
        """
        symbol = symbol.upper()
        
        if symbol in self.price_alerts and alert_type in self.price_alerts[symbol]:
            del self.price_alerts[symbol][alert_type]
            
            if not self.price_alerts[symbol]:
                del self.price_alerts[symbol]
            
            logger.info(f"Removed {alert_type} alert for {symbol}")
    
    def get_price_alerts(self) -> Dict[str, Dict[str, float]]:
        """Get all current price alerts."""
        return self.price_alerts.copy()
    
    def add_data_callback(self, callback: Callable[[StreamingDataPoint], None]):
        """Add a callback for streaming data updates."""
        self.data_callbacks.append(callback)
        logger.debug("Added data callback")
    
    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback for price alerts."""
        self.alert_callbacks.append(callback)
        logger.debug("Added alert callback")
    
    def get_latest_data(self, symbol: str) -> Optional[StreamingDataPoint]:
        """
        Get the latest streaming data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest streaming data point or None
        """
        # This would need to be implemented with a more sophisticated buffer
        # For now, we'll return None as this is a simplified implementation
        return None
    
    def get_data_buffer(self, max_points: int = 100) -> List[StreamingDataPoint]:
        """
        Get recent data from the buffer.
        
        Args:
            max_points: Maximum number of points to return
            
        Returns:
            List of recent streaming data points
        """
        data_points = []
        
        while not self.data_buffer.empty() and len(data_points) < max_points:
            try:
                point = self.data_buffer.get_nowait()
                data_points.append(point)
            except queue.Empty:
                break
        
        return data_points
    
    def get_alert_buffer(self) -> List[Dict[str, Any]]:
        """
        Get recent alerts from the alert buffer.
        
        Returns:
            List of recent alert data
        """
        alerts = []
        
        while not self.alert_buffer.empty():
            try:
                alert = self.alert_buffer.get_nowait()
                alerts.append(alert)
            except queue.Empty:
                break
        
        return alerts
    
    def clear_buffers(self):
        """Clear all data and alert buffers."""
        while not self.data_buffer.empty():
            try:
                self.data_buffer.get_nowait()
            except queue.Empty:
                break
        
        while not self.alert_buffer.empty():
            try:
                self.alert_buffer.get_nowait()
            except queue.Empty:
                break
        
        logger.info("Cleared all buffers")
    
    def get_streaming_stats(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        return {
            'is_streaming': self.is_streaming,
            'streaming_symbols': list(self.streaming_symbols),
            'data_points_received': self.stats['data_points_received'],
            'alerts_triggered': self.stats['alerts_triggered'],
            'buffer_overflows': self.stats['buffer_overflows'],
            'last_update': self.stats['last_update'],
            'data_buffer_size': self.data_buffer.qsize(),
            'alert_buffer_size': self.alert_buffer.qsize(),
            'active_price_alerts': len(self.price_alerts)
        }
    
    def add_symbol_to_streaming(self, symbol: str):
        """Add a symbol to the streaming list."""
        symbol = symbol.upper()
        
        with self._lock:
            self.streaming_symbols.add(symbol)
            logger.info(f"Added {symbol} to streaming")
    
    def remove_symbol_from_streaming(self, symbol: str):
        """Remove a symbol from the streaming list."""
        symbol = symbol.upper()
        
        with self._lock:
            if symbol in self.streaming_symbols:
                self.streaming_symbols.remove(symbol)
                logger.info(f"Removed {symbol} from streaming")
    
    def shutdown(self):
        """Shutdown the streaming data manager."""
        self.stop_streaming()
        self.clear_buffers()
        logger.info("Streaming data manager shutdown complete") 