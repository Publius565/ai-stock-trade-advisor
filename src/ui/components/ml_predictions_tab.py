"""
ML Predictions Tab Component

Integrates backend ML components to display intelligent trade suggestions,
predictions, and risk analysis in the UI.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QComboBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QSpinBox
)
from PyQt6.QtCore import pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QColor

from src.ml_models.prediction_engine import PredictionEngine
from src.strategy.trade_suggestion_engine import TradeSuggestionEngine
from src.ml_models.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class MLPredictionsTab(QWidget):
    """ML Predictions tab component with integrated backend ML features."""
    
    # Signals
    activity_logged = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self, db_manager=None, market_data_manager=None, profile_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.market_data_manager = market_data_manager
        self.profile_manager = profile_manager
        self.current_user_uid = None
        
        # Initialize ML components
        try:
            self.prediction_engine = PredictionEngine()
            # Initialize TradeSuggestionEngine with proper dependencies
            if db_manager:
                from src.strategy.trading_engine import TradingEngine
                trading_engine = TradingEngine(db_manager)
                self.trade_suggestion_engine = TradeSuggestionEngine(
                    db_manager=db_manager, 
                    trading_engine=trading_engine
                )
            else:
                self.trade_suggestion_engine = TradeSuggestionEngine()
            self.feature_engineer = FeatureEngineer()
            logger.info("ML components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ML components: {e}")
            self.prediction_engine = None
            self.trade_suggestion_engine = None
            self.feature_engineer = None
        
        self.init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_predictions)
        self.refresh_timer.start(60000)  # Refresh every minute
    
    def init_ui(self):
        """Initialize the ML predictions tab UI."""
        layout = QVBoxLayout(self)
        
        # Controls Section
        controls_group = QGroupBox("ML Prediction Controls")
        controls_layout = QGridLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Symbol:"), 0, 0)
        self.symbol_input = QComboBox()
        self.symbol_input.setEditable(True)
        self.symbol_input.addItems(["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"])
        controls_layout.addWidget(self.symbol_input, 0, 1)
        
        controls_layout.addWidget(QLabel("Prediction Horizon:"), 0, 2)
        self.horizon_spin = QSpinBox()
        self.horizon_spin.setRange(1, 30)
        self.horizon_spin.setValue(5)
        self.horizon_spin.setSuffix(" days")
        controls_layout.addWidget(self.horizon_spin, 0, 3)
        
        self.predict_btn = QPushButton("Generate Prediction")
        self.predict_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        controls_layout.addWidget(self.predict_btn, 1, 0, 1, 2)
        
        self.suggestions_btn = QPushButton("Get Trade Suggestions")
        self.suggestions_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        controls_layout.addWidget(self.suggestions_btn, 1, 2, 1, 2)
        
        layout.addWidget(controls_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Predictions Display
        predictions_group = QGroupBox("ML Predictions & Analysis")
        predictions_layout = QVBoxLayout(predictions_group)
        
        # Prediction summary
        self.prediction_summary = QTextEdit()
        self.prediction_summary.setMaximumHeight(150)
        self.prediction_summary.setReadOnly(True)
        self.prediction_summary.setText("No predictions generated yet. Select a symbol and click 'Generate Prediction'.")
        predictions_layout.addWidget(self.prediction_summary)
        
        # Technical indicators summary
        indicators_group = QGroupBox("Technical Indicators Summary")
        self.indicators_display = QTextEdit()
        self.indicators_display.setMaximumHeight(120)
        self.indicators_display.setReadOnly(True)
        self.indicators_display.setText("Technical indicators will appear here after prediction.")
        indicators_group.setLayout(QVBoxLayout())
        indicators_group.layout().addWidget(self.indicators_display)
        predictions_layout.addWidget(indicators_group)
        
        layout.addWidget(predictions_group)
        
        # Trade Suggestions Table
        suggestions_group = QGroupBox("Intelligent Trade Suggestions")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        self.suggestions_table = QTableWidget()
        self.suggestions_table.setColumnCount(7)
        self.suggestions_table.setHorizontalHeaderLabels([
            "Type", "Action", "Confidence", "Expected Return", "Risk Level", 
            "Position Size", "Rationale"
        ])
        suggestions_layout.addWidget(self.suggestions_table)
        
        layout.addWidget(suggestions_group)
        
        # Model Performance Section
        performance_group = QGroupBox("Model Performance")
        performance_layout = QGridLayout(performance_group)
        
        # Model metrics
        metrics = ["Random Forest R²", "Gradient Boosting R²", "Linear Regression R²", 
                  "Avg Prediction Confidence", "Total Predictions", "Success Rate"]
        
        self.performance_labels = {}
        row, col = 0, 0
        for metric in metrics:
            label_key = QLabel(f"{metric}:")
            label_value = QLabel("N/A")
            label_value.setStyleSheet("font-weight: bold; color: #FF9800;")
            
            performance_layout.addWidget(label_key, row, col)
            performance_layout.addWidget(label_value, row, col + 1)
            
            self.performance_labels[metric] = label_value
            
            col += 2
            if col >= 4:
                col = 0
                row += 1
        
        layout.addWidget(performance_group)
        
        # Setup connections
        self.setup_connections()
        
        logger.info("ML Predictions tab initialized")
    
    def setup_connections(self):
        """Set up signal connections."""
        self.predict_btn.clicked.connect(self.generate_prediction)
        self.suggestions_btn.clicked.connect(self.generate_trade_suggestions)
    
    def set_market_data_manager(self, manager):
        """Set the market data manager."""
        self.market_data_manager = manager
    
    def set_profile_manager(self, manager):
        """Set the profile manager and re-initialize ML components if needed.""" 
        self.profile_manager = manager
        
        # Re-initialize ML components if db_manager is available but trade_suggestion_engine is not
        if manager and self.db_manager and not self.trade_suggestion_engine:
            try:
                from src.strategy.trading_engine import TradingEngine
                trading_engine = TradingEngine(self.db_manager, manager)
                self.trade_suggestion_engine = TradeSuggestionEngine(
                    db_manager=self.db_manager, 
                    trading_engine=trading_engine
                )
                logger.info("ML components re-initialized with profile manager")
            except Exception as e:
                logger.error(f"Failed to re-initialize ML components with profile manager: {e}")
    
    def set_db_manager(self, manager):
        """Set the database manager and re-initialize ML components."""
        self.db_manager = manager
        
        # Re-initialize ML components with proper dependencies
        if manager and not self.trade_suggestion_engine:
            try:
                from src.strategy.trading_engine import TradingEngine
                from src.strategy.signal_generator import SignalGenerator
                
                # Note: profile_manager will be set later via set_profile_manager
                if hasattr(self, 'profile_manager') and self.profile_manager:
                    trading_engine = TradingEngine(manager, self.profile_manager)
                    signal_generator = SignalGenerator(manager, trading_engine)
                    
                    self.trade_suggestion_engine = TradeSuggestionEngine(
                        db_manager=manager, 
                        trading_engine=trading_engine,
                        signal_generator=signal_generator
                    )
                    logger.info("ML components re-initialized with database manager and signal generator")
                else:
                    logger.warning("Profile manager not available for ML component initialization")
            except Exception as e:
                logger.error(f"Failed to re-initialize ML components: {e}")
    
    def set_current_user(self, user_uid: str):
        """Set the current user UID."""
        self.current_user_uid = user_uid
    
    def generate_prediction(self):
        """Generate ML prediction for selected symbol."""
        if not self.prediction_engine:
            self.prediction_summary.setText("❌ ML components not available")
            return
        
        symbol = self.symbol_input.currentText().upper()
        horizon = self.horizon_spin.value()
        
        if not symbol:
            self.prediction_summary.setText("⚠️ Please enter a valid symbol")
            return
        
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Get market data (simulated for POC)
            import pandas as pd
            import numpy as np
            
            # Create sample market data for demonstration
            dates = pd.date_range(start='2024-01-01', periods=252, freq='D')
            sample_data = pd.DataFrame({
                'date': dates,
                'open': np.random.normal(150, 10, 252),
                'high': np.random.normal(155, 10, 252),
                'low': np.random.normal(145, 10, 252),
                'close': np.random.normal(150, 10, 252),
                'volume': np.random.normal(1000000, 200000, 252)
            })
            
            # Generate prediction
            prediction = self.prediction_engine.generate_prediction(symbol, sample_data, horizon)
            
            # Display prediction summary
            self.display_prediction_summary(symbol, prediction)
            
            # Generate technical indicators summary
            self.display_technical_indicators(sample_data)
            
            # Update performance metrics
            self.update_performance_metrics()
            
            self.activity_logged.emit(f"Generated ML prediction for {symbol}")
            
        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            self.prediction_summary.setText(f"❌ Error generating prediction: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
    
    def generate_trade_suggestions(self):
        """Generate intelligent trade suggestions."""
        if not self.trade_suggestion_engine:
            self.suggestions_table.setRowCount(0)
            return
        
        symbol = self.symbol_input.currentText().upper()
        
        if not symbol:
            return
        
        try:
            # Get user risk profile
            user_profile = self.get_user_risk_profile()
            
            # Create sample market data
            import pandas as pd
            import numpy as np
            dates = pd.date_range(start='2024-01-01', periods=252, freq='D')
            sample_data = pd.DataFrame({
                'date': dates,
                'open': np.random.normal(150, 10, 252),
                'high': np.random.normal(155, 10, 252),
                'low': np.random.normal(145, 10, 252),
                'close': np.random.normal(150, 10, 252),
                'volume': np.random.normal(1000000, 200000, 252)
            })
            
            # Generate suggestions
            suggestions = self.trade_suggestion_engine.generate_suggestions(
                symbol, sample_data, user_profile
            )
            
            # Display suggestions in table
            self.display_trade_suggestions(suggestions)
            
            self.activity_logged.emit(f"Generated {len(suggestions)} trade suggestions for {symbol}")
            
        except Exception as e:
            logger.error(f"Error generating trade suggestions: {e}")
    
    def display_prediction_summary(self, symbol: str, prediction: Dict):
        """Display prediction summary in text widget."""
        try:
            # Safely extract values with defaults
            confidence = prediction.get('confidence', 0) or 0
            predicted_price = prediction.get('predicted_price', 0) or 0
            predicted_return = prediction.get('predicted_return', 0) or 0
            risk_assessment = prediction.get('risk_assessment', {}) or {}
            
            # Get model predictions with safe defaults
            model_predictions = prediction.get('model_predictions', {}) or {}
            rf_pred = model_predictions.get('random_forest', 'N/A')
            gb_pred = model_predictions.get('gradient_boosting', 'N/A')
            lr_pred = model_predictions.get('linear_regression', 'N/A')
            
            # Format model predictions safely
            def format_prediction(pred):
                if pred == 'N/A':
                    return 'N/A'
                try:
                    return f"{pred:.4f}"
                except (TypeError, ValueError):
                    return 'N/A'
            
            summary = f"""
