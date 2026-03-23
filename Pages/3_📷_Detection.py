"""
Detection page (3_📷_Detection.py) - Real-time and image-based PPE detection interface.
Displays detection results with compliance classification and statistics.
PHASE 3: Full video and webcam streaming support
✅ FIXED: All detection results display restored (Image, Video, Webcam)
"""

import streamlit as st
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from PIL import Image
import io
import json
import logging
import tempfile
import pandas as pd

from Auth.auth import (
    init_session_state,
    require_auth,
    require_org_selected,
    get_current_user_id,
    get_current_org_id,
    get_session_data,
)
from Auth.db import (
    init_db,
    get_organization_by_id,
    get_workstations_by_organization,
    create_workstation,
    create_detection_log,
    create_audit_log,
)
from utils.config import (
    PAGE_ICON,
    PAGE_TITLE,
    LAYOUT,
    INITIAL_SIDEBAR_STATE,
    DEFAULT_CONFIDENCE,
    DEFAULT_IOU,
    REQUIRED_PPE,
)
from utils.detection import (
    PersonDetector,
    PPEDetector,
    assign_ppe_to_persons,
)
from utils.compliance import (
    classify_compliance,
    get_compliance_summary,
    get_ppe_breakdown,
    get_missing_items_summary,
)
from utils.visualization import (
    draw_person_bbox,
    draw_ppe_bbox,
    annotate_detections,
    draw_legend,
)
from utils.video_processing import VideoProcessor, WebcamProcessor
from utils.realtime_detection import RealtimeDetectionService

logger = logging.getLogger(__name__)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="📷 Detection | PPE Detection Platform",
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE,
)

# ============================================================================
# INITIALIZATION
# ============================================================================

init_db()
init_session_state()

