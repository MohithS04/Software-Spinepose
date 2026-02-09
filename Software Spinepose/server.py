
import cv2
import asyncio
import base64
import json
import uvicorn
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from spine_engine.core.session import HybridEngine
from spine_engine.utils.visualization import Visualizer
from spine_engine.brain.reasoner import GeminiReasoner
from spine_engine.core.storage import KnowledgeBase

app = FastAPI()

# Mount web directory
app.mount("/static", StaticFiles(directory="web"), name="static")

# Global Engine Instances
try:
    print("Initializing Spine-AI Engine...")
    engine = HybridEngine()
    engine.load_models()
    viz = Visualizer()
    reasoner = GeminiReasoner()
    kb = KnowledgeBase(db_root="spine_db")
    
    # Initialize Patient DB
    from spine_engine.core.storage import PatientDatabase
    patient_db = PatientDatabase(db_root="spine_db")
    
    print("Engine Ready.")
    
except Exception as e:
    print(f"CRITICAL: Engine Init Failed: {e}")

@app.get("/patients")
async def get_patients():
    return patient_db.get_all_patients()

@app.post("/patients")
async def create_patient(data: dict):
    return patient_db.add_patient(data)

@app.get("/")
async def get():
    with open("web/index.html", "r") as f:
        html = f.read()
    html = html.replace('href="styles.css?v=2"', 'href="/static/styles.css?v=2"')
    html = html.replace('src="script.js"', 'src="/static/script.js"')
    return HTMLResponse(html)

@app.post("/analyze_file")
async def analyze_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return JSONResponse({"error": "Invalid image data"}, status_code=400)
            
        # Process
        analysis = engine.process_frame(frame)
        
        # Visualize
        views = viz.render_multiview(frame, analysis)
        
        # Encode Helper
        def encode_img(img):
            _, buffer = cv2.imencode('.jpg', img)
            return base64.b64encode(buffer).decode('utf-8')
        
        metrics_data = {}
        report_text = "Analysis complete. No significant spine detected."
        
        if analysis.results:
            res = analysis.results[0]
            if res.metrics:
                metrics_data = {
                    "cobb_angle": round(res.metrics.cobb_angle_thoracic, 1),
                    "lumbar_flexion": round(res.metrics.lumbar_flexion, 1),
                    "health_score": round(res.metrics.health_score, 1)
                }
                
                kb.save_entry(analysis, frame, activity_context="upload_analysis")
                
                try:
                    report_text = reasoner.analyze_context(res.metrics, context_type="medical")
                except Exception as e:
                    print(f"AI Error: {e}")
                    report_text = "AI Diagnostic Service Unavailable."

        return {
            "image": encode_img(views['main']),
            "image_sagittal": encode_img(views['sagittal']),
            "image_coronal": encode_img(views['coronal']),
            "image_heatmap": encode_img(views['heatmap']),
            "metrics": metrics_data,
            "report": report_text
        }
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client Connected.")
    
    state = {
        "active": False,
        "mode": "medical",
        "recording": False,
        "activity": "standing"
    }

    async def stream_video():
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        try:
            frame_count = 0
            while True:
                if not state["active"]:
                    await asyncio.sleep(0.1)
                    continue

                ret, frame = cap.read()
                if not ret:
                    print("Camera read failed.")
                    break
                    
                # Process
                analysis = engine.process_frame(frame)
                
                # RAG Storage
                if state["recording"] and frame_count % 30 == 0:
                    entry_id = kb.save_entry(analysis, frame, activity_context=state["activity"])
                    if entry_id:
                        print(f"RAG Saved: {entry_id} [{state['activity']}]")
                
                frame_count += 1
                
                # Visualize
                views = viz.render_multiview(frame, analysis)
                
                def encode_img(img):
                    _, buffer = cv2.imencode('.jpg', img)
                    return base64.b64encode(buffer).decode('utf-8')

                # Metrics Initialization (Defensive)
                metrics_data = {}
                
                if analysis.results:
                    res = analysis.results[0]
                    if res.metrics:
                        metrics_data = {
                            "cobb_angle": round(res.metrics.cobb_angle_thoracic, 1) if res.metrics.cobb_angle_thoracic else 0,
                            "lumbar_flexion": round(res.metrics.lumbar_flexion, 1) if res.metrics.lumbar_flexion else 0,
                            "cervical_flexion": round(res.metrics.cervical_flexion, 1) if res.metrics.cervical_flexion else 0,
                            "symmetry_index": round(res.metrics.symmetry_index, 1) if res.metrics.symmetry_index else 0,
                            "health_score": round(res.metrics.health_score, 1)
                        }

                response = {
                    "image": encode_img(views['main']),
                    "image_sagittal": encode_img(views['sagittal']),
                    "image_coronal": encode_img(views['coronal']),
                    "image_heatmap": encode_img(views['heatmap']),
                    "metrics": metrics_data,
                    "status": "recording" if state["recording"] else "active",
                    "mode": state["mode"]
                }
                
                await websocket.send_json(response)
                await asyncio.sleep(0.03)
                
        except Exception as e:
            print(f"Stream Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cap.release()
            print("Camera released.")

    stream_task = asyncio.create_task(stream_video())

    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "start":
                state["active"] = True
                print("Stream Started.")
            elif command == "stop":
                state["active"] = False
                state["recording"] = False
                print("Stream Stopped.")
            elif command == "set_mode":
                state["mode"] = data.get("value", "medical")
            elif command == "record_toggle":
                state["recording"] = not state["recording"]
                print(f"Recording State: {state['recording']}")
            elif command == "set_activity":
                state["activity"] = data.get("value", "standing")
                
    except WebSocketDisconnect:
        print("WebSocket Disconnected.")
        stream_task.cancel()
    except Exception as e:
        print(f"WebSocket Error: {e}")
        stream_task.cancel()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