🎯 ML Prediction for {symbol}

📈 Predicted Price: ${predicted_price:.2f}
📊 Expected Return: {predicted_return:.2%}
🎯 Confidence Score: {confidence:.1%}
⚡ Risk Level: {risk_assessment.get('risk_level', 'Unknown')}

🤖 Model Consensus:
• Random Forest: {format_prediction(rf_pred)}
• Gradient Boosting: {format_prediction(gb_pred)}
• Linear Regression: {format_prediction(lr_pred)}

⚠️ Risk Factors:
• Volatility: {risk_assessment.get('volatility_score', 'N/A')}
• Market Conditions: {risk_assessment.get('market_conditions', 'N/A')}
            """
            
            self.prediction_summary.setText(summary.strip())
            
        except Exception as e:
            logger.error(f"Error displaying prediction summary: {e}")
            self.prediction_summary.setText(f"Error displaying prediction: {str(e)}")
    
    def display_technical_indicators(self, market_data):
        """Display technical indicators summary."""
        try:
            if not self.feature_engineer:
                return
            
            # Generate technical indicators (POC with sample data)
            indicators_text = """
📊 Technical Indicators Analysis:

📈 Trend Indicators:
• SMA (20): Bullish crossover detected
• EMA (12): Above price, upward trend
• MACD: Signal line above histogram

