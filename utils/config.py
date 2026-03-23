"""
Global configuration and constants for PPE Detection Platform.
"""

from enum import Enum
from pathlib import Path

# ============================================================================
# PROJECT PATHS
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "ppe_detection.db"
MODELS_PATH = PROJECT_ROOT / "models"
LOGS_PATH = PROJECT_ROOT / "logs"

# Create directories if they don't exist
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
MODELS_PATH.mkdir(parents=True, exist_ok=True)
LOGS_PATH.mkdir(parents=True, exist_ok=True)

# ============================================================================
# DATABASE
# ============================================================================
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
SQLALCHEMY_ECHO = False  # Set to True for SQL debugging

# ============================================================================
# USER ROLES
# ============================================================================
class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "Admin"
    SUPERVISOR = "Supervisor"
    VIEWER = "Viewer"


# ============================================================================
# PPE CLASSES & COMPLIANCE (MUST MATCH YOUR data.yaml EXACTLY)
# ============================================================================
PPE_CLASSES = {
    "boots": 0,      # Class 0
    "gloves": 1,     # Class 1 (NOT required - dataset limitation)
    "helmet": 2,     # Class 2
    "human": 3,      # Class 3 (person - NOT a PPE item)
    "vest": 4,       # Class 4
}

# Required PPE items for compliance (excluding gloves due to dataset limitations)
REQUIRED_PPE = ["helmet", "vest", "boots"]

# All detectable PPE items (excluding gloves and human)
DETECTABLE_PPE = ["helmet", "vest", "boots"]

# PPE CLASS COLORS (RGB for visualization)
PPE_COLORS = {
    "boots": (255, 0, 255),       # Magenta
    "gloves": (255, 255, 0),      # Cyan
    "helmet": (0, 255, 0),        # Green
    "vest": (255, 0, 0),          # Blue
}


# ============================================================================
# COMPLIANCE STATUS
# ============================================================================
class ComplianceStatus(str, Enum):
    """PPE compliance status."""
    GREEN = "✅ Compliant"
    YELLOW = "⚠️ Partial"
    RED = "❌ Non-Compliant"


# Compliance classification rules
COMPLIANCE_RULES = {
    "green": {"min_required": 3},      # All 3 required items
    "yellow": {"min_required": 1},     # 1-2 items
    "red": {"min_required": 0},        # 0 items
}

# ============================================================================
# YOLO DETECTION
# ============================================================================
YOLO_PERSON_MODEL = "yolov8m.pt"      # Pre-trained COCO model for person detection
YOLO_PPE_MODEL = "ppe_best.pt"        # UPDATED: Custom trained PPE model

DEFAULT_CONFIDENCE = 0.5
DEFAULT_IOU = 0.45
    
# ============================================================================
# STREAMLIT UI          
# ============================================================================
PAGE_ICON = "🛡️"
PAGE_TITLE = "PPE Detection & Compliance Platform"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"

# ============================================================================
# SESSION STATE KEYS
# ============================================================================
SESSION_USER_ID = "user_id"
SESSION_USER_EMAIL = "user_email"
SESSION_USER_NAME = "user_name"
SESSION_USER_ROLE = "user_role"
SESSION_ORG_ID = "org_id"
SESSION_ORG_NAME = "org_name"