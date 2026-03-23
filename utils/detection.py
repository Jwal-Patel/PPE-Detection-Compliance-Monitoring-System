"""
YOLO detection module for PPE and person detection.
Handles model loading, inference, and detection results processing.
"""

from typing import List, Tuple, Dict, Optional
import cv2
import numpy as np
from pathlib import Path
import streamlit as st
from ultralytics import YOLO

from utils.config import (
    YOLO_PERSON_MODEL,
    YOLO_PPE_MODEL,
    DEFAULT_CONFIDENCE,
    DEFAULT_IOU,
    MODELS_PATH,
)


# ============================================================================
# CACHED MODEL LOADERS (Streamlit-friendly)
# ============================================================================

@st.cache_resource
def load_person_detector_cached(model_path: str = YOLO_PERSON_MODEL):
    """Cache-wrapped YOLOv11 person detector model loading."""
    return YOLO(model_path)


@st.cache_resource
def load_ppe_detector_cached(model_path: str = None):
    """Cache-wrapped YOLOv11 PPE detector model loading."""
    model_path = model_path or str(MODELS_PATH / YOLO_PPE_MODEL)
    if not Path(model_path).exists():
        raise FileNotFoundError(f"PPE model not found at {model_path}")
    return YOLO(model_path)


# ============================================================================
# PERSON DETECTOR CLASS
# ============================================================================

class PersonDetector:
    """
    Detects persons in images/frames using YOLOv8 pre-trained model (COCO).
    """
    
    def __init__(self, confidence: float = DEFAULT_CONFIDENCE):
        """
        Initialize person detector.
        
        Args:
            confidence: Detection confidence threshold (0-1)
        """
        self.confidence = confidence
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load YOLOv8 COCO model for person detection."""
        try:
            self.model = load_person_detector_cached(YOLO_PERSON_MODEL)
        except Exception as e:
            raise RuntimeError(f"Failed to load person detection model: {str(e)}")
    
    def detect(self, image: np.ndarray) -> List[Dict]:
        """
        Detect persons in image.
        
        Args:
            image: Input image (numpy array, BGR format)
            
        Returns:
            List of detection dicts with keys:
                - bbox: [x1, y1, x2, y2] coordinates
                - confidence: Detection confidence score
                - class_id: Class ID (0 for person in COCO)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            results = self.model(image, conf=self.confidence, verbose=False)
            detections = []
            
            if results and len(results) > 0:
                boxes = results[0].boxes
                
                for box in boxes:
                    # Filter for person class (class_id = 0 in COCO)
                    if int(box.cls[0]) == 0:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        detections.append({
                            "bbox": [float(x1), float(y1), float(x2), float(y2)],
                            "confidence": float(box.conf[0].cpu().numpy()),
                            "class_id": 0,  # Person
                        })
            
            return detections
        
        except Exception as e:
            raise RuntimeError(f"Detection failed: {str(e)}")


# ============================================================================
# PPE DETECTOR CLASS
# ============================================================================

class PPEDetector:
    """
    Detects PPE items in images/frames using custom YOLOv11 model.
    Skips gloves detection due to dataset limitations.
    """
    
    def __init__(self, model_path: Optional[str] = None, confidence: float = DEFAULT_CONFIDENCE):
        """
        Initialize PPE detector.
        
        Args:
            model_path: Path to custom PPE model weights (.pt file)
            confidence: Detection confidence threshold (0-1)
        """
        self.confidence = confidence
        self.model_path = model_path or str(MODELS_PATH / YOLO_PPE_MODEL)
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load custom PPE detection model."""
        try:
            if not Path(self.model_path).exists():
                raise FileNotFoundError(f"PPE model not found at {self.model_path}")
            
            self.model = load_ppe_detector_cached(self.model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load PPE model: {str(e)}")
    
    def detect(self, image: np.ndarray) -> List[Dict]:
        """
        Detect PPE items in image.
        Skips gloves class due to dataset limitations.
        
        Args:
            image: Input image (numpy array, BGR format)
            
        Returns:
            List of detection dicts with keys:
                - bbox: [x1, y1, x2, y2] coordinates
                - class: PPE class name
                - class_id: Class ID
                - confidence: Detection confidence score
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            results = self.model(image, conf=self.confidence, verbose=False)
            detections = []
            
            if results and len(results) > 0:
                boxes = results[0].boxes
                names = results[0].names  # Class names mapping
                
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    class_id = int(box.cls[0])
                    class_name = names[class_id]
                    
                    # Skip 'human' class - use PersonDetector for humans instead
                    if class_name.lower() == 'human':
                        continue
                    
                    # Skip 'gloves' class - dataset does not support reliable glove detection
                    if class_name.lower() == 'gloves':
                        continue
                    
                    detections.append({
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "class": class_name.lower(),
                        "class_id": class_id,
                        "confidence": float(box.conf[0].cpu().numpy()),
                    })
            
            return detections
        
        except Exception as e:
            raise RuntimeError(f"PPE detection failed: {str(e)}")


