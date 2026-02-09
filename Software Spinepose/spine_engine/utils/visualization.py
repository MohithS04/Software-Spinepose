
import cv2
import numpy as np
from typing import Dict, Any, Tuple
from ..core.types import FrameAnalysis, AnalysisResult, Keypoint

class Visualizer:
    """
    Renders standard Pose Estimation overlays with 'Iron Man' palette.
    """
    
    def __init__(self):
        # Palette (BGR)
        self.RED = (0, 0, 255)
        self.WHITE = (255, 255, 255)
        
        # Connection Colors (Matching Reference Image)
        # Right Side = Orange
        self.C_RIGHT = (0, 165, 255) 
        # Left Side = Green
        self.C_LEFT = (0, 255, 0)
        # Torso & Face = Blue/Cyan
        self.C_TORSO = (255, 200, 0) # Light Blue looking
        self.C_FACE = (255, 255, 0)  # Cyan

    def draw_skeleton(self, img: np.ndarray, keypoints: Dict[str, Keypoint]):
        """
        Draws skeleton with fixed aesthetic:
        - Points: Red with White Border
        - Lines: Fixed Limb Colors + Central Spine
        """
        h, w, _ = img.shape
        
        # 1. Define Standard Connections
        connections = [
            # Arms (Right)
            ('RIGHT_SHOULDER', 'RIGHT_ELBOW', self.C_RIGHT),
            ('RIGHT_ELBOW', 'RIGHT_WRIST', self.C_RIGHT),
            
            # Arms (Left)
            ('LEFT_SHOULDER', 'LEFT_ELBOW', self.C_LEFT),
            ('LEFT_ELBOW', 'LEFT_WRIST', self.C_LEFT),
            
            # Legs (Right)
            ('RIGHT_HIP', 'RIGHT_KNEE', self.C_RIGHT),
            ('RIGHT_KNEE', 'RIGHT_ANKLE', self.C_RIGHT),
            
            # Legs (Left)
            ('LEFT_HIP', 'LEFT_KNEE', self.C_LEFT),
            ('LEFT_KNEE', 'LEFT_ANKLE', self.C_LEFT),
            
            # Face
            ('NOSE', 'LEFT_EYE', self.C_FACE),
            ('NOSE', 'RIGHT_EYE', self.C_FACE),
            ('LEFT_EYE', 'LEFT_EAR', self.C_FACE),
            ('RIGHT_EYE', 'RIGHT_EAR', self.C_FACE),
            
            # Torso Box
            ('LEFT_SHOULDER', 'RIGHT_SHOULDER', self.C_FACE),
            ('LEFT_HIP', 'RIGHT_HIP', self.C_FACE),
            ('LEFT_SHOULDER', 'LEFT_HIP', self.C_LEFT), 
            ('RIGHT_SHOULDER', 'RIGHT_HIP', self.C_RIGHT),
        ]
        
        # 2. Draw Limb Lines
        for start_name, end_name, color in connections:
            kp1 = keypoints.get(start_name)
            kp2 = keypoints.get(end_name)
            
            if kp1 and kp2:
                p1 = (int(kp1.x * w), int(kp1.y * h))
                p2 = (int(kp2.x * w), int(kp2.y * h))
                cv2.line(img, p1, p2, color, 2, cv2.LINE_AA)

        # 3. Draw Virtual Spine (Central Line)
        # Mid-Shoulder to Mid-Hip
        ls = keypoints.get('LEFT_SHOULDER')
        rs = keypoints.get('RIGHT_SHOULDER')
        lh = keypoints.get('LEFT_HIP')
        rh = keypoints.get('RIGHT_HIP')
        
        if ls and rs and lh and rh:
            mx_shoulder = int((ls.x + rs.x) / 2 * w)
            my_shoulder = int((ls.y + rs.y) / 2 * h)
            
            mx_hip = int((lh.x + rh.x) / 2 * w)
            my_hip = int((lh.y + rh.y) / 2 * h)
            
            # Draw Spine Line (Blue)
            cv2.line(img, (mx_shoulder, my_shoulder), (mx_hip, my_hip), self.C_TORSO, 2, cv2.LINE_AA)
            
            # Draw Neck (Nose to Mid-Shoulder) - Optional but usually good
            nose = keypoints.get('NOSE')
            if nose:
                nx, ny = int(nose.x * w), int(nose.y * h)
                cv2.line(img, (nx, ny), (mx_shoulder, my_shoulder), self.C_FACE, 2, cv2.LINE_AA)

        # 4. Draw Points (Last so they are on top)
        for name, kp in keypoints.items():
            cx, cy = int(kp.x * w), int(kp.y * h)
            # Outer White Ring
            cv2.circle(img, (cx, cy), 5, self.WHITE, 2) 
            # Inner Red Dot
            cv2.circle(img, (cx, cy), 3, self.RED, -1)
            
    def _create_crop(self, img: np.ndarray, bbox_obj, label: str) -> np.ndarray:
        h, w, _ = img.shape
        x1, y1, x2, y2 = bbox_obj.x1, bbox_obj.y1, bbox_obj.x2, bbox_obj.y2
        
        # Pad bounds
        pad_x = 20
        pad_y = 20
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(w, x2 + pad_x)
        y2 = min(h, y2 + pad_y)
        
        crop = img[y1:y2, x1:x2].copy()
        
        if crop.size == 0:
            return np.zeros((200, 200, 3), dtype=np.uint8)
            
        # Add Overlay Effect
        if label == "SAGITTAL":
            overlay = np.full(crop.shape, (255, 100, 0), dtype=np.uint8) # Blue-ish
            cv2.addWeighted(overlay, 0.2, crop, 0.8, 0, crop)
        elif label == "CORONAL":
            overlay = np.full(crop.shape, (0, 255, 100), dtype=np.uint8) # Green-ish
            cv2.addWeighted(overlay, 0.2, crop, 0.8, 0, crop)
            
        cv2.putText(crop, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.WHITE, 2)
        return crop

    def _create_heatmap(self, img: np.ndarray, bbox_obj) -> np.ndarray:
        """Simulate stress heatmap on the person."""
        heatmap = img.copy()
        h, w, _ = img.shape
        x1, y1, x2, y2 = bbox_obj.x1, bbox_obj.y1, bbox_obj.x2, bbox_obj.y2
        
        mask = np.zeros((h, w), dtype=np.uint8)
        center = ((x1+x2)//2, (y1+y2)//2)
        axes = ((x2-x1)//2, (y2-y1)//2)
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        mask = cv2.GaussianBlur(mask, (99, 99), 0)
        colored_mask = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
        cv2.addWeighted(colored_mask, 0.6, heatmap, 0.4, 0, heatmap)
        
        cv2.putText(heatmap, "STRESS MAP", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.WHITE, 2)
        return heatmap

    def render_multiview(self, img: np.ndarray, analysis: FrameAnalysis) -> Dict[str, np.ndarray]:
        """Returns main, sagittal, coronal, heatmap views."""
        main_view = img.copy()
        sagittal_view = np.zeros_like(img)
        coronal_view = np.zeros_like(img)
        heatmap_view = np.zeros_like(img)
        
        if not analysis.results:
            return {
                "main": main_view,
                "sagittal": sagittal_view,
                "coronal": coronal_view,
                "heatmap": heatmap_view
            }
            
        res = analysis.results[0]
        
        # 1. Main View Rendering (Simple Skeleton)
        if res.keypoints:
            self.draw_skeleton(main_view, res.keypoints)
            
        # Draw HUD (Simplified)
        self.draw_hud(main_view, res)
        
        # 2. Gen Sub-Views
        sagittal_view = self._create_crop(main_view, res.bbox, "SAGITTAL")
        coronal_view = self._create_crop(main_view, res.bbox, "CORONAL")
        heatmap_view = self._create_heatmap(img, res.bbox)
        
        return {
            "main": main_view,
            "sagittal": sagittal_view,
            "coronal": coronal_view,
            "heatmap": heatmap_view
        }

    def draw_hud(self, img: np.ndarray, result: AnalysisResult):
        """Draws floating text stats."""
        x1, y1 = result.bbox.x1, result.bbox.y1
        metrics = result.metrics
        if not metrics: return

        lines = [
            f"ID: {result.person_id}",
            f"Cobb: {metrics.cobb_angle_thoracic:.1f}" if metrics.cobb_angle_thoracic else "Cobb: N/A",
            f"Flex: {metrics.lumbar_flexion:.1f}" if metrics.lumbar_flexion else "Flex: N/A",
            f"Score: {metrics.health_score:.0f}",
        ]
        
        card_x = max(0, x1 - 180)
        card_y = y1
        for i, line in enumerate(lines):
            c = self.WHITE
            if "Score" in line:
               val = metrics.health_score
               if val > 80: c = (0, 255, 0)
               elif val > 50: c = (0, 255, 255)
               else: c = (0, 0, 255)

            cv2.putText(img, line, (card_x + 8, card_y + 20 + (i*25)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, c, 2)
