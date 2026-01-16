"""
Model Inference Service
Handles loading the model and making predictions
"""
import os
import logging
import requests
from flask import current_app

import numpy as np

logger = logging.getLogger(__name__)

# Global model instance (singleton)
_model = None
_model_loaded = False


class InferenceService:
    """Deep Learning inference service"""
    
    CLASS_LABELS = {
        0: 'Down Syndrome',
        1: 'Normal'
    }
    
    @classmethod
    def initialize_model(cls, model_path, download_url=None):
        """
        Initialize model at application startup (without Flask context)
        
        Args:
            model_path: path to model file
            download_url: URL to download if model doesn't exist
        
        Returns:
            loaded model or None
        """
        global _model, _model_loaded
        
        if _model_loaded and _model is not None:
            return _model
        
        # Check if model exists, download if not
        if not os.path.exists(model_path):
            logger.warning(f"Model not found at {model_path}")
            
            if download_url:
                logger.info("Attempting to download model...")
                if not cls.download_model(download_url, model_path):
                    logger.error("Failed to download model")
                    return None
            else:
                logger.error("No model download URL configured")
                return None
        
        try:
            # Configure TensorFlow to use GPU if available
            import tensorflow as tf
            
            # Suppress TF warnings for cleaner output
            tf.get_logger().setLevel('ERROR')
            
            # Check for GPU
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                logger.info(f"GPU detected: {gpus}")
                print(f"  🎮 GPU detected: {len(gpus)} device(s)")
                # Allow memory growth to prevent OOM
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
            else:
                logger.info("No GPU detected, using CPU")
                print(f"  💻 Using CPU for inference")
            
            # Load model
            logger.info(f"Loading model from {model_path}...")
            _model = tf.keras.models.load_model(model_path)
            _model_loaded = True
            
            logger.info("Model loaded successfully")
            logger.info(f"Model input shape: {_model.input_shape}")
            logger.info(f"Model output shape: {_model.output_shape}")
            
            return _model
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            _model = None
            _model_loaded = False
            return None
    
    @classmethod
    def download_model(cls, url, destination):
        """
        Download model from URL
        
        Args:
            url: download URL
            destination: local file path
        
        Returns:
            bool: True if successful
        """
        if not url:
            logger.error("Model download URL not configured")
            return False
        
        try:
            logger.info(f"Downloading model from {url}...")
            
            # Create directory if not exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            # Download with streaming
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) < 8192:  # Log every ~1MB
                                logger.info(f"Download progress: {progress:.1f}%")
            
            logger.info(f"Model downloaded successfully to {destination}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download model: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error during model download: {str(e)}")
            return False
    
    @classmethod
    def load_model(cls, model_path=None, download_url=None):
        """
        Get the loaded model (should already be initialized at startup)
        
        Args:
            model_path: path to model file (optional, uses config if not provided)
            download_url: URL to download if model doesn't exist (optional)
        
        Returns:
            loaded model or None
        """
        global _model, _model_loaded
        
        # Return cached model if already loaded
        if _model_loaded and _model is not None:
            return _model
        
        # Fallback: try to load if not initialized at startup
        logger.warning("Model was not preloaded, loading now...")
        
        # Get paths from config if not provided
        if model_path is None:
            model_path = current_app.config.get('MODEL_PATH')
        if download_url is None:
            download_url = current_app.config.get('MODEL_DOWNLOAD_URL')
        
        return cls.initialize_model(model_path, download_url)
    
    @classmethod
    def predict(cls, preprocessed_image):
        """
        Make prediction on preprocessed image
        
        Args:
            preprocessed_image: numpy array with shape (1, 224, 224, 3)
        
        Returns:
            dict with prediction results
        """
        model = cls.load_model()
        
        if model is None:
            raise RuntimeError("Model tidak tersedia. Silakan hubungi administrator.")
        
        try:
            # Run inference
            prediction = model.predict(preprocessed_image, verbose=0)
            
            # Get probability value (sigmoid output)
            prob_value = float(prediction[0][0])
            
            # Interpret prediction
            # Based on training: Class indices: {'downSyndrome': 0, 'healty': 1}
            # Sigmoid output > 0.5 means Normal (class 1)
            if prob_value > 0.5:
                result_class = 'Normal'
                confidence = prob_value
            else:
                result_class = 'Down Syndrome'
                confidence = 1 - prob_value
            
            return {
                'class': result_class,
                'confidence': confidence,
                'raw_probability': prob_value,
                'probabilities': {
                    'Normal': prob_value,
                    'Down Syndrome': 1 - prob_value
                }
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise RuntimeError(f"Gagal melakukan prediksi: {str(e)}")
    
    @classmethod
    def is_model_available(cls):
        """Check if model is loaded and available"""
        global _model, _model_loaded
        return _model_loaded and _model is not None
    
    @classmethod
    def get_model_info(cls):
        """Get model information"""
        model = cls.load_model()
        
        if model is None:
            return None
        
        return {
            'input_shape': model.input_shape,
            'output_shape': model.output_shape,
            'total_params': model.count_params()
        }
