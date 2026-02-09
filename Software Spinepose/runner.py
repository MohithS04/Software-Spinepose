import argparse
import cv2
import sys
import os
from spine_engine.core.session import HybridEngine
from spine_engine.brain.reasoner import GeminiReasoner
from spine_engine.utils.visualization import Visualizer

def main():
    parser = argparse.ArgumentParser(description="Spine-AI Engine Runner")
    parser.add_argument("--input", type=str, required=True, help="Path to input image/video")
    parser.add_argument("--output", type=str, default="output.jpg", help="Path to save result")
    parser.add_argument("--mode", type=str, default="medical", choices=["medical", "sports"], help="Analysis mode")
    args = parser.parse_args()
    
    # Init Modules
    print("[1/4] Initializing Engine...")
    engine = HybridEngine()
    engine.load_models()
    
    print("[2/4] Initializing Brain...")
    # Pass API Key from env if available
    reasoner = GeminiReasoner()
    
    print("[3/4] Initializing Visualizer...")
    viz = Visualizer()
    
    # Load Input
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.")
        return
        
    frame = cv2.imread(args.input)
    if frame is None:
        print("Error: Could not read image.")
        return
        
    print(f"[4/4] Processing Frame ({args.mode} mode)...")
    analysis = engine.process_frame(frame)
    
    # Enrichment Phase
    for res in analysis.results:
        if res.metrics and reasoner.available:
            print(f"   > Querying Gemini for Person ID {res.person_id}...")
            insight = reasoner.analyze_context(res.metrics, context_type=args.mode)
            print(f"   > Gemini Insight: {insight}")
            # Attach insight to metrics for potential display (not implemented in viz yet, but printed)
            
    # Visualize
    out_frame = viz.render(frame, analysis)
    
    # Save
    cv2.imwrite(args.output, out_frame)
    print(f"Done. Result saved to {args.output}")

if __name__ == "__main__":
    main()
