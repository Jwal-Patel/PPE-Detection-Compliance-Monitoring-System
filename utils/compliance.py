"""
PPE compliance classification module.
Determines compliance status (Green/Yellow/Red) based on detected PPE items.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass

from utils.config import REQUIRED_PPE, DETECTABLE_PPE, ComplianceStatus


@dataclass
class ComplianceResult:
    """Data class for compliance classification result."""
    
    status: str  # "Green", "Yellow", or "Red"
    detected_ppe: List[str]
    required_ppe: List[str]
    missing_ppe: List[str]
    confidence_score: float  # 0-1, how confident we are in this assessment
    
    def __repr__(self) -> str:
        return f"<ComplianceResult(status={self.status}, detected={self.detected_ppe})>"


def classify_compliance(detected_ppe: List[str]) -> ComplianceResult:
    """
    Classify worker compliance based on detected PPE items.
    
    Rules:
        - GREEN: All required items present (helmet, vest, boots)
        - YELLOW: 1 or more required items present (but not all)
        - RED: No required items present
    
    Args:
        detected_ppe: List of detected PPE class names (lowercase)
        
    Returns:
        ComplianceResult with status and details
    """
    detected_set = set(item.lower() for item in detected_ppe)
    required_set = set(REQUIRED_PPE)
    
    # Find missing items
    missing_ppe = list(required_set - detected_set)
    
    # Count detected required items
    detected_required_count = len(detected_set & required_set)
    
    # Determine status
    if detected_required_count == len(required_set):
        # All required items detected
        status = ComplianceStatus.GREEN
        confidence = 0.95
    elif detected_required_count > 0:
        # Some (but not all) required items detected
        status = ComplianceStatus.YELLOW
        confidence = 0.85
    else:
        # No required items detected
        status = ComplianceStatus.RED
        confidence = 0.95
    
    return ComplianceResult(
        status=status,
        detected_ppe=sorted(list(detected_set)),
        required_ppe=sorted(list(required_set)),
        missing_ppe=sorted(missing_ppe),
        confidence_score=confidence
    )


def calculate_compliance_percentage(compliance_results: List[ComplianceResult]) -> float:
    """
    Calculate overall compliance percentage.
    
    Args:
        compliance_results: List of ComplianceResult objects
        
    Returns:
        Compliance percentage (0-100)
    """
    if not compliance_results:
        return 0.0
    
    compliant_count = sum(
        1 for result in compliance_results
        if result.status == ComplianceStatus.GREEN
    )
    
    return (compliant_count / len(compliance_results)) * 100


def get_compliance_summary(compliance_results: List[ComplianceResult]) -> Dict:
    """
    Generate compliance summary statistics.
    
    Args:
        compliance_results: List of ComplianceResult objects
        
    Returns:
        Dict with summary stats
    """
    if not compliance_results:
        return {
            "total": 0,
            "compliant": 0,
            "partial": 0,
            "non_compliant": 0,
            "compliance_rate": 0.0,
        }
    
    compliant = sum(1 for r in compliance_results if r.status == ComplianceStatus.GREEN)
    partial = sum(1 for r in compliance_results if r.status == ComplianceStatus.YELLOW)
    non_compliant = sum(1 for r in compliance_results if r.status == ComplianceStatus.RED)
    
    return {
        "total": len(compliance_results),
        "compliant": compliant,
        "partial": partial,
        "non_compliant": non_compliant,
        "compliance_rate": (compliant / len(compliance_results)) * 100 if compliance_results else 0.0,
    }


def get_ppe_breakdown(compliance_results: List[ComplianceResult]) -> Dict[str, int]:
    """
    Get count of each PPE item detected across all workers.
    
    Args:
        compliance_results: List of ComplianceResult objects
        
    Returns:
        Dict with PPE item counts (only for detectable items)
    """
    ppe_counts = {ppe: 0 for ppe in DETECTABLE_PPE}
    
    for result in compliance_results:
        for ppe in result.detected_ppe:
            if ppe in ppe_counts:
                ppe_counts[ppe] += 1
    
    return ppe_counts


def get_missing_items_summary(compliance_results: List[ComplianceResult]) -> Dict[str, int]:
    """
    Get count of missing PPE items across non-compliant and partial workers.
    
    Args:
        compliance_results: List of ComplianceResult objects
        
    Returns:
        Dict with missing item counts (only for required items)
    """
    missing_counts = {ppe: 0 for ppe in REQUIRED_PPE}
    
    for result in compliance_results:
        if result.status in [ComplianceStatus.YELLOW, ComplianceStatus.RED]:
            for missing in result.missing_ppe:
                if missing in missing_counts:
                    missing_counts[missing] += 1
    
    return missing_counts