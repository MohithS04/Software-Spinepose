import os
import sys
import cv2
import time
import requests
import numpy as np
from io import BytesIO

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spine_engine.core.session import HybridEngine
from spine_engine.core.storage import KnowledgeBase

# Reference Data Sources (Public Domain / Creative Commons from Wikimedia)
REFERENCES = [
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/e/e2/Scoliosis_X-ray.jpg",
        "condition": "scoliosis_reference",
        "desc": "Scoliosis (Posterior-Anterior View)"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/0/0b/ScheuermannDiseaseT6to10.png",
        "condition": "kyphosis_reference",
        "desc": "Scheuermann's Kyphosis (Wedge Vertebrae)"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/5/5b/Scheuermanns70.jpg",
        "condition": "kyphosis_severe_reference",
        "desc": "Severe Kyphosis (70 degree curve)"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/3/34/Lateral_lumbar_x_ray.jpg",
        "condition": "normal_lumbar_reference",
        "desc": "Normal Lumbar Spine (Lateral)"
    }
]

def ingest_references():
    print("Initializing Spine-AI Hybrid Engine for Ingestion...")
    engine = HybridEngine()
    engine.load_models()
    kb = KnowledgeBase(db_root="spine_db")
    print("Engine Ready.\n")

    for ref in REFERENCES:
        print(f"Processing: {ref['desc']}...")
        try:
            # Download with headers to avoid 403
            print(f"  Downloading from {ref['url']}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(ref['url'], headers=headers, timeout=10)
            response.raise_for_status()
            
            # Convert to OpenCV Image
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if frame is None:
                print("  ERROR: Failed to decode image.")
                continue

            # Analyze
            print("  Analyzing spinal posture...")
            # We assume the image is a "frame" for the engine
            # Note: Engine might expect a person in a video frame, but let's see how it handles X-rays.
            # If the engine relies on BodyPose (MoveNet), it might fail on X-rays without a person.
            # However, the user asked to "add those pictures to backend". 
            # If the engine *fails* to detect a person (likely for X-rays), we should still save it as a reference 
            # but maybe without the full metrics if pose detection fails.
            
            # For this task, we will try to process it. If pose detection fails, 
            # we might need a fallback way to just save the image to the KB.
            
            analysis = engine.process_frame(frame)
            
            analysis = engine.process_frame(frame)
            
            # Save to RAG
            if analysis.results:
                entry_id = kb.save_entry(analysis, frame, activity_context=ref['condition'], domain="medical")
                print(f"  SUCCESS: Ingested as Entry ID: {entry_id} (With Pose Metrics)")
            else:
                print("  NOTE: No pose detected (Expected for X-rays). Saving as Raw Reference...")
                entry_id = kb.save_reference(frame, condition=ref['condition'], description=ref['desc'], domain="medical")
                print(f"  SUCCESS: Ingested as Entry ID: {entry_id} (Reference Image Only)")

        except Exception as e:
            print(f"  FAILED: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    # Ensure raw save fallback if needed
    # We might need to modify KnowledgeBase to allow saving without analysis results 
    # if we just want to store "Reference Images" for RAG retrieval.
    ingest_references()
