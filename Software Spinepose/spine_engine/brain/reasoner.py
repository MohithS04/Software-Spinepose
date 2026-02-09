from google import genai
import os
from typing import Optional, Dict
from ..core.types import SpineMetrics

class GeminiReasoner:
    """
    Interface to Google Gemini 3 (Flash Preview)
    for high-level reasoning about biomechanics.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if self.api_key:
            # The new Client automatically looks for GEMINI_API_KEY or can take it directly
            self.client = genai.Client(api_key=self.api_key)
            self.available = True
        else:
            print("Warning: No GEMINI_API_KEY found. Reasoning module disabled.")
            self.available = False
            
    def analyze_context(self, metrics: SpineMetrics, context_type: str = "medical") -> str:
        """
        Generate a natural language assessment using Gemini 3 Flash Preview.
        context_type: 'medical' | 'sports'
        """
        if not self.available:
            return "AI Analysis Unavailable (Key Missing)"
            
        prompt = ""
        if context_type == "medical":
            prompt = f"""
            Act as a Lead Radiologist writing a formal X-Ray/MRI Diagnostic Report.
            
            PATIENT BIOMETRICS (Derived from Computer Vision):
            - Thoracic Cobb Angle: {metrics.cobb_angle_thoracic:.1f} degrees
            - Lumbar Lordosis (Flexion): {metrics.lumbar_flexion:.1f} degrees
            - Postural Health Index: {metrics.health_score:.1f}/100
            
            TASK:
            Provide a concise "Impression" section for the report.
            Focus strictly on spinal alignment, potential scoliosis (if Cobb > 10), and lordosis.
            Use professional medical terminology (e.g., "dextroscoliosis", "hypolordosis").
            Do NOT mention "I am an AI". Output ONLY the clinical impression.
            """
        else:
            prompt = f"""
            Act as an Elite Biomechanics Coach analyzing a movement screen.
            
            ATHLETE METRICS:
            - Spine Flexion: {metrics.lumbar_flexion:.1f} degrees
            - Stability Index: {metrics.health_score:.1f}/100
            
            TASK:
            Provide a direct "Correction Cue".
            Focus on neutral spine maintenance and injury prevention (disk herniation risk).
            Keep it punchy and actionable (e.g., "Cue: Brace core...").
            """
            
        try:
            response = self.client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            return f"AI Error: {str(e)}"
