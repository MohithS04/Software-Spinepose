
import os
import json
import time
import cv2
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import asdict
from .types import FrameAnalysis

class KnowledgeBase:
    """
    RAG Storage Engine.
    Persists Spine Analysis data for future retrieval.
    Structure:
    - db/
        - index.jsonl (Metadata + Metrics)
        - images/ (Snapshots)
        - vectors/ (Embeddings - generic placeholder)
    """
    
    def __init__(self, db_root: str = "spine_db"):
        self.root = db_root
        self.images_dir = os.path.join(self.root, "images")
        self.index_path = os.path.join(self.root, "index.jsonl")
        
        os.makedirs(self.images_dir, exist_ok=True)
        
    def save_entry(self, analysis: FrameAnalysis, image: Any, activity_context: str = "unknown", domain: str = "medical") -> str:
        """
        Saves a single frame analysis to the RAG DB.
        Returns the unique Entry ID.
        """
        if not analysis.results:
            return ""
            
        # Prepare Metadata from Analysis
        res = analysis.results[0]
        meta = {
            "metrics": {
                "cobb_angle": res.metrics.cobb_angle_thoracic,
                "flexion": res.metrics.lumbar_flexion,
                "health_score": res.metrics.health_score
            },
            "keypoints_summary": list(res.keypoints.keys()) 
        }
        
        return self._persist(image, activity_context, meta, domain)

    def save_reference(self, image: Any, condition: str, description: str, domain: str = "medical") -> str:
        """
        Saves a reference image (e.g., Internet X-ray) without requiring pose analysis.
        """
        meta = {
            "type": "reference",
            "condition": condition,
            "description": description,
            "metrics": {} # Placeholder
        }
        return self._persist(image, condition, meta, domain)

    def _persist(self, image: Any, activity: str, metadata: Dict, domain: str) -> str:
        entry_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Save Image Snapshot
        img_filename = f"{entry_id}.jpg"
        img_path = os.path.join(self.images_dir, img_filename)
        cv2.imwrite(img_path, image)
        
        record = {
            "id": entry_id,
            "timestamp": timestamp,
            "activity": activity,
            "domain": domain, # medical or sports
            "image_path": img_path,
            **metadata
        }
        
        # Append to Index (JSONL)
        with open(self.index_path, "a") as f:
            f.write(json.dumps(record) + "\n")
            
        return entry_id

    def query(self, activity_filter: Optional[str] = None) -> List[Dict]:
        """
        Simple retrieval by activity tag.
        In a full RAG, this would use vector similarity.
        """
        results = []
        if not os.path.exists(self.index_path):
            return results
            
        with open(self.index_path, "r") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if activity_filter:
                        if record.get("activity") == activity_filter:
                            results.append(record)
                    else:
                        results.append(record)
                except:
                    continue
        return results

class PatientDatabase:
    """
    Simple JSON-based Patient Database.
    """
    def __init__(self, db_root: str = "spine_db"):
        self.root = db_root
        self.patients_file = os.path.join(self.root, "patients.json")
        
        if not os.path.exists(self.patients_file):
            with open(self.patients_file, "w") as f:
                json.dump([], f)
    
    def add_patient(self, patient_data: Dict) -> Dict:
        """
        Adds a new patient.
        """
        patients = self.get_all_patients()
        
        # Simple ID generation if not provided
        if "id" not in patient_data or not patient_data["id"]:
             patient_data["id"] = str(uuid.uuid4())[:8]
             
        patients.append(patient_data)
        
        with open(self.patients_file, "w") as f:
            json.dump(patients, f, indent=4)
            
        return patient_data
        
    def get_all_patients(self) -> List[Dict]:
        """
        Returns all patients.
        """
        if not os.path.exists(self.patients_file):
            return []
            
        with open(self.patients_file, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    
    def get_patient(self, patient_id: str) -> Optional[Dict]:
        patients = self.get_all_patients()
        for p in patients:
            if p["id"] == patient_id:
                return p
        return None
