
import os
import cv2
import requests
import numpy as np
from spine_engine.core.session import HybridEngine
from spine_engine.core.storage import KnowledgeBase

# Sports References (Resolved URLs)
REFERENCES = [
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/8/84/Squatting.jpg",
        "condition": "squat_side_view",
        "desc": "Squat (Side View)",
        "domain": "sports"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/e/e8/Romanian-deadlift-1.png",
        "condition": "deadlift_side_view",
        "desc": "Deadlift (Side View Diagram)",
        "domain": "sports"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/3/36/H._J._Whigham,_golfer_(in_follow_through).PNG",
        "condition": "golf_swing_follow_through",
        "desc": "Golf Swing (Follow Through)",
        "domain": "sports"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/d/d7/Summer_Streets_NYC_2023-08-19,_female_runner_on_Park_Av_and_66th,_Upper_East_Side,_Manhattan.jpg",
        "condition": "runner_side_view",
        "desc": "Runner (Side View)",
        "domain": "sports"
    }
]

def ingest_sports():
    print("Initializing Spine-AI Hybrid Engine for Sports Ingestion...")
    # config = EngineConfig(mode="sports") 
    engine = HybridEngine() # Use default init
    engine.load_models() # Initialize YOLO and Pose models
    kb = KnowledgeBase()
    
    # User-Agent to avoid 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }

    print("Engine Ready.\n")
    
    for ref in REFERENCES:
        print(f"Processing: {ref['desc']} ({ref['domain']})...")
        try:
            # Download
            print(f"  Downloading from {ref['url']}...")
            response = requests.get(ref['url'], headers=headers, timeout=10)
            response.raise_for_status()
            
            # Convert to OpenCV Image
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if frame is None:
                print("  FAILED: Could not decode image.")
                continue
                
            print("  Analyzing spinal posture...")
            analysis = engine.process_frame(frame)
            
            # Save to RAG with Domain Labeling
            if analysis.results:
                # If pose is detected, perfect!
                entry_id = kb.save_entry(analysis, frame, activity_context=ref['condition'], domain=ref['domain'])
                print(f"  SUCCESS: Ingested as Entry ID: {entry_id} (With Pose Metrics) [Domain: {ref['domain']}]")
            else:
                # Fallback to reference save
                print("  NOTE: No pose detected (or low confidence). Saving as labeled Reference...")
                entry_id = kb.save_reference(frame, condition=ref['condition'], description=ref['desc'], domain=ref['domain'])
                print(f"  SUCCESS: Ingested as Entry ID: {entry_id} (Reference Only) [Domain: {ref['domain']}]")

        except Exception as e:
            print(f"  FAILED: {e}")
        print("-" * 30)

if __name__ == "__main__":
    ingest_sports()
