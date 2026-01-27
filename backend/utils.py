import os
import cv2
import numpy as np
from PIL import Image
import base64
from io import BytesIO
from pathlib import Path

class ImageUtils:
    @staticmethod
    def load_image(image_path: str, mode: str = 'color') -> np.ndarray:
        """Load image with error handling"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        try:
            if mode == 'color':
                img = cv2.imread(image_path, cv2.IMREAD_COLOR)
                if img is None:
                    raise ValueError(f"Failed to load image: {image_path}")
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    raise ValueError(f"Failed to load image: {image_path}")
            
            return img
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
            raise
    
    @staticmethod
    def save_image(image: np.ndarray, save_path: str, quality: int = 95) -> bool:
        """Save image with proper format"""
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Save based on extension
            ext = Path(save_path).suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                cv2.imwrite(save_path, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
            else:
                cv2.imwrite(save_path, image)
            
            return True
        except Exception as e:
            print(f"Error saving {save_path}: {e}")
            return False
    
    @staticmethod
    def resize_image(image: np.ndarray, max_dimension: int = 1200) -> np.ndarray:
        """Smart resize maintaining aspect ratio"""
        h, w = image.shape[:2]
        
        if max(h, w) <= max_dimension:
            return image
        
        # Calculate new dimensions
        if w > h:
            new_w = max_dimension
            new_h = int(h * (max_dimension / w))
        else:
            new_h = max_dimension
            new_w = int(w * (max_dimension / h))
        
        # Use high-quality interpolation
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    @staticmethod
    def numpy_to_base64(image: np.ndarray) -> str:
        """Convert numpy array to base64 for web display"""
        # Ensure proper format
        if len(image.shape) == 3 and image.shape[2] == 3:
            pil_img = Image.fromarray(image)
        elif len(image.shape) == 2:
            pil_img = Image.fromarray(image)
        else:
            raise ValueError(f"Unsupported image shape: {image.shape}")
        
        buffered = BytesIO()
        pil_img.save(buffered, format="JPEG", quality=90)
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{img_str}"