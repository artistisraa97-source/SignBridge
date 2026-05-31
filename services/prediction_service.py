# Common prediction services

import cv2
import numpy as np

def decode_image(image_data: bytes) -> np.ndarray:
    """Decode image data to numpy array."""
    np_img = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    return frame

def preprocess_frame(frame: np.ndarray) -> np.ndarray:
    """Preprocess frame for prediction."""
    # Common preprocessing
    return frame