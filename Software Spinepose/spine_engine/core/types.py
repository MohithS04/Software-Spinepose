from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import numpy as np

@dataclass
class Keypoint:
    """Represents a single skeletal landmark in 3D space."""
    id: int
    name: str
    x: float  # Normalized [0, 1]
    y: float  # Normalized [0, 1]
    z: float  # Depth (relative)
    visibility: float  # [0, 1] confidence

@dataclass
class BoundingBox:
    """Represents a detected person's bounding box."""
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    
    @property
    def area(self) -> int:
        return (self.x2 - self.x1) * (self.y2 - self.y1)
    
    @property
    def center(self) -> Tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

@dataclass
class Patient:
    """Represents a Patient for hospital/clinical use."""
    id: str
    name: str
    age: int
    gender: str
    notes: Optional[str] = ""

@dataclass
class SpineMetrics:
    """ biomechanical analysis results for a spine."""
    cobb_angle_thoracic: Optional[float] = None
    cobb_angle_lumbar: Optional[float] = None
    cervical_flexion: Optional[float] = None # Neck forward bend (Text Neck)
    lumbar_flexion: Optional[float] = None   # Lower back bend
    pelvic_tilt: Optional[float] = None
    
    # Clinical Indicators
    posture_type: str = "Neutral" # Kyphosis, Lordosis, Swayback, Flatback
    symmetry_index: float = 100.0 # 100 is perfect symmetry
    
    # "Spine Currency" / Health Score (0-100)
    health_score: float = 0.0

@dataclass
class AnalysisResult:
    """Complete analysis for a single person in a frame."""
    person_id: int
    bbox: BoundingBox
    keypoints: Dict[str, Keypoint] = field(default_factory=dict)
    metrics: Optional[SpineMetrics] = None
    raw_landmarks: Optional[List[Keypoint]] = None # Full MediaPipe output
    
@dataclass
class FrameAnalysis:
    """Container for all analysis in a single video frame."""
    frame_id: int
    timestamp_ms: float
    results: List[AnalysisResult] = field(default_factory=list)
