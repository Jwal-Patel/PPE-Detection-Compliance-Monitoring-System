"""
YOLOv11 PPE Detection Model Training Script
Trains a custom YOLOv11 model on the PPE dataset (hardhat, mask, vest, gloves, boots).

Usage:
    python train.py
    python train.py --epochs 100 --batch-size 8 --device 0 --model-size m
    python train.py --resume --resume-model models/ppe_best.pt
"""

import argparse
import sys
from pathlib import Path
import logging
from datetime import datetime

import torch
import yaml
from ultralytics import YOLO

# ============================================================================
# LOGGING CONFIGURATION (UTF-8 Support for Windows)
# ============================================================================

# Create logs directory
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging with UTF-8 encoding
log_file = LOGS_DIR / f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Custom formatter that handles Unicode
class UTF8Formatter(logging.Formatter):
    """Formatter that properly handles UTF-8 characters."""
    def format(self, record):
        return super().format(record)

# File handler with UTF-8 encoding
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Console handler with UTF-8 encoding (for Windows compatibility)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Formatter
formatter = UTF8Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent
DATA_YAML = PROJECT_ROOT / "data.yaml"
MODELS_DIR = PROJECT_ROOT / "models"
RUNS_DIR = PROJECT_ROOT / "runs"

# Create directories
MODELS_DIR.mkdir(exist_ok=True)
RUNS_DIR.mkdir(exist_ok=True)

# ============================================================================
# TRAINING CONFIGURATION (YOLOv11)
# ============================================================================

