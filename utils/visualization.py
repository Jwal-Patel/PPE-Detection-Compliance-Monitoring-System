"""
Visualization utilities for annotating images with detection and compliance results.
"""

from typing import List, Dict, Tuple
import cv2
import numpy as np

from utils.config import PPE_COLORS, ComplianceStatus
from utils.compliance import ComplianceResult


def draw_person_bbox(
    image: np.ndarray,
    bbox: List[float],
    compliance_status: str,
    person_id: int = None,
    thickness: int = 2
) -> np.ndarray:
    """
    Draw person bounding box with color-coded compliance status.
    
    Args:
        image: Input image (numpy array, BGR)
        bbox: [x1, y1, x2, y2] coordinates
        compliance_status: ComplianceStatus (Green/Yellow/Red)
        person_id: Optional person ID to display
        thickness: Line thickness
        
    Returns:
        Annotated image
    """
    x1, y1, x2, y2 = [int(coord) for coord in bbox]
    
    # Color based on compliance status
    if compliance_status == ComplianceStatus.GREEN:
        color = (0, 255, 0)  # Green
        label = "✅ Compliant"
    elif compliance_status == ComplianceStatus.YELLOW:
        color = (0, 165, 255)  # Orange
        label = "⚠️ Partial"
    else:  # RED
        color = (0, 0, 255)  # Red
        label = "❌ Non-Compliant"
    
    # Draw bbox
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    
    # Draw label
    if person_id is not None:
        label = f"Worker {person_id}: {label}"
    
    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
    cv2.rectangle(image, (x1, y1 - label_size[1] - 8), (x1 + label_size[0], y1), color, -1)
    cv2.putText(
        image,
        label,
        (x1, y1 - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )
    
    return image


def draw_ppe_bbox(
    image: np.ndarray,
    bbox: List[float],
    ppe_class: str,
    confidence: float,
    thickness: int = 1
) -> np.ndarray:
    """
    Draw PPE bounding box with class label.
    
    Args:
        image: Input image (numpy array, BGR)
        bbox: [x1, y1, x2, y2] coordinates
        ppe_class: PPE class name
        confidence: Detection confidence
        thickness: Line thickness
        
    Returns:
        Annotated image
    """
    x1, y1, x2, y2 = [int(coord) for coord in bbox]
    color = PPE_COLORS.get(ppe_class.lower(), (255, 255, 255))
    
    # Draw bbox
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    
    # Draw label
    label = f"{ppe_class} ({confidence:.2f})"
    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
    
    cv2.rectangle(image, (x1, y1 - label_size[1] - 4), (x1 + label_size[0], y1), color, -1)
    cv2.putText(
        image,
        label,
        (x1, y1 - 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )
    
    return image


def annotate_detections(
    image: np.ndarray,
    person_detections: List[Dict],
    ppe_detections: List[Dict],
    compliance_results: List[ComplianceResult],
    show_ppe: bool = True
) -> np.ndarray:
    """
    Annotate image with all detections and compliance results.
    
    Args:
        image: Input image (numpy array, BGR)
        person_detections: List of person bboxes
        ppe_detections: List of PPE detections with class labels
        compliance_results: List of compliance results per person
        show_ppe: Whether to draw PPE bboxes
        
    Returns:
        Annotated image
    """
    annotated = image.copy()
    
    # Draw person bboxes with compliance status
    for person_id, person_det in enumerate(person_detections):
        if person_id < len(compliance_results):
            compliance = compliance_results[person_id]
            annotated = draw_person_bbox(
                annotated,
                person_det["bbox"],
                compliance.status,
                person_id=person_id
            )
    
    # Draw PPE bboxes
    if show_ppe:
        for ppe in ppe_detections:
            annotated = draw_ppe_bbox(
                annotated,
                ppe["bbox"],
                ppe["class"],
                ppe["confidence"]
            )
    
    return annotated


def draw_legend(image: np.ndarray, show_ppe: bool = True) -> np.ndarray:
    """
    Draw legend on image.
    
    Args:
        image: Input image (numpy array, BGR)
        show_ppe: Whether to include PPE items in legend
        
    Returns:
        Image with legend
    """
    legend_image = image.copy()
    y_offset = 30
    x_offset = 10
    
    # Title
    cv2.putText(
        legend_image,
        "Legend:",
        (x_offset, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )
    y_offset += 30
    
    # Compliance statuses
    statuses = [
        (ComplianceStatus.GREEN, "Compliant"),
        (ComplianceStatus.YELLOW, "Partial"),
        (ComplianceStatus.RED, "Non-Compliant"),
    ]
    
    for status, label in statuses:
        if status == ComplianceStatus.GREEN:
            color = (0, 255, 0)
        elif status == ComplianceStatus.YELLOW:
            color = (0, 165, 255)
        else:
            color = (0, 0, 255)
        
        cv2.rectangle(legend_image, (x_offset, y_offset - 15), (x_offset + 20, y_offset + 5), color, -1)
        cv2.putText(
            legend_image,
            label,
            (x_offset + 30, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )
        y_offset += 25
    
    # PPE items
    if show_ppe:
        cv2.putText(
            legend_image,
            "PPE Items:",
            (x_offset, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )
        y_offset += 25
        
        for ppe_name, ppe_color in PPE_COLORS.items():
            cv2.rectangle(legend_image, (x_offset, y_offset - 10), (x_offset + 15, y_offset + 5), ppe_color, -1)
            cv2.putText(
                legend_image,
                ppe_name.capitalize(),
                (x_offset + 25, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )
            y_offset += 20
    
    return legend_image