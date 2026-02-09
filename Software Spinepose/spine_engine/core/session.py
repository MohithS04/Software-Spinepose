import cv2
import numpy as np
from typing import List, Optional, Dict

from .types import FrameAnalysis, AnalysisResult, BoundingBox
from ..detectors.yolo_model import YOLODetector
from ..detectors.pose_model import PoseEstimator
from ..analysis.geometry import analyze_biomechanics

class HybridEngine:
    """
    The Core Engine.
    Orchestrates YOLO (Detection) -> MediaPipe (Pose) -> Analysis (Geometry/Gemini).
    """
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.yolo = YOLODetector(self.config.get('yolo_config', {}))
        self.pose = PoseEstimator(self.config.get('pose_config', {}))
        
    def load_models(self):
        print("Loading YOLO...")
        self.yolo.load_model()
        print("Loading Pose Estimator...")
        self.pose.load_model()
        print("Models Loaded.")
        
    def process_frame(self, frame: np.ndarray, frame_id: int = 0) -> FrameAnalysis:
        """
        Full pipeline for a single frame.
        1. Detect Persons
        2. For each person, Crop & Estimate Pose
        3. Analyze Biomechanics
        """
        # 1. Detection
        # YOLO expects RGB usually, but OpenCV gives BGR.
        # Ultralytics handles BGR/RGB automatically if passed as numpy.
        # Let's keep it as is.
        boxes: List[BoundingBox] = self.yolo.process(frame)
        
        analysis_results = []
        
        for box in boxes:
            # ROI Extraction with padding
            h, w, _ = frame.shape
            pad = 10
            x1 = max(0, box.x1 - pad)
            y1 = max(0, box.y1 - pad)
            x2 = min(w, box.x2 + pad)
            y2 = min(h, box.y2 + pad)
            
            crop = frame[y1:y2, x1:x2]
            
            if crop.size == 0:
                continue
            
            # 2. Pose Estimation
            # Convert crop to RGB for MediaPipe
            crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            landmarks = self.pose.process(crop_rgb)
            
            if landmarks:
                # 3. De-normalize coordinates
                # Landmarks are normalized [0,1] relative to the CROP.
                # Need to map back to FULL IMAGE.
                
                crop_h, crop_w, _ = crop.shape
                
                for name, kp in landmarks.items():
                    # Denormalize to crop pixel space
                    px = kp.x * crop_w
                    py = kp.y * crop_h
                    
                    # Add offset
                    full_x = px + x1
                    full_y = py + y1
                    
                    # Normalize back to full image [0,1]
                    kp.x = full_x / w
                    kp.y = full_y / h
                    # Z is relative, keep as is
                    
                # 4. Biomechanical Analysis
                metrics = analyze_biomechanics(landmarks)
                
                result = AnalysisResult(
                    person_id=0, # TODO: Tracking ID
                    bbox=box,
                    keypoints=landmarks,
                    metrics=metrics
                )
                analysis_results.append(result)
                
        return FrameAnalysis(
            frame_id=frame_id,
            timestamp_ms=0, # TODO
            results=analysis_results
        )
