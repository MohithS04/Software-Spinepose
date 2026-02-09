from abc import ABC, abstractmethod
from typing import Any, List, Optional
import numpy as np

class BaseDetector(ABC):
    """Abstract base class for all AI detection modules."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        
    @abstractmethod
    def load_model(self):
        """Load model weights and initialize resources."""
        pass
        
    @abstractmethod
    def preprocess(self, image: np.ndarray) -> Any:
        """Prepare image for the model."""
        pass
        
    @abstractmethod
    def predict(self, input_data: Any) -> Any:
        """Run inference."""
        pass
        
    @abstractmethod
    def postprocess(self, raw_output: Any) -> Any:
        """Convert raw model output to standard types."""
        pass
    
    def process(self, image: np.ndarray) -> Any:
        """Full pipeline execution: Pre -> Predict -> Post."""
        processed = self.preprocess(image)
        raw = self.predict(processed)
        return self.postprocess(raw)