DEFAULT_CONFIG = {
    "model": "yolov11m.pt",             # YOLOv11 base model
    "epochs": 100,                      # Number of training epochs
    "batch_size": 8,                    # Batch size (YOLOv11 more memory efficient)
    "imgsz": 640,                       # Image size for training
    "patience": 20,                     # Early stopping patience
    "device": 0,                        # GPU device ID (0 for first GPU, -1 for CPU)
    "workers": 4,                       # DataLoader workers
    "optimizer": "SGD",                 # Optimizer (SGD, Adam, AdamW, RMSProp)
    "lr0": 0.01,                        # Initial learning rate
    "lrf": 0.01,                        # Final learning rate (lr0 * lrf)
    "momentum": 0.937,                  # SGD momentum
    "weight_decay": 0.0005,             # Weight decay
    "warmup_epochs": 3.0,               # Warmup epochs
    "augment": True,                    # Data augmentation
    "mosaic": 1.0,                      # Mosaic augmentation ratio
    "flipud": 0.5,                      # Flip upside-down probability
    "fliplr": 0.5,                      # Flip left-right probability
    "hsv_h": 0.015,                     # HSV hue augmentation
    "hsv_s": 0.7,                       # HSV saturation augmentation
    "hsv_v": 0.4,                       # HSV value augmentation
    "degrees": 10.0,                    # Rotation degrees
    "translate": 0.1,                   # Translation ratio
    "scale": 0.5,                       # Scale ratio
    "seed": 0,                          # Random seed
    "save": True,                       # Save training results
    "save_period": 10,                  # Save checkpoint every N epochs
    "val": True,                        # Run validation
    "half": True,                       # Use FP16 (half precision) - YOLOv11 supports well
    "cache": False,                     # Cache dataset
    "verbose": True,                    # Verbose output
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def setup_yolo_environment():
    """
    Setup proper YOLO environment for model downloading.
    Ensures models are cached in the user's home directory, not the project directory.
    """
    import os
    
    # Set proper cache directory to user's home
    yolo_home = Path.home() / '.cache' / 'yolov8'
    yolo_home.mkdir(parents=True, exist_ok=True)
    
    os.environ['YOLO_HOME'] = str(yolo_home)
    
    logger.info(f"[SETUP] YOLO cache directory: {yolo_home}")
    
    return yolo_home


def download_model_if_missing(model_name: str) -> bool:
    """
    Download YOLOv11 model if not available locally.
    Uses ultralytics' internal download mechanism with proper error handling.
    
    Args:
        model_name: Model name (e.g., 'yolov11m.pt')
        
    Returns:
        True if model is available, False otherwise
    """
    import os
    from urllib.request import urlopen
    
    logger.info(f"\n[CHECK] Verifying model availability: {model_name}")
    
    try:
        # Ensure YOLO cache is properly set
        yolo_cache = Path.home() / '.cache' / 'yolov8' / 'models'
        yolo_cache.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[DOWNLOAD] Downloading/loading {model_name}...")
        logger.info(f"           Cache directory: {yolo_cache}")
        logger.info(f"           This may take a few minutes on first run...")
        
        # Load model - ultralytics will automatically download to cache
        model = YOLO(model_name)
        
        logger.info(f"[OK] ✅ Model {model_name} successfully loaded")
        logger.info(f"     Model location: {model.model_name if hasattr(model, 'model_name') else 'Cached'}")
        
        return True
    
    except Exception as e:
        error_msg = str(e).lower()
        
        if "no such file" in error_msg or "filenotfound" in error_msg:
            logger.error(f"[ERROR] ❌ Model download failed: File not accessible")
            logger.info(f"\n[SOLUTION 1 - Automatic Download]:")
            logger.info(f"  Try again with automatic download enabled:")
            logger.info(f"  python train.py --model-size m")
            
            logger.info(f"\n[SOLUTION 2 - Manual Download]:")
            logger.info(f"  1. Go to: https://github.com/ultralytics/assets/releases")
            logger.info(f"  2. Download: {model_name}")
            logger.info(f"  3. Save to: {Path.home() / '.cache' / 'yolov8' / 'models'}")
            
            logger.info(f"\n[SOLUTION 3 - Force Reinstall]:")
            logger.info(f"  pip install --upgrade ultralytics --force-reinstall")
            logger.info(f"  python -c \"from ultralytics import YOLO; YOLO('{model_name}')\"")
            
        elif "connection" in error_msg or "timeout" in error_msg or "network" in error_msg:
            logger.error(f"[ERROR] ❌ Network error during download")
            logger.info(f"\n[TROUBLESHOOTING]:")
            logger.info(f"  1. Check internet connection")
            logger.info(f"  2. Try disabling VPN/proxy")
            logger.info(f"  3. Check firewall settings")
            logger.info(f"  4. Use a different network")
            
        else:
            logger.error(f"[ERROR] ❌ Unexpected error: {str(e)}")
        
        return False


def check_environment() -> bool:
    """
    Check if training environment is ready (CUDA, YOLOv11, dependencies, etc.).
    
    Returns:
        True if environment is valid, False otherwise
    """
    logger.info("=" * 80)
    logger.info("ENVIRONMENT CHECK")
    logger.info("=" * 80)
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    logger.info(f"Python Version: {python_version}")
    
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ required for YOLOv11")
        return False
    
    # Check PyTorch
    logger.info(f"PyTorch Version: {torch.__version__}")
    
    # Check Ultralytics (YOLOv11)
    try:
        from ultralytics import __version__
        logger.info(f"Ultralytics Version: {__version__}")
        
        # Check if YOLOv11 is available
        if int(__version__.split('.')[0]) < 8 or (int(__version__.split('.')[0]) == 8 and int(__version__.split('.')[1]) < 3):
            logger.warning("Consider upgrading ultralytics to 8.3+ for YOLOv11 support")
    except Exception as e:
        logger.error(f"Failed to check ultralytics version: {str(e)}")
        return False
    
    # Check CUDA availability
    if torch.cuda.is_available():
        logger.info(f"[OK] CUDA Available: {torch.cuda.get_device_name(0)}")
        logger.info(f"     CUDA Version: {torch.version.cuda}")
        logger.info(f"     GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        logger.warning("[WARNING] CUDA NOT available - Training will use CPU (SLOW)")
    
    return True


def validate_dataset(data_yaml_path: Path) -> bool:
    """
    Validate dataset configuration and structure for YOLOv11.
    
    Args:
        data_yaml_path: Path to data.yaml file
        
    Returns:
        True if dataset is valid, False otherwise
    """
    logger.info("\n" + "=" * 80)
    logger.info("DATASET VALIDATION (YOLOv11)")
    logger.info("=" * 80)
    
    if not data_yaml_path.exists():
        logger.error(f"[ERROR] data.yaml not found at {data_yaml_path}")
        return False
    
    logger.info(f"[OK] data.yaml found: {data_yaml_path}")
    
    # Load and validate YAML
    try:
        with open(data_yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Check if config is None (empty or invalid YAML)
        if config is None:
            logger.error("[ERROR] data.yaml is empty or invalid")
            return False
        
        logger.info(f"[OK] YAML parsed successfully")
        
        # Check required keys (YOLOv11 compatible)
        required_keys = ['path', 'train', 'val', 'nc', 'names']
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            logger.error(f"[ERROR] Missing required keys in data.yaml: {', '.join(missing_keys)}")
            return False
        
        logger.info(f"[OK] Required keys present")
        logger.info(f"     Number of classes: {config['nc']}")
        
        # Handle both dict and list formats for names (YOLOv11 compatibility)
        if isinstance(config['names'], dict):
            class_names = ', '.join(str(v) for v in config['names'].values())
        elif isinstance(config['names'], list):
            class_names = ', '.join(str(v) for v in config['names'])
        else:
            class_names = "Unknown format"
        
        logger.info(f"     Classes: {class_names}")
        
        # Validate class count
        if len(config['names']) != config['nc']:
            logger.error(f"[ERROR] Class count mismatch: nc={config['nc']} but names has {len(config['names'])} entries")
            return False
        
        logger.info(f"[OK] Class mapping validated")
        
        # Check dataset paths
        dataset_root = Path(config['path'])
        
        if not dataset_root.is_absolute():
            dataset_root = data_yaml_path.parent / dataset_root
        
        train_images = dataset_root / config['train']
        val_images = dataset_root / config['val']
        
        logger.info(f"\n     Dataset Root: {dataset_root}")
        
        if not train_images.exists():
            logger.error(f"[ERROR] Training images not found: {train_images}")
            return False
        
        logger.info(f"     [OK] Training images: {train_images}")
        train_count = len(list(train_images.glob("*.*")))
        logger.info(f"          Found {train_count} training images")
        
        if not val_images.exists():
            logger.error(f"[ERROR] Validation images not found: {val_images}")
            return False
        
        logger.info(f"     [OK] Validation images: {val_images}")
        val_count = len(list(val_images.glob("*.*")))
        logger.info(f"          Found {val_count} validation images")
        
        # Check corresponding labels
        train_labels = dataset_root / config['train'].replace('images', 'labels')
        val_labels = dataset_root / config['val'].replace('images', 'labels')
        
        if not train_labels.exists():
            logger.error(f"[ERROR] Training labels not found: {train_labels}")
            return False
        
        if not val_labels.exists():
            logger.error(f"[ERROR] Validation labels not found: {val_labels}")
            return False
        
        logger.info(f"     [OK] Label directories validated")
        
        return True
    
    except Exception as e:
        logger.error(f"[ERROR] Error validating dataset: {str(e)}", exc_info=True)
        return False


def print_config(config: dict) -> None:
    """Print training configuration."""
    logger.info("\n" + "=" * 80)
    logger.info("YOLOV11 TRAINING CONFIGURATION")
    logger.info("=" * 80)
    
    for key, value in config.items():
        logger.info(f"  {key:.<40} {value}")


def train_model(
    data_yaml: Path,
    epochs: int = 100,
    batch_size: int = 8,
    imgsz: int = 640,
    model_size: str = "m",
    device: int = 0,
    patience: int = 20,
    resume: bool = False,
    resume_model: str = None,
    **kwargs
) -> bool:
    """
    Train YOLOv11 model on PPE dataset.
    
    Args:
        data_yaml: Path to data.yaml configuration file
        epochs: Number of training epochs
        batch_size: Batch size for training
        imgsz: Image size for training
        model_size: Model size (nano, small, medium, large, xlarge)
        device: GPU device ID or -1 for CPU
        patience: Early stopping patience
        resume: Whether to resume training from checkpoint
        resume_model: Path to model checkpoint for resuming
        **kwargs: Additional arguments passed to YOLO trainer
        
    Returns:
        True if training successful, False otherwise
    """
    logger.info("\n" + "=" * 80)
    logger.info("STARTING YOLOV11 TRAINING")
    logger.info("=" * 80)
    
    try:
        # Select base model (YOLOv11)
        base_models = {
            "n": "yolov11n.pt",   # Nano - fastest
            "s": "yolov11s.pt",   # Small
            "m": "yolov11m.pt",   # Medium (recommended)
            "l": "yolov11l.pt",   # Large
            "x": "yolov11x.pt",   # XLarge - most accurate
        }
        
        if model_size not in base_models:
            logger.error(f"[ERROR] Invalid model size: {model_size}")
            logger.info(f"        Valid sizes: {', '.join(base_models.keys())}")
            return False
        
        model_name = base_models[model_size]
        logger.info(f"[OK] Using YOLOv11 base model: {model_name}")
        
        # DOWNLOAD MODEL IF MISSING
        if not download_model_if_missing(model_name):
            return False
        
        # Load or resume model
        if resume and resume_model and Path(resume_model).exists():
            logger.info(f"[LOAD] Resuming training from: {resume_model}")
            model = YOLO(resume_model)
        else:
            logger.info(f"[LOAD] Loading base model: {model_name}")
            model = YOLO(model_name)
        
        # Print model info
        logger.info(f"\n[INFO] Model Summary:")
        try:
            logger.info(f"       Parameters: {sum(p.numel() for p in model.model.parameters()):,}")
        except:
            logger.info(f"       Model loaded successfully")
        
        # Prepare training arguments (YOLOv11 optimized)
        train_args = {
            "data": str(data_yaml),
            "epochs": epochs,
            "imgsz": imgsz,
            "batch": batch_size,
            "patience": patience,
            "device": device,
            "save": True,
            "save_period": 10,
            "project": str(RUNS_DIR),
            "name": f"ppe_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "exist_ok": False,
            "verbose": True,
            "seed": 42,
            "deterministic": True,  # YOLOv11 feature for reproducibility
            "half": True,            # FP16 precision (YOLOv11 handles well)
        }
        
        # Add custom arguments
        train_args.update(kwargs)
        
        print_config(train_args)
        
        # Start training
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING IN PROGRESS...")
        logger.info("=" * 80 + "\n")
        
        results = model.train(**train_args)
        
        # Save best model
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING COMPLETED")
        logger.info("=" * 80)
        
        best_model_path = MODELS_DIR / "ppe_best.pt"
        logger.info(f"[SAVE] Saving best model to: {best_model_path}")
        
        # Copy best model from runs to models directory
        if hasattr(results, 'save_dir'):
            best_in_runs = Path(results.save_dir) / "weights" / "best.pt"
            if best_in_runs.exists():
                import shutil
                shutil.copy(str(best_in_runs), str(best_model_path))
                logger.info(f"[OK] Best model saved: {best_model_path}")
        
        # Training summary
        logger.info(f"\n[SUMMARY] YOLOv11 Training Summary:")
        logger.info(f"          Total Epochs: {epochs}")
        logger.info(f"          Batch Size: {batch_size}")
        logger.info(f"          Image Size: {imgsz}x{imgsz}")
        logger.info(f"          Model Size: {model_size} ({model_name})")
        logger.info(f"          Framework: YOLOv11")
        
        logger.info(f"\n[SUCCESS] YOLOv11 training completed successfully!")
        logger.info(f"          Logs saved to: {log_file}")
        logger.info(f"          Models saved to: {MODELS_DIR}")
        logger.info(f"          Training runs saved to: {RUNS_DIR}")
        
        return True
    
    except Exception as e:
        logger.error(f"[ERROR] Training failed: {str(e)}", exc_info=True)
        return False


def validate_model(model_path: Path, data_yaml: Path) -> bool:
    """
    Validate trained YOLOv11 model on validation dataset.
    
    Args:
        model_path: Path to trained model
        data_yaml: Path to data.yaml
        
    Returns:
        True if validation successful, False otherwise
    """
    logger.info("\n" + "=" * 80)
    logger.info("YOLOV11 MODEL VALIDATION")
    logger.info("=" * 80)
    
    if not model_path.exists():
        logger.error(f"[ERROR] Model not found: {model_path}")
        return False
    
    try:
        model = YOLO(str(model_path))
        logger.info(f"[OK] Model loaded: {model_path}")
        
        results = model.val(data=str(data_yaml))
        
        logger.info(f"\n[RESULTS] Validation Results:")
        logger.info(f"          mAP@0.5: {results.box.map50:.4f}")
        logger.info(f"          mAP@0.5:0.95: {results.box.map:.4f}")
        
        return True
    
    except Exception as e:
        logger.error(f"[ERROR] Validation failed: {str(e)}", exc_info=True)
        return False


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main training script entry point."""
    
    # ========================================================================
    # SETUP YOLO ENVIRONMENT (MUST BE FIRST)
    # ========================================================================
    setup_yolo_environment()
    
    # ========================================================================
    # COMMAND LINE INTERFACE
    # ========================================================================
    
    parser = argparse.ArgumentParser(
        description="Train YOLOv11 model for PPE detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python train.py
  python train.py --epochs 150 --batch-size 8 --model-size m
  python train.py --epochs 100 --batch-size 4 --device 0 --imgsz 960 --model-size l
  python train.py --resume --resume-model models/ppe_best.pt
        """
    )
    
    # Training parameters
    parser.add_argument(
        "--epochs",
        type=int,
        default=DEFAULT_CONFIG["epochs"],
        help=f"Number of training epochs (default: {DEFAULT_CONFIG['epochs']})"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_CONFIG["batch_size"],
        help=f"Batch size for training (default: {DEFAULT_CONFIG['batch_size']})"
    )
    
    parser.add_argument(
        "--imgsz",
        type=int,
        default=DEFAULT_CONFIG["imgsz"],
        help=f"Image size for training (default: {DEFAULT_CONFIG['imgsz']})"
    )
    
    parser.add_argument(
        "--model-size",
        type=str,
        default="m",
        choices=["n", "s", "m", "l", "x"],
        help="YOLOv11 model size: nano(n), small(s), medium(m), large(l), xlarge(x) (default: m)"
    )
    
    parser.add_argument(
        "--device",
        type=int,
        default=DEFAULT_CONFIG["device"],
        help=f"GPU device ID (0 for first GPU, -1 for CPU) (default: {DEFAULT_CONFIG['device']})"
    )
    
    parser.add_argument(
        "--patience",
        type=int,
        default=DEFAULT_CONFIG["patience"],
        help=f"Early stopping patience (default: {DEFAULT_CONFIG['patience']})"
    )
    
    # Resume training
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume training from last checkpoint"
    )
    
    parser.add_argument(
        "--resume-model",
        type=str,
        default=None,
        help="Path to model checkpoint for resuming training"
    )
    
    # Data configuration
    parser.add_argument(
        "--data-yaml",
        type=Path,
        default=DATA_YAML,
        help=f"Path to data.yaml (default: {DATA_YAML})"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # ========================================================================
    # TRAINING PIPELINE
    # ========================================================================
    
    logger.info("\n")
    logger.info("[START] YOLOv11 PPE DETECTION MODEL TRAINING PIPELINE")
    logger.info("=" * 80)
    
    # Step 1: Check environment
    if not check_environment():
        logger.error("[FAILED] Environment check failed")
        return False
    
    # Step 2: Validate dataset
    if not validate_dataset(args.data_yaml):
        logger.error("[FAILED] Dataset validation failed")
        return False
    
    # Step 3: Train model
    if not train_model(
        data_yaml=args.data_yaml,
        epochs=args.epochs,
        batch_size=args.batch_size,
        imgsz=args.imgsz,
        model_size=args.model_size,
        device=args.device,
        patience=args.patience,
        resume=args.resume,
        resume_model=args.resume_model,
    ):
        logger.error("[FAILED] Model training failed")
        return False
    
    # Step 4: Validate model (optional)
    best_model = MODELS_DIR / "ppe_best.pt"
    if best_model.exists():
        validate_model(best_model, args.data_yaml)
    
    logger.info("\n" + "=" * 80)
    logger.info("[SUCCESS] YOLOV11 TRAINING PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"[LOGS] Training logs: {log_file}\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)