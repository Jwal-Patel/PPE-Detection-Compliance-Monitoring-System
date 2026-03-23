"""
Video processing utilities for real-time PPE detection.
Handles video file decoding, frame extraction, and streaming.
PHASE 3: Real-time video and webcam support.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Generator, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Process video files for frame-by-frame PPE detection.
    Supports both file-based and streaming (webcam) inputs.
    """
    
    def __init__(self, video_path: str, skip_frames: int = 0):
        """
        Initialize video processor.
        
        Args:
            video_path: Path to video file or camera index (0 for default webcam)
            skip_frames: Skip N frames between detections (for performance)
        """
        self.video_path = video_path
        self.skip_frames = skip_frames
        self.frame_count = 0
        self.fps = 30  # Default FPS
        self.frame_width = 640
        self.frame_height = 480
        
        self.cap = None
        self._open_video()
    
    def _open_video(self) -> bool:
        """
        Open video source (file or webcam).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to open as file first
            if isinstance(self.video_path, str) and Path(self.video_path).exists():
                self.cap = cv2.VideoCapture(self.video_path)
                logger.info(f"[VIDEO] Opened video file: {self.video_path}")
            else:
                # Try as camera index
                try:
                    cam_index = int(self.video_path)
                    self.cap = cv2.VideoCapture(cam_index)
                    logger.info(f"[VIDEO] Opened webcam: camera {cam_index}")
                except (ValueError, TypeError):
                    logger.error(f"[VIDEO] Invalid video source: {self.video_path}")
                    return False
            
            # Check if successfully opened
            if not self.cap.isOpened():
                logger.error("[VIDEO] Failed to open video source")
                return False
            
            # Get video properties
            self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            logger.info(f"[VIDEO] FPS: {self.fps}, Resolution: {self.frame_width}x{self.frame_height}")
            
            return True
        
        except Exception as e:
            logger.error(f"[VIDEO] Error opening video: {str(e)}")
            return False
    
    def get_frame_generator(self) -> Generator[Tuple[bool, np.ndarray, int], None, None]:
        """
        Generator that yields video frames one at a time.
        
        Yields:
            Tuple of (success, frame, frame_number)
        """
        if not self.cap or not self.cap.isOpened():
            logger.error("[VIDEO] Video source not opened")
            return
        
        frame_skip_counter = 0
        
        try:
            while True:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    logger.info("[VIDEO] End of video reached")
                    break
                
                self.frame_count += 1
                
                # Skip frames if configured
                if self.skip_frames > 0:
                    if frame_skip_counter < self.skip_frames:
                        frame_skip_counter += 1
                        continue
                    frame_skip_counter = 0
                
                # Resize for consistent processing
                frame = self._resize_frame(frame)
                
                yield (True, frame, self.frame_count)
        
        except Exception as e:
            logger.error(f"[VIDEO] Error reading frames: {str(e)}")
            yield (False, None, self.frame_count)
        
        finally:
            self.close()
    
    def _resize_frame(self, frame: np.ndarray, max_width: int = 1280) -> np.ndarray:
        """
        Resize frame to reasonable size while maintaining aspect ratio.
        
        Args:
            frame: Input frame
            max_width: Maximum width
            
        Returns:
            Resized frame
        """
        height, width = frame.shape[:2]
        
        if width > max_width:
            ratio = max_width / width
            new_height = int(height * ratio)
            frame = cv2.resize(frame, (max_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        return frame
    
    def close(self) -> None:
        """Release video resources."""
        if self.cap:
            self.cap.release()
            logger.info("[VIDEO] Video resources released")
    
    def get_properties(self) -> dict:
        """Get video properties."""
        return {
            "fps": self.fps,
            "width": self.frame_width,
            "height": self.frame_height,
            "total_frames": self.total_frames if self.total_frames > 0 else "Unknown",
            "current_frame": self.frame_count,
        }


class WebcamProcessor:
    """
    Lightweight webcam processor for real-time streaming.
    """
    
    def __init__(self, camera_index: int = 0):
        """
        Initialize webcam processor.
        
        Args:
            camera_index: Camera index (0 for default)
        """
        self.camera_index = camera_index
        self.cap = None
        self.is_opened = False
        self._open_camera()
    
    def _open_camera(self) -> bool:
        """Open camera connection."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Test read
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.is_opened = True
                logger.info(f"[WEBCAM] Camera {self.camera_index} opened successfully")
                return True
            else:
                logger.error(f"[WEBCAM] Failed to read from camera {self.camera_index}")
                return False
        
        except Exception as e:
            logger.error(f"[WEBCAM] Error opening camera: {str(e)}")
            return False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read single frame from webcam.
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.is_opened or not self.cap:
            return False, None
        
        try:
            ret, frame = self.cap.read()
            return ret, frame if ret else None
        except Exception as e:
            logger.error(f"[WEBCAM] Error reading frame: {str(e)}")
            return False, None
    
    def close(self) -> None:
        """Release webcam resources."""
        if self.cap:
            self.cap.release()
            self.is_opened = False
            logger.info("[WEBCAM] Webcam resources released")


def extract_frames_from_video(
    video_path: str,
    max_frames: int = 100,
    skip_frames: int = 0
) -> Generator[Tuple[bool, np.ndarray, int], None, None]:
    """
    Extract frames from video file with optional frame skipping.
    
    Args:
        video_path: Path to video file
        max_frames: Maximum frames to extract
        skip_frames: Skip N frames between extractions
        
    Yields:
        Tuple of (success, frame, frame_number)
    """
    processor = VideoProcessor(video_path, skip_frames=skip_frames)
    
    if not processor.cap or not processor.cap.isOpened():
        logger.error("Failed to open video")
        return
    
    frame_count = 0
    for success, frame, frame_num in processor.get_frame_generator():
        if not success:
            break
        
        if frame_count >= max_frames:
            break
        
        yield (True, frame, frame_num)
        frame_count += 1
    
    processor.close()