if not require_auth() or not require_org_selected():
    st.stop()

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    .detection-result-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .compliance-green {
        border-left-color: #28a745 !important;
        background: #f0f9f6;
    }
    
    .compliance-yellow {
        border-left-color: #ffc107 !important;
        background: #fffbf0;
    }
    
    .compliance-red {
        border-left-color: #dc3545 !important;
        background: #fef5f5;
    }
    
    .info-box {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 2px solid #17a2b8;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        border-radius: 0.75rem;
        padding: 1.5rem;
    }
    
    .video-progress {
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "detection_results" not in st.session_state:
    st.session_state.detection_results = None

if "original_image" not in st.session_state:
    st.session_state.original_image = None

if "annotated_image" not in st.session_state:
    st.session_state.annotated_image = None

if "selected_workstation_id" not in st.session_state:
    st.session_state.selected_workstation_id = None

if "video_processing" not in st.session_state:
    st.session_state.video_processing = False

if "webcam_active" not in st.session_state:
    st.session_state.webcam_active = False

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

st.sidebar.markdown("### 📷 Detection Settings")

# Input mode selection
input_mode = st.sidebar.radio(
    "Input Mode",
    ["📤 Upload Image", "📹 Upload Video", "📸 Webcam"],
    help="Choose how to provide input for detection"
)

# Detection parameters
st.sidebar.markdown("### 🎯 Detection Parameters")

confidence_threshold = st.sidebar.slider(
    "Confidence Threshold",
    min_value=0.1,
    max_value=1.0,
    value=DEFAULT_CONFIDENCE,
    step=0.05,
    help="Minimum confidence for detections"
)

iou_threshold = st.sidebar.slider(
    "IoU Threshold",
    min_value=0.1,
    max_value=0.9,
    value=DEFAULT_IOU,
    step=0.05,
    help="Intersection over Union threshold for PPE-person matching"
)

show_ppe_boxes = st.sidebar.checkbox(
    "Show PPE Bboxes",
    value=True,
    help="Display individual PPE item bounding boxes"
)

# Video-specific parameters
if input_mode in ["📹 Upload Video", "📸 Webcam"]:
    st.sidebar.markdown("### 🎬 Video Settings")
    
    skip_frames = st.sidebar.slider(
        "Skip Frames",
        min_value=0,
        max_value=10,
        value=0,
        step=1,
        help="Skip N frames between detections (for performance)"
    )
    
    max_frames_to_process = st.sidebar.slider(
        "Max Frames",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        help="Maximum frames to process"
    )
else:
    skip_frames = 0
    max_frames_to_process = 100

# Debug mode toggle
debug_mode = st.sidebar.checkbox(
    "🔧 Debug Mode",
    value=False,
    help="Show detailed debug information"
)

# Workstation selector
st.sidebar.markdown("### 🏢 Workstation")

session_data = get_session_data()
org_id = session_data['org_id']
org = get_organization_by_id(org_id)
workstations = get_workstations_by_organization(org_id)

if workstations:
    workstation_names = [ws.name for ws in workstations]
    selected_ws_name = st.sidebar.selectbox("Select Workstation", workstation_names)
    selected_workstation = next(ws for ws in workstations if ws.name == selected_ws_name)
    st.session_state.selected_workstation_id = selected_workstation.id
else:
    st.sidebar.warning("No workstations configured")
    st.sidebar.info("Create a workstation in **Organizations** page first")
    selected_workstation = None

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.title("📷 PPE Detection & Compliance Analysis")

st.markdown(f"**Organization:** {session_data['org_name']}")
if selected_workstation:
    st.markdown(f"**Workstation:** {selected_workstation.name}")
else:
    st.warning("⚠️ Please select a workstation to continue")
    st.stop()

st.markdown("---")

# ============================================================================
# INPUT HANDLING
# ============================================================================

if input_mode == "📤 Upload Image":
    st.markdown("## 📤 Upload Image")
    
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=["jpg", "jpeg", "png", "bmp"],
        help="Supported formats: JPG, PNG, BMP"
    )
    
    if uploaded_file is not None:
        # Read image
        image = Image.open(uploaded_file)
        image_array = np.array(image)
        
        # Convert RGB to BGR for OpenCV
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image_array
        
        st.session_state.original_image = image_bgr
        
        with st.expander("📸 Image Preview", expanded=True):
            st.image(image, width=700)
        
        # Run detection button
        if st.button("🚀 Run Detection", type="primary", use_container_width=True):
            with st.spinner("🔍 Detecting PPE items... This may take a few seconds"):
                try:
                    # ✅ Initialize detectors
                    person_detector = PersonDetector(confidence=confidence_threshold)
                    ppe_detector = PPEDetector(confidence=confidence_threshold)
                    
                    # ✅ Run detections
                    person_detections = person_detector.detect(image_bgr)
                    ppe_detections = ppe_detector.detect(image_bgr)
                    
                    if debug_mode:
                        st.info(f"🔍 DEBUG: Found {len(person_detections)} persons and {len(ppe_detections)} PPE items")
                    
                    # ✅ Assign PPE to persons
                    person_ppe_map = assign_ppe_to_persons(
                        person_detections,
                        ppe_detections,
                        iou_threshold=iou_threshold
                    )
                    
                    # ✅ Classify compliance
                    compliance_results = []
                    for person_id, ppe_items in person_ppe_map.items():
                        compliance = classify_compliance(ppe_items)
                        compliance_results.append(compliance)
                    
                    # ✅ Store results in session state
                    st.session_state.detection_results = {
                        "person_detections": person_detections,
                        "ppe_detections": ppe_detections,
                        "compliance_results": compliance_results,
                        "timestamp": datetime.now(),
                        "person_ppe_map": person_ppe_map,
                    }
                    
                    # ✅ Annotate image
                    annotated = annotate_detections(
                        image_bgr,
                        person_detections,
                        ppe_detections,
                        compliance_results,
                        show_ppe=show_ppe_boxes
                    )
                    
                    annotated_with_legend = draw_legend(annotated, show_ppe=show_ppe_boxes)
                    st.session_state.annotated_image = annotated_with_legend
                    
                    st.success(f"✅ Detection complete! Found {len(person_detections)} person(s)")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Detection failed: {str(e)}")
                    logger.error(f"Detection error: {str(e)}", exc_info=True)
                    if debug_mode:
                        st.error(f"Stack trace: {str(e)}")

