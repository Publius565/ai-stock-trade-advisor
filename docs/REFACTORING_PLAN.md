# Modular Architecture Refactoring Plan
*AI-Driven Stock Trade Advisor - Version 0.4.3*

## Overview
This document outlines specific refactoring recommendations to further optimize the project's modular architecture, following Rule 2.3 and best practices for maintainable code.

## Current Status ✅
- **All files under 1500-line threshold** (Rule 2.3 compliant)
- **Excellent modular architecture** with clear layer separation
- **Recent UI refactoring success**: 1022 → 350 lines through component modularization
- **Database integrity verified**: 17 tables with proper structure

## Refactoring Priorities

### 1. MarketDataManager Decomposition (596 lines)
**Problem**: Single class with multiple responsibilities violates SRP

**Current Structure**:
```python
class MarketDataManager(BaseDatabaseManager):
    # Symbol management (6 methods)
    # Market data storage (4 methods)  
    # Technical indicators (4 methods)
    # Market movers (3 methods)
    # Watchlist management (8 methods)
    # News articles (2 methods)
    # Statistics (1 method)
```

**Recommended Split**:
```python
# New specialized managers
class SymbolManager(BaseDatabaseManager):
    - get_or_create_symbol()
    - get_symbol()
    - get_symbol_statistics()

class MarketDataStorage(BaseDatabaseManager):
    - store_market_data()
    - get_market_data()

class IndicatorManager(BaseDatabaseManager):
    - store_indicator_data()
    - get_indicator_data()

class WatchlistManager(BaseDatabaseManager):
    - create_watchlist()
    - add_symbol_to_watchlist()
    - get_user_watchlists()
    - get_watchlist_symbols()
    - remove_symbol_from_watchlist()
    - delete_watchlist()

class NewsManager(BaseDatabaseManager):
    - store_market_mover()
    - store_news_article()
    - get_top_movers()
```

**Implementation Steps**:
1. Create new manager classes inheriting from BaseDatabaseManager
2. Move related methods to appropriate managers
3. Update factory pattern in DatabaseManager
4. Update imports across the project
5. Update unit tests

**Expected Benefits**:
- Smaller, focused classes (~100-150 lines each)
- Better testability and maintainability
- Clearer responsibilities
- Easier to extend individual components

### 2. Market Scanner Strategy Pattern (582 lines)
**Problem**: Multiple scanning strategies in single class

**Current Structure**:
```python
class MarketScanner:
    - scan_top_movers()
    - scan_user_watchlists()
    - scan_news_for_symbols()
    - Various helper methods
```

**Recommended Strategy Pattern**:
```python
class ScanningStrategy(ABC):
    @abstractmethod
    def scan(self, **kwargs) -> Dict[str, Any]:
        pass

class TopMoversScanner(ScanningStrategy):
    def scan(self, limit: int = 50) -> Dict[str, List]:
        # Top movers logic only

class WatchlistScanner(ScanningStrategy):
    def scan(self, user_uid: str) -> Dict[str, Any]:
        # Watchlist scanning logic only

class NewsScanner(ScanningStrategy):
    def scan(self, symbols: List[str], hours_back: int = 24) -> Dict[str, List]:
        # News scanning logic only

class MarketScanner:
    def __init__(self):
        self.strategies = {
            'top_movers': TopMoversScanner(),
            'watchlist': WatchlistScanner(),
            'news': NewsScanner()
        }
    
    def scan(self, strategy_name: str, **kwargs) -> Dict[str, Any]:
        return self.strategies[strategy_name].scan(**kwargs)
```

### 3. Profile Manager Enhancement (502 lines)
**Recommended Split**:
```python
class UserProfileManager(BaseDatabaseManager):
    # Core profile operations
    - create_user_profile()
    - get_user_profile()
    - update_risk_profile()

class UserPreferencesManager(BaseDatabaseManager):
    # Preferences and settings
    - get_user_preferences()
    - update_preferences()
    - manage_notifications()
```

## Implementation Timeline

### Phase 1 (Week 1): Database Managers Split
- [ ] Create SymbolManager class
- [ ] Create MarketDataStorage class  
- [ ] Create IndicatorManager class
- [ ] Update DatabaseManager factory
- [ ] Update tests

### Phase 2 (Week 2): Remaining Managers
- [ ] Create WatchlistManager class
- [ ] Create NewsManager class
- [ ] Update all imports
- [ ] Comprehensive testing

### Phase 3 (Week 3): Scanner Strategy Pattern
- [ ] Implement scanning strategy interface
- [ ] Create specialized scanner classes
- [ ] Refactor MarketScanner to use strategies
- [ ] Update UI components

### Phase 4 (Week 4): Profile Manager Split
- [ ] Split ProfileManager functionality
- [ ] Create UserPreferencesManager
- [ ] Update dependencies
- [ ] Final integration testing

## Validation Criteria
- ✅ All classes under 300 lines
- ✅ Single Responsibility Principle adherence
- ✅ Existing tests continue to pass
- ✅ No breaking changes to public APIs
- ✅ Documentation updated

## Risk Mitigation
- Incremental refactoring with continuous testing
- Maintain backward compatibility during transition
- Comprehensive unit test coverage
- Code review for each major change

## Success Metrics
- Reduced class complexity (lines per class)
- Improved test coverage and maintainability
- Better separation of concerns
- Enhanced developer productivity 