# AI-Driven Stock Trade Advisor

A comprehensive Windows-based desktop application that provides personalized stock trading recommendations using a combination of rule-based logic and machine learning.

## 📁 Source Code Repository

**GitHub Repository**: [https://github.com/Publius565/ai-stock-trade-advisor](https://github.com/Publius565/ai-stock-trade-advisor)

- **Repository Type**: Private
- **Branch**: master
- **Last Updated**: 2025-07-26
- **Status**: Active Development

### Repository Structure
```
ai-stock-trade-advisor/
├── config/           # Configuration files and API keys
├── data/            # Local data storage
├── docs/            # Project documentation
├── docker/          # Docker configuration
├── models/          # ML models and rule configurations
├── scripts/         # Utility scripts
├── src/             # Main source code
├── tests/           # Unit and integration tests
└── venv/            # Python virtual environment
```

## 🚀 Features

- **Personalized Risk Profiling**: Custom risk assessment and investment goal tracking
- **Dual-Tier Recommendations**: High-risk/high-reward and low-risk/low-reward suggestions
- **Real-Time Market Data**: Integration with Alpha Vantage and Yahoo Finance APIs
- **Paper Trading Simulation**: Safe strategy testing with Alpaca Trading API
- **Performance Analytics**: Comprehensive tracking and visualization
- **Machine Learning**: Adaptive strategies that learn from market conditions
- **Local Data Storage**: Complete privacy with no cloud transmission
- **Regulatory Compliance**: Built-in risk disclosures and audit logging

## 🛠️ Technology Stack

- **Language**: Python 3.9+
- **GUI Framework**: PyQt6
- **Database**: SQLite
- **Machine Learning**: scikit-learn, TensorFlow/Keras, PyTorch
- **Data Processing**: pandas, NumPy, TA-Lib
- **Visualization**: Matplotlib, Plotly
- **APIs**: Alpha Vantage, Yahoo Finance, Alpaca Trading

## 📋 Prerequisites

- Python 3.9 or higher
- Windows 10/11
- API keys for:
  - Alpha Vantage (market data)
  - Alpaca Trading (paper trading)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Agent-Green
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys**
   ```bash
   # Create config/api_keys.env file with your API keys
   ALPHA_VANTAGE_API_KEY=your_key_here
   ALPACA_API_KEY=your_key_here
   ALPACA_SECRET_KEY=your_secret_here
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

## 📁 Project Structure

```
Agent-Green/
├── src/                    # Main source code
│   ├── data_layer/        # Data ingestion and API integration
│   ├── profile/           # User profile and risk management
│   ├── strategy/          # Trading engine and rule-based system
│   ├── execution/         # Trade execution and tracking
│   ├── ml_models/         # Machine learning components
│   ├── ui/               # User interface components
│   └── utils/            # Utility functions and helpers
├── config/               # Configuration files
├── data/                 # Local data storage
├── models/               # Saved ML models
├── logs/                 # Application logs
├── tests/                # Unit and integration tests
├── docs/                 # Project documentation
└── main.py              # Application entry point
```

## 🔧 Configuration

The application uses a centralized configuration system in `config/config.py`. Key settings include:

- **Trading Parameters**: Risk tolerance, position sizes, stop losses
- **API Configuration**: Endpoints and authentication
- **Data Settings**: Cache duration, update intervals
- **Security**: Encryption and audit logging
- **UI Preferences**: Window size, theme, display options

## 📊 Usage

1. **First Launch**: Complete risk assessment and set investment goals
2. **Market Analysis**: View real-time market data and technical indicators
3. **Trade Suggestions**: Review personalized recommendations with rationale
4. **Paper Trading**: Execute simulated trades to test strategies
5. **Performance Tracking**: Monitor portfolio performance and analytics
6. **Strategy Adaptation**: Let the system learn and improve over time

## 🔒 Security & Privacy

- **Local Storage**: All data stored locally, no cloud transmission
- **Encrypted Keys**: API keys encrypted and stored securely
- **Audit Logging**: Complete record of all system activities
- **Compliance**: Built-in regulatory compliance features

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

## 📈 Development Roadmap

- **Phase 1**: Project setup and foundation ✅
- **Phase 2**: Core infrastructure (data layer, profiles, database)
- **Phase 3**: Trading engine development
- **Phase 4**: Execution and tracking system
- **Phase 5**: User interface implementation
- **Phase 6**: Machine learning and adaptation
- **Phase 7**: Security and compliance
- **Phase 8**: Testing and validation
- **Phase 9**: Documentation and deployment
- **Phase 10**: Advanced features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. It is not intended to provide financial advice. Trading stocks involves risk, and you should consult with a qualified financial advisor before making investment decisions.

## 📞 Support

For questions, issues, or contributions, please refer to the project documentation in the `/docs/` directory or create an issue in the repository.

---

**Version**: 0.1.0  
**Last Updated**: 2025-07-26 