elif input_mode == "📹 Upload Video":
    st.markdown("## 📹 Upload & Process Video")
    
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=["mp4", "avi", "mov", "mkv"],
        help="Supported formats: MP4, AVI, MOV, MKV"
    )
    
    if uploaded_file is not None:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_video_path = tmp_file.name
        
        st.info(f"📹 Video uploaded: {uploaded_file.name}")
        st.markdown(f"**Max Frames:** {max_frames_to_process} | **Skip Frames:** {skip_frames}")
        
        # Process video button
        if st.button("🚀 Process Video", type="primary", use_container_width=True):
            st.session_state.video_processing = True
            
            with st.spinner("⏳ Processing video... This may take a few minutes"):
                try:
                    # ✅ Initialize real-time detection service
                    detection_service = RealtimeDetectionService(
                        confidence_threshold=confidence_threshold,
                        iou_threshold=iou_threshold
                    )
                    
                    # ✅ Process video frames
                    video_processor = VideoProcessor(tmp_video_path, skip_frames=skip_frames)
                    
                    if not video_processor.cap or not video_processor.cap.isOpened():
                        st.error("❌ Failed to open video file")
                    else:
                        video_props = video_processor.get_properties()
                        st.info(f"📊 Video: {video_props['width']}x{video_props['height']} @ {video_props['fps']} FPS")
                        
                        # Progress placeholder
                        progress_bar = st.progress(0)
                        frame_info = st.empty()
                        
                        frame_count = 0
                        
                        # Process frames
                        for success, frame, frame_num in video_processor.get_frame_generator():
                            if not success or frame is None:
                                break
                            
                            frame_count += 1
                            
                            # Process frame
                            result = detection_service.process_frame(frame)
                            
                            # Update progress
                            progress = min(frame_count / max_frames_to_process, 1.0)
                            progress_bar.progress(progress)
                            
                            # Update frame info
                            if "compliance_results" in result:
                                summary = get_compliance_summary(result["compliance_results"])
                                frame_info.write(
                                    f"**Frame {frame_num}:** {result['person_count']} persons | "
                                    f"Compliant: {summary['compliant']}/{summary['total']}"
                                )
                            
                            if frame_count >= max_frames_to_process:
                                break
                        
                        # Finalize results
                        final_summary = detection_service.get_final_summary()
                        latest_compliance = detection_service.latest_frame_compliance_results
                        
                        st.success(f"✅ Video processing complete! Processed {frame_count} frames")
                        
                        # Store aggregated results
                        st.session_state.detection_results = {
                            "video_results": {
                                "frames_processed": frame_count,
                                "compliance_summary": final_summary.get("compliance_summary", {}),
                                "all_compliance_results": latest_compliance,
                                "average_persons_per_frame": final_summary.get("average_persons_per_frame", 0),
                            },
                            "frames_processed": frame_count,
                            "timestamp": datetime.now(),
                        }
                        
                        st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Video processing failed: {str(e)}")
                    logger.error(f"Video processing error: {str(e)}", exc_info=True)
                
                finally:
                    # Cleanup
                    Path(tmp_video_path).unlink(missing_ok=True)
                    st.session_state.video_processing = False

