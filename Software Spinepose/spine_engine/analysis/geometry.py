import numpy as np
from typing import Dict, Tuple, Optional
from ..core.types import Keypoint, SpineMetrics

def calculate_angle_3d(a: Keypoint, b: Keypoint, c: Keypoint) -> float:
    """
    Calculates the 3D angle at point b formed by points a, b, and c.
    Returns angle in degrees.
    """
    av = np.array([a.x, a.y, a.z])
    bv = np.array([b.x, b.y, b.z])
    cv = np.array([c.x, c.y, c.z])
    
    ba = av - bv
    bc = cv - bv
    
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    
    return np.degrees(angle)

def calculate_slope_angle(p1: Keypoint, p2: Keypoint) -> float:
    """Calculates angle of line p1-p2 relative to horizontal axis."""
    dy = p2.y - p1.y
    dx = p2.x - p1.x
    return np.degrees(np.arctan2(dy, dx))

def analyze_biomechanics(landmarks: Dict[str, Keypoint]) -> SpineMetrics:
    """Compute biomechanical metrics from landmarks."""
    metrics = SpineMetrics()
    
    # Extract key landmarks
    # MediaPipe Pose landmarks: 11=left_shoulder, 12=right_shoulder, 23=left_hip, 24=right_hip
    # Additional Landmarks for Advanced Metrics
    le = landmarks.get('LEFT_EAR')
    re = landmarks.get('RIGHT_EAR')
    nose = landmarks.get('NOSE')
    
    ls = landmarks.get('LEFT_SHOULDER')
    rs = landmarks.get('RIGHT_SHOULDER')
    lh = landmarks.get('LEFT_HIP')
    rh = landmarks.get('RIGHT_HIP')
    lk = landmarks.get('LEFT_KNEE')
    rk = landmarks.get('RIGHT_KNEE')

    if ls and rs and lh and rh:
        # 1. Estimated Cobb Angle (Heuristic: Angle between shoulder line and hip line)
        # In a healthy spine, these are parallel (angle = 0).
        # Scoliosis causes lateral tilt.
        shoulder_slope = calculate_slope_angle(ls, rs)
        hip_slope = calculate_slope_angle(lh, rh)
        
        # The deviation from parallel is our heuristic cobb score
        metrics.cobb_angle_thoracic = abs(shoulder_slope - hip_slope)
        
        # 2. Lumbar Flexion (Forward bend)
        # Angle between vertical and the vector from Mid-Hip to Mid-Shoulder
        mid_hip_x = (lh.x + rh.x) / 2
        mid_hip_y = (lh.y + rh.y) / 2
        mid_hip_z = (lh.z + rh.z) / 2
        
        mid_shoulder_x = (ls.x + rs.x) / 2
        mid_shoulder_y = (ls.y + rs.y) / 2
        mid_shoulder_z = (ls.z + rs.z) / 2
        
        # Vector from hip to shoulder
        trunk_vec = np.array([
            mid_shoulder_x - mid_hip_x,
            mid_shoulder_y - mid_hip_y,
            mid_shoulder_z - mid_hip_z
        ])
        
        # Vertical vector (upwards is negative Y in most image coords, but let's assume standard 3D)
        # In MediaPipe, y increases downwards. So "up" is -y.
        vertical_vec = np.array([0, -1, 0])
        
        # Projection for flexion (usually sagittal plane, so ignored x in 2D or use 3D)
        cosine_flex = np.dot(trunk_vec, vertical_vec) / (np.linalg.norm(trunk_vec) * np.linalg.norm(vertical_vec))
        flexion_angle = np.degrees(np.arccos(np.clip(cosine_flex, -1.0, 1.0)))
        
        metrics.lumbar_flexion = flexion_angle

        # 3. Cervical Flexion (Text Neck)
        # Vector from Mid-Shoulder to Mid-Ear
        if le and re:
            mid_ear_x = (le.x + re.x) / 2
            mid_ear_y = (le.y + re.y) / 2
            mid_ear_z = (le.z + re.z) / 2
            
            neck_vec = np.array([
                mid_ear_x - mid_shoulder_x,
                mid_ear_y - mid_shoulder_y,
                mid_ear_z - mid_shoulder_z
            ])
            
            # Angle against vertical
            cosine_cervical = np.dot(neck_vec, vertical_vec) / (np.linalg.norm(neck_vec) * np.linalg.norm(vertical_vec))
            cervical_angle = np.degrees(np.arccos(np.clip(cosine_cervical, -1.0, 1.0)))
            
            metrics.cervical_flexion = cervical_angle
        
        # 4. Symmetry Index
        # Compare Left Side Length (Shoulder->Hip) vs Right Side Length
        left_side_len = np.linalg.norm(np.array([ls.x-lh.x, ls.y-lh.y]))
        right_side_len = np.linalg.norm(np.array([rs.x-rh.x, rs.y-rh.y]))
        
        if max(left_side_len, right_side_len) > 0:
            symmetry = (min(left_side_len, right_side_len) / max(left_side_len, right_side_len)) * 100
            metrics.symmetry_index = symmetry

        # 5. Health Score Calculation
        score = 100.0
        
        # Penalty: Cobb (Scoliosis risk)
        if metrics.cobb_angle_thoracic > 5: # Tightened threshold
            score -= (metrics.cobb_angle_thoracic - 5) * 3
            
        # Penalty: Forward Head (Text Neck)
        # Normal neck angle is roughly 0-10 deg forward? Wait, vertical is 0. 
        # Actually, straight neck is aligned with trunk?
        # Let's assume > 15 deg forward is bad.
        if metrics.cervical_flexion and metrics.cervical_flexion > 20: 
             score -= (metrics.cervical_flexion - 20) * 1.5
             metrics.posture_type = "Forward Head"
             
        # Penalty: Symmetry
        if metrics.symmetry_index < 95:
            score -= (95 - metrics.symmetry_index) * 2
            
        metrics.health_score = max(0.0, score)
        
    return metrics
