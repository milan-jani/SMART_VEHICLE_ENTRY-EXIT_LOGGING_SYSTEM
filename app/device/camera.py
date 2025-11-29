"""
Camera Module
Handles camera capture and preview functionality
"""
import cv2
import time
from typing import Tuple, Optional


def capture_with_preview(camera_index: int = 0) -> Tuple[Optional[str], Optional[str]]:
    """
    Capture image from camera with live preview
    
    Args:
        camera_index: Camera device index (0, 1, 2, etc.)
    
    Returns:
        Tuple of (filename, frame_data) or (None, None) if cancelled
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise Exception("[ERROR] Camera not found.")

    print("[INFO] Press 'c' to capture photo")
    print("Press 'q' to quit")

    filename = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame.")
            break

        cv2.imshow("Live Preview - Press 'c' to capture", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            # Save to data/photos directory
            import os
            photo_dir = os.path.join(
                os.path.dirname(__file__),
                "..", "..",
                "data", "photos"
            )
            os.makedirs(photo_dir, exist_ok=True)
            
            filename = os.path.join(photo_dir, f"capture_{int(time.time())}.jpg")
            cv2.imwrite(filename, frame)
            print(f"[SAVED] {filename}")
            break

        elif key == ord('q'):
            print("Capture cancelled.")
            break

    cap.release()
    cv2.destroyAllWindows()
    
    return filename, None


def capture_single_frame(camera_index: int = 0, save_path: str = None) -> Optional[str]:
    """
    Capture a single frame without preview
    
    Args:
        camera_index: Camera device index
        save_path: Optional custom save path
    
    Returns:
        Path to saved image or None
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise Exception("[ERROR] Camera not found.")
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return None
    
    if save_path is None:
        import os
        photo_dir = os.path.join(
            os.path.dirname(__file__),
            "..", "..",
            "data", "photos"
        )
        os.makedirs(photo_dir, exist_ok=True)
        save_path = os.path.join(photo_dir, f"capture_{int(time.time())}.jpg")
    
    cv2.imwrite(save_path, frame)
    return save_path
