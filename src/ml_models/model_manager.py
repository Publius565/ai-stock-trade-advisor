"""
Model Manager for Machine Learning Components

Handles model lifecycle, training, persistence, and versioning.
"""

import os
import pickle
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages machine learning models for stock prediction."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.model_metadata: Dict[str, Dict] = {}
        
        # Ensure models directory exists
        os.makedirs(models_dir, exist_ok=True)
        
        # Initialize default models
        self._initialize_default_models()
    
    def _initialize_default_models(self):
        """Initialize default ML models."""
        self.models = {
            'random_forest': RandomForestRegressor(
                n_estimators=100, 
                max_depth=10, 
                random_state=42
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100, 
                max_depth=5, 
                random_state=42
            ),
            'linear_regression': LinearRegression()
        }
        
        # Initialize scalers for each model
        for model_name in self.models.keys():
            self.scalers[model_name] = StandardScaler()
            self.model_metadata[model_name] = {
                'created_at': datetime.now().isoformat(),
                'last_trained': None,
                'performance_metrics': {},
                'feature_importance': {},
                'training_samples': 0
            }
    
    def train_model(self, model_name: str, X: pd.DataFrame, y: pd.Series, 
                   validation_split: float = 0.2) -> Dict[str, float]:
        """Train a specific model with the provided data."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")
        
        logger.info(f"Training {model_name} model with {len(X)} samples")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scalers[model_name].fit_transform(X_train)
        X_val_scaled = self.scalers[model_name].transform(X_val)
        
        # Train model
        self.models[model_name].fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred = self.models[model_name].predict(X_val_scaled)
        
        # Calculate metrics
        mse = mean_squared_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        
        # Cross-validation score
        cv_scores = cross_val_score(
            self.models[model_name], X_train_scaled, y_train, 
            cv=5, scoring='r2'
        )
        
        # Update metadata
        self.model_metadata[model_name].update({
            'last_trained': datetime.now().isoformat(),
            'performance_metrics': {
                'mse': mse,
                'r2': r2,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            },
            'training_samples': len(X_train)
        })
        
        # Store feature importance if available
        if hasattr(self.models[model_name], 'feature_importances_'):
            feature_importance = dict(zip(
                X.columns, 
                self.models[model_name].feature_importances_
            ))
            self.model_metadata[model_name]['feature_importance'] = feature_importance
        
        logger.info(f"{model_name} training complete - R²: {r2:.4f}, MSE: {mse:.4f}")
        
        return {
            'mse': mse,
            'r2': r2,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
    
    def predict(self, model_name: str, X: pd.DataFrame) -> np.ndarray:
        """Make predictions using a trained model."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")
        
        # Scale features
        X_scaled = self.scalers[model_name].transform(X)
        
        # Make prediction
        predictions = self.models[model_name].predict(X_scaled)
        
        return predictions
    
    def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """Get performance metrics for a specific model."""
        if model_name not in self.model_metadata:
            raise ValueError(f"Model '{model_name}' not found")
        
        return self.model_metadata[model_name]
    
    def save_model(self, model_name: str, filename: Optional[str] = None) -> str:
        """Save a trained model to disk."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{model_name}_{timestamp}.pkl"
        
        filepath = os.path.join(self.models_dir, filename)
        
        # Save model and scaler
        model_data = {
            'model': self.models[model_name],
            'scaler': self.scalers[model_name],
            'metadata': self.model_metadata[model_name]
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model {model_name} saved to {filepath}")
        return filepath
    
    def load_model(self, filepath: str) -> str:
        """Load a trained model from disk."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        # Extract model name from filename
        filename = os.path.basename(filepath)
        if '_' in filename:
            model_name = filename.split('_')[0]
            # Handle special case for gradient_boosting
            if model_name == 'gradient' and 'gradient_boosting' in filename:
                model_name = 'gradient_boosting'
        else:
            model_name = filename.split('.')[0]
        
        # Load components
        self.models[model_name] = model_data['model']
        self.scalers[model_name] = model_data['scaler']
        self.model_metadata[model_name] = model_data['metadata']
        
        logger.info(f"Model {model_name} loaded from {filepath}")
        return model_name
    
    def list_models(self) -> List[str]:
        """List all available models."""
        return list(self.models.keys())
    
    def get_best_model(self) -> Optional[str]:
        """Get the best performing model based on R² score."""
        best_model = None
        best_score = -float('inf')
        
        for model_name, metadata in self.model_metadata.items():
            if 'performance_metrics' in metadata and 'r2' in metadata['performance_metrics']:
                score = metadata['performance_metrics']['r2']
                if score > best_score:
                    best_score = score
                    best_model = model_name
        
        return best_model 