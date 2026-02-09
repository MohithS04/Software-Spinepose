from typing import List, Any
import numpy as np
from ultralytics import YOLO
from ..core.types import BoundingBox
from .base import BaseDetector

class YOLODetector(BaseDetector):
    """YOLOv8 Wrapper for Person Detection."""
    
    def load_model(self):
        model_path = self.config.get('model_path', 'yolov8n.pt')
        self.model = YOLO(model_path)
        # Warmup
        # self.model(np.zeros((640, 640, 3), dtype=np.uint8))
        
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        return image # YOLO handles preprocessing internally
        
    def predict(self, input_data: np.ndarray) -> Any:
        # Run inference, enforcing class 0 (person)
        results = self.model(input_data, classes=[0], verbose=False)
        return results
        
    def postprocess(self, raw_output: Any) -> List[BoundingBox]:
        boxes = []
        result = raw_output[0] # First image results
        
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            
            b = BoundingBox(
                x1=int(x1),
                y1=int(y1),
                x2=int(x2),
                y2=int(y2),
                confidence=conf
            )
            boxes.append(b)
            
        return boxes
