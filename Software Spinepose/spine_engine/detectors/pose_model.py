import mediapipe as mp
import numpy as np
from typing import Dict, Any, List, Optional
from ..core.types import Keypoint
from .base import BaseDetector

# Robust import for MediaPipe Pose
try:
    from mediapipe.python.solutions import pose as mp_pose
except ImportError:
    try:
        from mediapipe.solutions import pose as mp_pose
    except ImportError:
         print("Warning: Could not import mediapipe.solutions.pose directly. Relying on mp.solutions attribute.")
         mp_pose = None

class PoseEstimator(BaseDetector):
    """MediaPipe Pose Wrapper for Skeletal Estimation."""
    
    def load_model(self):
        complexity = self.config.get('complexity', 1) # 1=Full, 2=Heavy
        
        # Use the imported module, or fall back to mp.solutions.pose
        if mp_pose:
            self.mp_pose_module = mp_pose
        else:
             if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'pose'):
                 self.mp_pose_module = mp.solutions.pose
             else:
                 raise ImportError("Fatal: mediapipe.solutions.pose could not be loaded. Please check your mediapipe installation.")

        self.pose = self.mp_pose_module.Pose(
            static_image_mode=self.config.get('static_image_mode', False),
            model_complexity=complexity,
            enable_segmentation=False,
            min_detection_confidence=0.5
        )
        
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        # MediaPipe expects RGB
        # If input is BGR (OpenCV default), we should convert it.
        # However, we'll assume the pipeline handles color space or verify later.
        # For safety, let's assume input might be BGR and user should ensure RGB if needed,
        # or we just pass through. MediaPipe is sensitive to color.
        # Let's assume standard RGB input for the detector pipeline to be safe.
        return image
        
    def predict(self, input_data: np.ndarray) -> Any:
        # Input should be RGB
        results = self.pose.process(input_data)
        return results
        
    def postprocess(self, raw_output: Any) -> Optional[Dict[str, Keypoint]]:
        if not raw_output.pose_landmarks:
            return None
            
        landmarks = {}
        mp_landmarks = raw_output.pose_landmarks.landmark
        
        # Map MediaPipe landmarks to our Keypoint type
        for idx, lm in enumerate(mp_landmarks):
            # MediaPipe provides 33 landmarks
            name = self.mp_pose_module.PoseLandmark(idx).name
            
            k = Keypoint(
                id=idx,
                name=name,
                x=lm.x,
                y=lm.y,
                z=lm.z,
                visibility=lm.visibility
            )
            landmarks[name] = k
            
        return landmarks