# ============================================================================
# PPE-TO-PERSON ASSIGNMENT (IMPROVED)
# ============================================================================

def assign_ppe_to_persons(
    person_detections: List[Dict],
    ppe_detections: List[Dict],
    iou_threshold: float = 0.1
) -> Dict:
    """
    Match PPE detections to persons based on spatial overlap (IMPROVED).
    
    Enhanced algorithm:
    1. For each PPE item, find the person with best IoU overlap
    2. Assign PPE to person if IoU >= threshold
    3. Fallback: If no overlap found, assign to closest person (centroid distance)
    
    Args:
        person_detections: List of person bboxes
        ppe_detections: List of PPE bboxes with class labels
        iou_threshold: IoU threshold for assignment (lowered to 0.1 for flexibility)
        
    Returns:
        Dict mapping person_id to list of detected PPE items
        {
            0: ["helmet", "vest", "boots"],
            1: ["vest"],
            ...
        }
    """
    person_ppe_map = {i: [] for i in range(len(person_detections))}
    
    # If no persons detected, return empty map
    if not person_detections:
        return person_ppe_map
    
    for ppe in ppe_detections:
        ppe_bbox = ppe["bbox"]
        best_iou = -1
        best_person_id = -1
        best_distance = float('inf')
        
        # Step 1: Try to find person by IoU overlap
        for person_id, person in enumerate(person_detections):
            person_bbox = person["bbox"]
            iou = calculate_iou(ppe_bbox, person_bbox)
            
            if iou >= iou_threshold:
                if iou > best_iou:
                    best_iou = iou
                    best_person_id = person_id
        
        # Step 2: Fallback - assign to closest person by centroid distance
        if best_person_id == -1:
            ppe_centroid = get_bbox_centroid(ppe_bbox)
            
            for person_id, person in enumerate(person_detections):
                person_bbox = person["bbox"]
                person_centroid = get_bbox_centroid(person_bbox)
                distance = euclidean_distance(ppe_centroid, person_centroid)
                
                if distance < best_distance:
                    best_distance = distance
                    best_person_id = person_id
        
        # Step 3: Assign PPE to best matching person
        if best_person_id >= 0:
            person_ppe_map[best_person_id].append(ppe["class"])
    
    return person_ppe_map


def calculate_iou(bbox1: List[float], bbox2: List[float]) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.
    
    Args:
        bbox1: [x1, y1, x2, y2]
        bbox2: [x1, y1, x2, y2]
        
    Returns:
        IoU score (0-1)
    """
    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2
    
    # Calculate intersection
    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)
    
    if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
        return 0.0
    
    inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
    
    # Calculate union
    bbox1_area = (x1_max - x1_min) * (y1_max - y1_min)
    bbox2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = bbox1_area + bbox2_area - inter_area
    
    if union_area == 0:
        return 0.0
    
    return inter_area / union_area


def get_bbox_centroid(bbox: List[float]) -> Tuple[float, float]:
    """
    Calculate centroid (center point) of a bounding box.
    
    Args:
        bbox: [x1, y1, x2, y2]
        
    Returns:
        Tuple of (center_x, center_y)
    """
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def euclidean_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate Euclidean distance between two points.
    
    Args:
        point1: (x1, y1)
        point2: (x2, y2)
        
    Returns:
        Distance value
    """
    x1, y1 = point1
    x2, y2 = point2
    return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Load and preprocess image for detection.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Image as numpy array (BGR format)
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to load image from {image_path}")
    return image