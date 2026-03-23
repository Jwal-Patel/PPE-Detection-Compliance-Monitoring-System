"""
Utils package for configuration, detection, compliance, and visualization.
"""

from utils.config import (
    PROJECT_ROOT,
    DATABASE_URL,
    DATABASE_PATH,
    MODELS_PATH,
    LOGS_PATH,
    UserRole,
    PPE_CLASSES,
    REQUIRED_PPE,
    PPE_COLORS,
    ComplianceStatus,
    COMPLIANCE_RULES,
    YOLO_PERSON_MODEL,
    YOLO_PPE_MODEL,
    DEFAULT_CONFIDENCE,
    DEFAULT_IOU,
    PAGE_ICON,
    PAGE_TITLE,
    LAYOUT,
    INITIAL_SIDEBAR_STATE,
    SESSION_USER_ID,
    SESSION_USER_EMAIL,
    SESSION_USER_NAME,
    SESSION_USER_ROLE,
    SESSION_ORG_ID,
    SESSION_ORG_NAME,
)

# Phase 3: Video Processing
from utils.video_processing import VideoProcessor, WebcamProcessor
from utils.realtime_detection import RealtimeDetectionService

# ?? REMOVED: Lazy imports to prevent circular dependency with Auth.db
# These are only imported when actually needed in pages/modules

__all__ = [
    # Paths
    "PROJECT_ROOT",
    "DATABASE_URL",
    "DATABASE_PATH",
    "MODELS_PATH",
    "LOGS_PATH",
    # Enums & Config
    "UserRole",
    "ComplianceStatus",
    "PPE_CLASSES",
    "REQUIRED_PPE",
    "PPE_COLORS",
    "COMPLIANCE_RULES",
    "YOLO_PERSON_MODEL",
    "YOLO_PPE_MODEL",
    "DEFAULT_CONFIDENCE",
    "DEFAULT_IOU",
    "PAGE_ICON",
    "PAGE_TITLE",
    "LAYOUT",
    "INITIAL_SIDEBAR_STATE",
    "SESSION_USER_ID",
    "SESSION_USER_EMAIL",
    "SESSION_USER_NAME",
    "SESSION_USER_ROLE",
    "SESSION_ORG_ID",
    "SESSION_ORG_NAME",
    # Phase 3
    "VideoProcessor",
    "WebcamProcessor",
    "RealtimeDetectionService",
]