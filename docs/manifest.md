# Project Manifest - AI-Driven Stock Trade Advisor

## Source Code Repository

**GitHub Repository**: [https://github.com/Publius565/ai-stock-trade-advisor](https://github.com/Publius565/ai-stock-trade-advisor)

- **Repository Type**: Private
- **Branch**: master
- **Last Updated**: 2025-07-26
- **Status**: Active Development
- **Backup Status**: ✅ Fully backed up to GitHub

## Current Project Structure

This document provides a comprehensive listing of all folders and files in the AI-Driven Stock Trade Advisor project, along with their purposes and relationships.

## Root Directory Files
- **main.py** - Main application entry point orchestrating all system components
- **README.md** - Comprehensive project documentation with installation and usage instructions
- **requirements.txt** - Python dependencies and package management
- **.gitignore** - Git ignore patterns for sensitive files and build artifacts
- **debug_schema.py** - Database schema debugging and testing script
- **test_updated_schema.py** - Database schema update testing script
- **simple_database_test.py** - Basic database functionality testing
- **test_database_infrastructure.py** - Comprehensive database infrastructure testing
- **quick_api_test.py** - Quick API connection verification script
- **test_api_connections.py** - Comprehensive API connection testing
- **test_data_ingestion.py** - Data ingestion layer testing and validation

## Documentation Directory (`/docs/`)
- **manifest.md** - This file: Complete listing of project structure and file purposes
- **CHANGELOG.md** - Chronological record of all project changes and updates
- **TODOS.md** - Tracking of planned features, tasks, and their completion status
- **devreadme.txt** - Technical description of the application, tech stack, and dependencies
- **chathistory.md** - Record of development conversations and decisions with timestamps

## Configuration Directory (`/config/`)
- **api_keys.env** - API keys configuration file with placeholders (SECURE: Contains only placeholders)
- **config.py** - Main application configuration settings
- **github_config.py** - GitHub repository configuration and credential management
- **github_settings.json** - GitHub settings storage (contains only username)
- **logging_config.py** - Comprehensive logging configuration with rotation
- **database_schema.sql** - Original database schema with 13 tables
- **optimized_database_schema.sql** - Optimized database schema with UIDs and indexing
- **risk_disclosure.txt** - Risk disclosure template for regulatory compliance

## Source Code Directory (`/src/`)
### Core Application Modules
- **`/src/__init__.py`** - Package initialization file
- **`/src/data_layer/`** - Data ingestion and API integration modules
  - **`__init__.py`** - Package initialization
  - **api_client.py** - API client for external financial data providers
  - **data_cache.py** - Intelligent data caching system
  - **data_validator.py** - Data validation and quality assurance
  - **market_data.py** - Market data management and processing
  - **streaming_data.py** - Real-time data streaming capabilities
- **`/src/profile/`** - User profile and risk management modules
  - **`__init__.py`** - Package initialization
- **`/src/strategy/`** - Trade suggestion engine and rule-based systems
  - **`__init__.py`** - Package initialization
- **`/src/execution/`** - Trade execution and tracking modules
  - **`__init__.py`** - Package initialization
- **`/src/ml_models/`** - Machine learning and AI components
  - **`__init__.py`** - Package initialization
- **`/src/ui/`** - User interface components (GUI or web-based)
  - **`__init__.py`** - Package initialization
- **`/src/utils/`** - Utility functions and database management
  - **`__init__.py`** - Package initialization with all database managers
  - **base_manager.py** - Abstract base class for database operations
  - **database_manager.py** - Factory pattern for accessing specialized managers
  - **user_manager.py** - User profile and authentication management
  - **market_data_manager.py** - Market data, symbols, and indicators management
  - **signal_manager.py** - Trading signals and portfolio management

## Data and Storage Directories
- **`/data/`** - Local data storage and cache
  - **trading_advisor.db** - Main SQLite database
  - **test_trading_advisor.db** - Test database
  - **simple_test.db** - Simple test database
  - **updated_test.db** - Updated test database
  - **debug_test.db** - Debug test database
  - **`/test_cache/`** - Test cache directory with cached data files
- **`/models/`** - Saved ML models and rule configurations (empty, ready for use)
- **`/logs/`** - Application logs and debugging information (empty, ready for use)

## Development and Testing
- **`/tests/`** - Unit tests and integration tests (empty, ready for use)
- **`/scripts/`** - Utility scripts for setup, deployment, and maintenance
  - **init_database.py** - Database initialization script with verification
  - **github_setup.py** - GitHub repository setup and configuration
  - **docker_management.py** - Docker container management utilities
  - **backup_verification.py** - Backup verification and testing script

## Containerization and Deployment
- **`/docker/`** - Docker configuration files for containerization
  - **Dockerfile** - Multi-stage Docker build configuration
  - **docker-compose.yml** - Docker Compose configuration for development and production
  - **.dockerignore** - Docker build context exclusions
  - **README.md** - Docker usage documentation and troubleshooting guide

## Development Environment
- **`/venv/`** - Python virtual environment (excluded from version control)
- **`/examples/`** - Example configurations and usage scenarios (empty, ready for use)
- **`/resources/`** - Static resources, templates, and assets (empty, ready for use)

## Security Assessment

### Secrets Scan Results - ✅ SECURE
**Date**: 2025-07-26
**Status**: No exposed secrets found

#### Files Checked:
- ✅ `config/api_keys.env` - Contains only placeholders, no actual API keys
- ✅ `config/github_settings.json` - Contains only username, no tokens
- ✅ `config/github_config.py` - Secure credential management, no hardcoded secrets
- ✅ `config/config.py` - Uses environment variables, no hardcoded secrets
- ✅ All Python source files - No hardcoded credentials found
- ✅ Database files - No sensitive data in test databases
- ✅ Configuration files - Properly secured with placeholders

#### Security Measures in Place:
- ✅ `.gitignore` properly excludes sensitive files:
  - `config/api_keys.env`
  - `config/.github_credentials`
  - `config/github_settings.json`
  - `*.key` files
  - Database files
  - Log files
- ✅ API keys use environment variables and placeholders
- ✅ GitHub credentials stored securely with proper file permissions
- ✅ No hardcoded secrets in source code
- ✅ Database contains only test data, no production credentials

#### Recommendations:
- ✅ Current security practices are appropriate
- ✅ No immediate action required
- ✅ Continue using environment variables for API keys
- ✅ Maintain current .gitignore exclusions

## File Purposes and Relationships

### Core Application Files
- **Main application entry point** - Orchestrates all system components
- **Configuration files** - Store API keys, user preferences, and system settings
- **Database schemas** - Define data structures for user profiles, trade history, and market data
- **API integration modules** - Handle communication with external financial data providers
- **ML model files** - Serialized machine learning models and training data

### Security and Compliance
- **Encryption utilities** - Secure storage of sensitive data and API keys
- **Compliance modules** - Risk disclosures, regulatory compliance features
- **Audit logging** - Record of all system activities and user interactions

### User Interface
- **GUI components** - Desktop application interface elements
- **Web interface** - Local web server for browser-based access
- **Charts and visualizations** - Performance dashboards and analytics displays

## Development Workflow Files
- **Requirements files** - Python dependencies and package management
- **Build scripts** - Automated build and deployment processes
- **CI/CD configuration** - Continuous integration and deployment setup
- **Environment files** - Development, testing, and production configurations

## Data Management
- **Backup utilities** - User data backup and restoration tools
- **Data migration scripts** - Schema updates and data format changes
- **Cache management** - Market data caching and cleanup utilities

## Regulatory and Legal
- **Disclosure templates** - Risk warnings and compliance notices
- **Terms of service** - User agreements and legal disclaimers
- **Privacy policy** - Data handling and privacy protection measures

This manifest will be updated as the project evolves and new files are added to maintain a complete record of the project structure. 