⚡ Momentum Indicators:
• RSI (14): 67.3 (Neutral to Overbought)
• Stochastic: 73.2 (Overbought)
• Williams %R: -28.4 (Bullish)

🎯 Volatility Indicators:
• Bollinger Bands: Price near upper band
• ATR: Moderate volatility (2.3%)
• VIX: Low fear index (18.2)
            """
            
            self.indicators_display.setText(indicators_text.strip())
            
        except Exception as e:
            logger.error(f"Error displaying technical indicators: {e}")
    
    def display_trade_suggestions(self, suggestions: List[Dict]):
        """Display trade suggestions in table."""
        try:
            self.suggestions_table.setRowCount(len(suggestions))
            
            for row, suggestion in enumerate(suggestions):
                # Risk level color coding
                risk_level = suggestion.get('risk_level', 'medium')
                if risk_level == 'low':
                    color = QColor(76, 175, 80)  # Green
                elif risk_level == 'high':
                    color = QColor(244, 67, 54)  # Red
                else:
                    color = QColor(255, 152, 0)  # Orange
                
                items = [
                    suggestion.get('suggestion_type', 'N/A'),
                    suggestion.get('action', 'N/A'),
                    f"{suggestion.get('confidence', 0):.1%}",
                    f"{suggestion.get('expected_return', 0):.2%}",
                    suggestion.get('risk_level', 'N/A'),
                    f"{suggestion.get('position_size_pct', 0):.1%}",
                    suggestion.get('rationale', 'N/A')[:50] + "..."
                ]
                
                for col, item_text in enumerate(items):
                    item = QTableWidgetItem(str(item_text))
                    if col == 4:  # Risk level column
                        item.setBackground(color)
                    self.suggestions_table.setItem(row, col, item)
            
            # Auto-resize columns
            self.suggestions_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error displaying trade suggestions: {e}")
    
    def update_performance_metrics(self):
        """Update model performance metrics display."""
        try:
            # Sample performance metrics for POC
            metrics_data = {
                "Random Forest R²": "0.847",
                "Gradient Boosting R²": "0.823", 
                "Linear Regression R²": "0.651",
                "Avg Prediction Confidence": "73.2%",
                "Total Predictions": "1,247",
                "Success Rate": "68.4%"
            }
            
            for metric, value in metrics_data.items():
                if metric in self.performance_labels:
                    self.performance_labels[metric].setText(value)
                    
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def get_user_risk_profile(self) -> Dict:
        """Get current user risk profile."""
        try:
            if self.profile_manager and self.current_user_uid:
                profile = self.profile_manager.get_user_profile(self.current_user_uid)
                return profile.get('risk_profile', {})
            else:
                # Default risk profile for POC
                return {
                    'risk_tolerance': 'medium',
                    'max_position_pct': 0.1,
                    'stop_loss_pct': 0.05,
                    'take_profit_pct': 0.15
                }
        except Exception as e:
            logger.error(f"Error getting user risk profile: {e}")
            return {'risk_tolerance': 'medium'}
    
    def refresh_predictions(self):
        """Auto-refresh predictions if symbol is selected."""
        if self.symbol_input.currentText():
            self.activity_logged.emit("Auto-refreshing ML predictions...") 