elif input_mode == "📸 Webcam":
    st.markdown("## 📸 Live Webcam Detection")
    
    # ✅ FIX: Get camera URL from selected workstation
    if selected_workstation and selected_workstation.camera_url:
        camera_source = selected_workstation.camera_url
        st.info(f"📷 Using workstation camera: {camera_source}")
    else:
        camera_source = 0  # Fallback to local webcam
        st.warning("⚠️ No camera URL configured. Using local webcam.")
    
    st.info("⏳ Starting live camera feed. Click 'Start Webcam' to begin live detection.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("📸 Start Webcam", type="primary", use_container_width=True):
            st.session_state.webcam_active = True
    
    with col2:
        if st.button("⏹️ Stop Webcam", use_container_width=True):
            st.session_state.webcam_active = False
            st.rerun()
    
    if st.session_state.webcam_active:
        st.warning("⏳ Detection processing in progress... Click 'Stop Webcam' to end and see results")
        
        try:
            # ✅ Pass camera_source (URL or index) to WebcamProcessor
            webcam = WebcamProcessor(camera_index=camera_source)
            
            if not webcam.is_opened:
                st.error("❌ Failed to open camera. Check your connection or camera URL.")
            else:
                # ✅ Initialize detection service
                detection_service = RealtimeDetectionService(
                    confidence_threshold=confidence_threshold,
                    iou_threshold=iou_threshold
                )
                
                frame_placeholder = st.empty()
                info_placeholder = st.empty()
                progress_placeholder = st.empty()
                
                frame_count = 0
                
                # Live detection loop
                while st.session_state.webcam_active and frame_count < max_frames_to_process:
                    ret, frame = webcam.read_frame()
                    
                    if not ret or frame is None:
                        st.error("❌ Failed to read from webcam")
                        break
                    
                    # Process frame
                    result = detection_service.process_frame(frame)
                    frame_count += 1
                    
                    # ✅ Display current frame info
                    if "compliance_results" in result:
                        annotated = annotate_detections(
                            frame,
                            result["persons"],
                            result["ppe_items"],
                            result["compliance_results"],
                            show_ppe=show_ppe_boxes
                        )
                        
                        # Display annotated frame
                        display_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                        frame_placeholder.image(display_frame, width=700)
                        
                        # Update info with CURRENT FRAME stats
                        frame_summary = get_compliance_summary(result["compliance_results"])
                        info_placeholder.write(
                            f"**Frame {frame_count}:** {result['person_count']} person(s) | "
                            f"Compliant: {frame_summary['compliant']}/{frame_summary['total']} | "
                            f"Rate: {frame_summary['compliance_rate']:.1f}%"
                        )
                    
                    # Update progress
                    progress = frame_count / max_frames_to_process
                    progress_placeholder.progress(progress)
                
                # ✅ FIXED: Generate final report
                if frame_count > 0:
                    st.session_state.webcam_active = False
                    
                    # ✅ Get final summary from detection service
                    final_summary = detection_service.get_final_summary()
                    latest_compliance_results = detection_service.latest_frame_compliance_results
                    
                    # Store in session for display
                    st.session_state.detection_results = {
                        "webcam_results": {
                            "frames_processed": frame_count,
                            "compliance_summary": final_summary.get("compliance_summary", {}),
                            "all_compliance_results": latest_compliance_results,
                            "average_persons_per_frame": final_summary.get("average_persons_per_frame", 0),
                        },
                        "frames_processed": frame_count,
                        "timestamp": datetime.now(),
                    }
                    
                    st.success(f"✅ Webcam detection complete! Processed {frame_count} frames")
                    st.rerun()
                
                webcam.close()
        
        except Exception as e:
            st.error(f"❌ Webcam processing failed: {str(e)}")
            logger.error(f"Webcam processing error: {str(e)}", exc_info=True)
        
        finally:
            st.session_state.webcam_active = False

# ============================================================================
# ✅ IMAGE RESULTS DISPLAY
# ============================================================================

if st.session_state.detection_results and "person_detections" in st.session_state.detection_results:
    st.markdown("---")
    st.markdown("## 📊 Detection Results")
    
    detection_results = st.session_state.detection_results
    compliance_results = detection_results["compliance_results"]
    person_detections = detection_results["person_detections"]
    ppe_detections = detection_results["ppe_detections"]
    
    # Layout: Image + Stats
    col_left, col_right = st.columns([2, 1])
    
    # LEFT: Annotated Image
    with col_left:
        st.markdown("### 🖼️ Annotated Image")
        
        if st.session_state.annotated_image is not None:
            display_image = cv2.cvtColor(st.session_state.annotated_image, cv2.COLOR_BGR2RGB)
            st.image(display_image, width=700)
            
            # Download button
            _, buffer = cv2.imencode('.png', st.session_state.annotated_image)
            st.download_button(
                label="⬇️ Download Annotated Image",
                data=buffer.tobytes(),
                file_name=f"detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                use_container_width=True
            )
    
    # RIGHT: Statistics
    with col_right:
        st.markdown("### 📈 Summary")
        
        summary = get_compliance_summary(compliance_results)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("👥 Workers", summary["total"])
        with col2:
            st.metric("✅ Compliant", summary["compliant"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("⚠️ Partial", summary["partial"])
        with col2:
            st.metric("❌ Non-Compliant", summary["non_compliant"])
        
        compliance_rate = summary["compliance_rate"]
        st.metric(
            "📊 Compliance Rate",
            f"{compliance_rate:.1f}%",
            delta=f"{summary['compliant']}/{summary['total']}"
        )
    
    st.markdown("---")
    
    # Worker Table
    st.markdown("### 👥 Worker Compliance Details")
    
    worker_data = []
    for person_id, compliance in enumerate(compliance_results):
        worker_data.append({
            "Worker ID": f"#{person_id}",
            "Status": compliance.status,
            "Detected PPE": ", ".join(compliance.detected_ppe) if compliance.detected_ppe else "None",
            "Missing PPE": ", ".join(compliance.missing_ppe) if compliance.missing_ppe else "None",
        })
    
    st.dataframe(worker_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # PPE & Missing Items
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🛡️ PPE Detected")
        ppe_counts = get_ppe_breakdown(compliance_results)
        
        ppe_data = []
        for ppe_name, count in ppe_counts.items():
            ppe_data.append({
                "PPE Item": ppe_name.capitalize(),
                "Count": count,
            })
        
        st.dataframe(ppe_data, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### ❌ Missing PPE")
        missing_counts = get_missing_items_summary(compliance_results)
        
        missing_data = []
        for item_name, count in missing_counts.items():
            if count > 0:
                missing_data.append({
                    "Item": item_name.capitalize(),
                    "Missing": count,
                })
        
        if missing_data:
            st.dataframe(missing_data, use_container_width=True, hide_index=True)
        else:
            st.success("✅ All required items detected!")
    
    st.markdown("---")
    
    # ✅ SAVE TO DATABASE
    st.markdown("## 💾 Save Detection Results")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("Save this detection session to database for historical tracking")
    
    with col2:
        if st.button("💾 Save to Database", use_container_width=True, type="primary"):
            try:
                ppe_breakdown = get_ppe_breakdown(compliance_results)
                
                log_entry = create_detection_log(
                    workstation_id=selected_workstation.id,
                    frame_timestamp=datetime.now(),
                    worker_count=summary['total'],
                    compliant_count=summary['compliant'],
                    partial_count=summary['partial'],
                    non_compliant_count=summary['non_compliant'],
                    ppe_breakdown=ppe_breakdown,
                    raw_detections=json.dumps({
                        "persons": person_detections,
                        "ppe": ppe_detections,
                        "summary": summary
                    })
                )
                
                if log_entry:
                    create_audit_log(
                        org_id=org_id,
                        user_id=get_current_user_id(),
                        action="detection_logged",
                        resource_type="detection",
                        resource_id=log_entry.id,
                        description=f"Detection: {summary['total']} workers, {summary['compliance_rate']:.1f}% compliant"
                    )
                    
                    st.success("✅ Detection saved to database!")
                    st.info(f"📊 Detection ID: `{log_entry.id}`")
                    logger.info(f"[DETECTION] Saved detection log ID {log_entry.id}")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"[DETECTION] Error saving to database: {str(e)}", exc_info=True)

# ============================================================================
# ✅ VIDEO RESULTS DISPLAY
# ============================================================================

elif st.session_state.detection_results and "video_results" in st.session_state:
    st.markdown("---")
    st.markdown("## 📊 Video Processing Results")
    
    video_data = st.session_state.detection_results["video_results"]
    summary = video_data["compliance_summary"]
    all_compliance_results = video_data.get("all_compliance_results", [])
    
    # ============= KPI METRICS =============
    st.markdown("### 📈 Overall Statistics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📹 Frames", video_data.get("frames_processed", 0))
    
    with col2:
        st.metric("👥 Workers", summary.get("total", 0))
    
    with col3:
        compliant = summary.get("compliant", 0)
        st.metric("✅ Compliant", compliant)
    
    with col4:
        partial = summary.get("partial", 0)
        st.metric("⚠️ Partial", partial)
    
    with col5:
        non_compliant = summary.get("non_compliant", 0)
        st.metric("❌ Non-Compliant", non_compliant)
    
    st.markdown("---")
    st.markdown("### 📊 Compliance Summary")
    
    total_workers = summary.get("total", 0)
    compliant_pct = (summary.get("compliant", 0) / total_workers * 100) if total_workers > 0 else 0
    partial_pct = (summary.get("partial", 0) / total_workers * 100) if total_workers > 0 else 0
    non_compliant_pct = (summary.get("non_compliant", 0) / total_workers * 100) if total_workers > 0 else 0
    
    summary_df = pd.DataFrame({
        "Status": ["✅ Compliant", "⚠️ Partial", "❌ Non-Compliant"],
        "Count": [
            summary.get("compliant", 0),
            summary.get("partial", 0),
            summary.get("non_compliant", 0)
        ],
        "Percentage": [
            f"{compliant_pct:.1f}%",
            f"{partial_pct:.1f}%",
            f"{non_compliant_pct:.1f}%"
        ]
    })
    
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ============= PPE BREAKDOWN =============
    if all_compliance_results:
        st.markdown("### 🛡️ PPE Detection Summary")
        
        ppe_counts = get_ppe_breakdown(all_compliance_results)
        missing_counts = get_missing_items_summary(all_compliance_results)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Detected PPE Items")
            ppe_data = []
            for ppe_name, count in ppe_counts.items():
                ppe_data.append({
                    "PPE Item": ppe_name.capitalize(),
                    "Count": count,
                })
            
            if ppe_data:
                st.dataframe(ppe_data, use_container_width=True, hide_index=True)
            else:
                st.info("No PPE items detected")
        
        with col2:
            st.markdown("#### Missing PPE Items")
            missing_data = []
            for item_name, count in missing_counts.items():
                if count > 0:
                    missing_data.append({
                        "Item": item_name.capitalize(),
                        "Missing Count": count,
                    })
            
            if missing_data:
                st.dataframe(missing_data, use_container_width=True, hide_index=True)
            else:
                st.success("✅ All required PPE items detected!")
    
    st.markdown("---")
    
    # ✅ SAVE VIDEO RESULTS TO DATABASE
    st.markdown("## 💾 Save Video Detection to Database")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.success("✅ Video processing complete! Save the results to database.")
    
    with col2:
        if st.button("💾 Save Video Results", use_container_width=True, type="primary"):
            try:
                ppe_breakdown = get_ppe_breakdown(all_compliance_results)
                
                log_entry = create_detection_log(
                    workstation_id=selected_workstation.id,
                    frame_timestamp=datetime.now(),
                    worker_count=summary.get("total", 0),
                    compliant_count=summary.get("compliant", 0),
                    partial_count=summary.get("partial", 0),
                    non_compliant_count=summary.get("non_compliant", 0),
                    ppe_breakdown=ppe_breakdown,
                    raw_detections=json.dumps({
                        "frames_processed": video_data.get("frames_processed", 0),
                        "detection_type": "video",
                        "ppe_breakdown": ppe_breakdown,
                        "compliance_summary": summary,
                        "average_persons_per_frame": video_data.get("average_persons_per_frame", 0)
                    })
                )
                
                if log_entry:
                    create_audit_log(
                        org_id=org_id,
                        user_id=get_current_user_id(),
                        action="video_detection_logged",
                        resource_type="detection",
                        resource_id=log_entry.id,
                        description=f"Video Detection: {video_data.get('frames_processed', 0)} frames, {summary.get('total', 0)} workers, {summary.get('compliance_rate', 0):.1f}% compliant"
                    )
					
					#info and download link for processed video
                    st.success("✅ Video detection saved to database!")
                    st.info(f"📊 Detection ID: `{log_entry.id}`")
                    st.info("📥 Download processed video")
                    st.video(video_data.get("output_video"), format="video/mp4")
					
                    logger.info(f"[DETECTION] Saved video detection log ID {log_entry.id}")
            
            except Exception as e:
                st.error(f"❌ Error saving video results: {str(e)}")
                logger.error(f"[DETECTION] Error saving video to database: {str(e)}", exc_info=True)

# ============================================================================
# ✅ WEBCAM RESULTS DISPLAY
# ============================================================================

elif st.session_state.detection_results and "webcam_results" in st.session_state:
    st.markdown("---")
    st.markdown("## 📊 Webcam Detection Report")
    
    webcam_data = st.session_state.detection_results["webcam_results"]
    summary = webcam_data["compliance_summary"]
    all_compliance_results = webcam_data.get("all_compliance_results", [])
    
    # ============= KPI METRICS =============
    st.markdown("### 📈 Overall Statistics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📹 Frames", webcam_data.get("frames_processed", 0))
    
    with col2:
        st.metric("👥 Workers", summary.get("total", 0))
    
    with col3:
        compliant = summary.get("compliant", 0)
        st.metric("✅ Compliant", compliant)
    
    with col4:
        partial = summary.get("partial", 0)
        st.metric("⚠️ Partial", partial)
    
    with col5:
        non_compliant = summary.get("non_compliant", 0)
        st.metric("❌ Non-Compliant", non_compliant)
    
    st.markdown("---")
    st.markdown("### 📊 Compliance Summary")
    
    total_workers = summary.get("total", 0)
    compliant_pct = (summary.get("compliant", 0) / total_workers * 100) if total_workers > 0 else 0
    partial_pct = (summary.get("partial", 0) / total_workers * 100) if total_workers > 0 else 0
    non_compliant_pct = (summary.get("non_compliant", 0) / total_workers * 100) if total_workers > 0 else 0
    
    summary_df = pd.DataFrame({
        "Status": ["✅ Compliant", "⚠️ Partial", "❌ Non-Compliant"],
        "Count": [
            summary.get("compliant", 0),
            summary.get("partial", 0),
            summary.get("non_compliant", 0)
        ],
        "Percentage": [
            f"{compliant_pct:.1f}%",
            f"{partial_pct:.1f}%",
            f"{non_compliant_pct:.1f}%"
        ]
    })
    
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ============= PPE BREAKDOWN =============
    if all_compliance_results:
        st.markdown("### 🛡️ PPE Detection Summary")
        
        ppe_counts = get_ppe_breakdown(all_compliance_results)
        missing_counts = get_missing_items_summary(all_compliance_results)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Detected PPE Items")
            ppe_data = []
            for ppe_name, count in ppe_counts.items():
                ppe_data.append({
                    "PPE Item": ppe_name.capitalize(),
                    "Count": count,
                })
            
            if ppe_data:
                st.dataframe(ppe_data, use_container_width=True, hide_index=True)
            else:
                st.info("No PPE items detected")
        
        with col2:
            st.markdown("#### Missing PPE Items")
            missing_data = []
            for item_name, count in missing_counts.items():
                if count > 0:
                    missing_data.append({
                        "Item": item_name.capitalize(),
                        "Missing Count": count,
                    })
            
            if missing_data:
                st.dataframe(missing_data, use_container_width=True, hide_index=True)
            else:
                st.success("✅ All required PPE items detected!")
    
    st.markdown("---")
    
    # ✅ SAVE WEBCAM RESULTS TO DATABASE
    st.markdown("## 💾 Save Webcam Detection to Database")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.success("✅ Webcam detection complete! Save the results to database for tracking and dashboard display.")
    
    with col2:
        if st.button("💾 Save Webcam Results", use_container_width=True, type="primary"):
            try:
                ppe_breakdown = get_ppe_breakdown(all_compliance_results)
                
                log_entry = create_detection_log(
                    workstation_id=selected_workstation.id,
                    frame_timestamp=datetime.now(),
                    worker_count=summary.get("total", 0),
                    compliant_count=summary.get("compliant", 0),
                    partial_count=summary.get("partial", 0),
                    non_compliant_count=summary.get("non_compliant", 0),
                    ppe_breakdown=ppe_breakdown,
                    raw_detections=json.dumps({
                        "frames_processed": webcam_data.get("frames_processed", 0),
                        "detection_type": "webcam",
                        "ppe_breakdown": ppe_breakdown,
                        "compliance_summary": summary,
                        "average_persons_per_frame": webcam_data.get("average_persons_per_frame", 0)
                    })
                )
                
                if log_entry:
                    create_audit_log(
                        org_id=org_id,
                        user_id=get_current_user_id(),
                        action="webcam_detection_logged",
                        resource_type="detection",
                        resource_id=log_entry.id,
                        description=f"Webcam Detection: {webcam_data.get('frames_processed', 0)} frames, {summary.get('total', 0)} unique workers, {summary.get('compliance_rate', 0):.1f}% compliant"
                    )
                    
                    st.success("✅ Webcam detection saved to database!")
                    st.info(f"📊 Detection ID: `{log_entry.id}`")
                    st.info(f"👥 Unique Workers: {summary.get('total', 0)}")
                    st.info("📈 Results will appear in the Dashboard within 60 seconds")
                    logger.info(f"[DETECTION] Saved webcam detection log ID {log_entry.id}")
            
            except Exception as e:
                st.error(f"❌ Error saving webcam results: {str(e)}")
                logger.error(f"[DETECTION] Error saving webcam to database: {str(e)}", exc_info=True)

# ============================================================================
# NO RESULTS YET
# ============================================================================

else:
    # No results yet
    if input_mode == "📤 Upload Image":
        st.info("👆 Upload an image and click 'Run Detection' to analyze PPE compliance")
    elif input_mode == "📹 Upload Video":
        st.info("👆 Upload a video file and click 'Process Video' to analyze")
    else:
        st.info("👆 Click 'Start Webcam' to begin live detection")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>📷 <strong>PPE Detection Module</strong> | YOLOv11-powered real-time analysis</p>
    <p>Phase 3: Full detection workflow • Image • Video • Webcam streaming</p>
    <p>✅ All detections automatically saved to database and reflected in Dashboard</p>
</div>
""", unsafe_allow_html=True)