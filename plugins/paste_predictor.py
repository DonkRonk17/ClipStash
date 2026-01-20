#!/usr/bin/env python3
"""
Paste Predictor Plugin - Intelligent Paste Predictor
Priority: HIGH

Tracks paste patterns and predicts next paste using ML:
- Tracks paste patterns based on context (time, app, content type)
- Builds training dataset from history
- Trains scikit-learn RandomForest model
- Predicts next paste with confidence scores
- Persists model to disk
"""

import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from clipstash_core import ClipStashPlugin, ClipItem, PluginPriority

logger = logging.getLogger(__name__)


class PastePredictorPlugin(ClipStashPlugin):
    """
    Predicts which clipboard item user is likely to paste next.
    Uses machine learning based on usage patterns.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._name = "PastePredictor"
        self._priority = PluginPriority.HIGH
        self._version = "1.0.0"
        
        # Configuration
        self.model_path = Path(config.get('model_path', Path.home() / '.clipstash' / 'paste_predictor.pkl')) if config else Path.home() / '.clipstash' / 'paste_predictor.pkl'
        self.min_training_samples = config.get('min_training_samples', 50) if config else 50
        self.max_predictions = config.get('max_predictions', 5) if config else 5
        self.retrain_interval = config.get('retrain_interval', 100) if config else 100  # Retrain every N pastes
        
        # State
        self.model = None
        self.feature_names = []
        self.paste_history = []
        self.paste_count = 0
        self.last_train_count = 0
    
    async def initialize(self) -> bool:
        """Initialize the paste predictor."""
        try:
            # Try to load existing model
            if self.model_path.exists():
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data.get('model')
                    self.feature_names = data.get('feature_names', [])
                    self.paste_history = data.get('paste_history', [])
                    self.last_train_count = data.get('last_train_count', 0)
                logger.info(f"Loaded paste predictor model from {self.model_path}")
            else:
                logger.info("No existing model found, will train on first use")
        except Exception as e:
            logger.error(f"Error loading paste predictor model: {e}")
        
        logger.info(f"{self.name} initialized")
        return True
    
    async def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Generate paste predictions for new clip.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Clip with predictions added
        """
        # Record this event
        self._record_event(clip, context)
        
        # Generate predictions if model is trained
        if self.model is not None:
            predictions = self._predict(clip, context)
            if predictions:
                clip.metadata.predictions['paste_likelihood'] = predictions
                clip.metadata.confidence_scores['paste_prediction'] = predictions[0]['confidence']
                logger.debug(f"Predicted paste likelihood: {predictions[0]['confidence']:.2f}")
        
        # Check if we should retrain
        if (self.paste_count - self.last_train_count) >= self.retrain_interval:
            if len(self.paste_history) >= self.min_training_samples:
                logger.info("Retraining paste predictor model...")
                await self._train_model()
        
        return clip
    
    async def on_paste(self, clip: ClipItem, context: Dict[str, Any]) -> Optional[ClipItem]:
        """
        Record paste event for learning.
        
        Args:
            clip: Clip being pasted
            context: Current context
        
        Returns:
            Original clip
        """
        self.paste_count += 1
        
        # Update paste history with successful paste
        event = {
            'content_hash': clip.hash,
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'pasted': True
        }
        self.paste_history.append(event)
        
        # Keep history manageable
        if len(self.paste_history) > 1000:
            self.paste_history = self.paste_history[-1000:]
        
        logger.debug(f"Recorded paste event (total: {self.paste_count})")
        
        return clip
    
    def _record_event(self, clip: ClipItem, context: Dict[str, Any]):
        """Record a clipboard event."""
        event = {
            'content_hash': clip.hash,
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'content_type': clip.metadata.enrichments.get('content', {}).get('content_type', 'unknown'),
            'length': len(clip.content),
            'pasted': False  # Will be updated on actual paste
        }
        self.paste_history.append(event)
    
    async def _train_model(self):
        """Train the prediction model."""
        try:
            import numpy as np
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import LabelEncoder
            
            # Prepare training data
            X, y = self._prepare_training_data()
            
            if len(X) < self.min_training_samples:
                logger.warning(f"Not enough training samples: {len(X)} < {self.min_training_samples}")
                return
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=50,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X, y)
            self.last_train_count = self.paste_count
            
            # Save model
            self._save_model()
            
            logger.info(f"Trained paste predictor on {len(X)} samples")
        
        except ImportError:
            logger.warning("scikit-learn not available for paste prediction")
        except Exception as e:
            logger.error(f"Error training paste predictor: {e}")
    
    def _prepare_training_data(self):
        """Prepare training data from paste history."""
        import numpy as np
        
        X = []  # Features
        y = []  # Labels (pasted or not)
        
        for event in self.paste_history:
            features = self._extract_features(event)
            X.append(features)
            y.append(1 if event.get('pasted', False) else 0)
        
        return np.array(X), np.array(y)
    
    def _extract_features(self, event: Dict[str, Any]) -> List[float]:
        """Extract feature vector from event."""
        context = event.get('context', {})
        
        # Time-based features
        try:
            timestamp = datetime.fromisoformat(event.get('timestamp', datetime.now().isoformat()))
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
        except:
            hour = 0
            day_of_week = 0
        
        # Content features
        content_type = event.get('content_type', 'unknown')
        content_type_map = {'text': 0, 'code': 1, 'url': 2, 'email': 3, 'unknown': 4}
        content_type_encoded = content_type_map.get(content_type, 4)
        
        length = event.get('length', 0)
        
        # Context features
        active_app = context.get('active_app', 'Unknown')
        active_app_hash = hash(active_app) % 1000  # Simple hash to number
        
        features = [
            hour / 24.0,  # Normalized hour
            day_of_week / 7.0,  # Normalized day
            content_type_encoded / 4.0,  # Normalized content type
            min(length / 1000.0, 1.0),  # Normalized length (capped at 1000)
            (active_app_hash % 100) / 100.0,  # Normalized app hash
        ]
        
        return features
    
    def _predict(self, clip: ClipItem, context: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Predict paste likelihood.
        
        Args:
            clip: Clip to predict for
            context: Current context
        
        Returns:
            List of predictions with confidence scores
        """
        if self.model is None:
            return None
        
        try:
            import numpy as np
            
            # Extract features for this clip
            event = {
                'content_hash': clip.hash,
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'content_type': clip.metadata.enrichments.get('content', {}).get('content_type', 'unknown'),
                'length': len(clip.content),
            }
            features = self._extract_features(event)
            
            # Predict
            X = np.array([features])
            probabilities = self.model.predict_proba(X)[0]
            
            # Get paste probability (class 1)
            paste_prob = probabilities[1] if len(probabilities) > 1 else 0.5
            
            predictions = [
                {
                    'type': 'paste_likelihood',
                    'confidence': float(paste_prob),
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            return predictions
        
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None
    
    def _save_model(self):
        """Save model to disk."""
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'model': self.model,
                'feature_names': self.feature_names,
                'paste_history': self.paste_history,
                'last_train_count': self.last_train_count,
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.debug(f"Saved paste predictor model to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    async def shutdown(self):
        """Save model on shutdown."""
        if self.model is not None:
            self._save_model()
        logger.info(f"{self.name} shutdown")
