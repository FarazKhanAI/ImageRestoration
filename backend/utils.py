import os
import cv2
import numpy as np
from PIL import Image
import base64
from io import BytesIO
from pathlib import Path
import uuid
from typing import Tuple, Optional, List

class ImageUtils:
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Generate a unique filename to prevent collisions"""
        ext = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())[:8]
        return f"{unique_id}{ext}"
    
    @staticmethod
    def load_image(image_path: str, mode: str = 'color') -> np.ndarray:
        """
        Load image with OpenCV and convert to RGB if needed
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        if mode == 'color':
            img = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError(f"Failed to load image: {image_path}")
            # Convert BGR to RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"Failed to load image: {image_path}")
        
        return img
    
    @staticmethod
    def save_image(image: np.ndarray, save_path: str, quality: int = 90) -> bool:
        """
        Save image to disk with proper directory creation
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Convert RGB to BGR for OpenCV saving
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Determine compression parameters
            ext = Path(save_path).suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                cv2.imwrite(save_path, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
            elif ext == '.png':
                compression = int((100 - quality) / 11.11)
                cv2.imwrite(save_path, image, [cv2.IMWRITE_PNG_COMPRESSION, compression])
            else:
                cv2.imwrite(save_path, image)
            
            return True
        except Exception as e:
            print(f"Error saving image to {save_path}: {e}")
            return False
    
    @staticmethod
    def resize_image(image: np.ndarray, max_dimension: int = 1200) -> np.ndarray:
        """
        Resize image while maintaining aspect ratio
        """
        try:
            if isinstance(max_dimension, str):
                max_dimension = int(float(max_dimension))
        except (ValueError, TypeError):
            max_dimension = 1200
        
        h, w = image.shape[:2]
        
        if max(h, w) <= max_dimension:
            return image
        
        if w > h:
            new_w = max_dimension
            new_h = int(h * (max_dimension / w))
        else:
            new_h = max_dimension
            new_w = int(w * (max_dimension / h))
        
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    @staticmethod
    def numpy_to_base64(image: np.ndarray, format: str = 'JPEG') -> str:
        """
        Convert numpy array to base64 string for web display
        """
        pil_img = Image.fromarray(image)
        buffered = BytesIO()
        pil_img.save(buffered, format=format, quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/{format.lower()};base64,{img_str}"
    
    @staticmethod
    def create_advanced_mask(image_shape: Tuple[int, int], 
                           coordinates: List[Tuple[int, int]], 
                           brush_size: int = 20,
                           feather: bool = True) -> np.ndarray:
        """
        Create an advanced mask with morphological processing and feathering
        """
        mask = np.zeros(image_shape[:2], dtype=np.uint8)
        
        if not coordinates:
            return mask
        
        try:
            if isinstance(brush_size, str):
                brush_size = int(float(brush_size))
        except (ValueError, TypeError):
            brush_size = 20
        
        # Draw circles at each coordinate with varying sizes for more natural look
        for x, y in coordinates:
            try:
                x_int = int(float(x))
                y_int = int(float(y))
                if 0 <= x_int < image_shape[1] and 0 <= y_int < image_shape[0]:
                    # Use slightly random brush size for more natural strokes
                    current_brush = max(5, brush_size + np.random.randint(-3, 4))
                    cv2.circle(mask, (x_int, y_int), current_brush, 255, -1)
            except (ValueError, TypeError):
                continue
        
        if feather:
            # Apply morphological operations to clean the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # Feather edges for smooth transition
            mask_float = mask.astype(np.float32) / 255.0
            mask_float = cv2.GaussianBlur(mask_float, (11, 11), 3.0)
            mask = (mask_float * 255).astype(np.uint8)
        
        return mask
    
    @staticmethod
    def create_mask_from_coordinates(image_shape: Tuple[int, int], 
                                   coordinates: list, 
                                   brush_size: int = 20) -> np.ndarray:
        """
        Legacy function for backward compatibility
        """
        return ImageUtils.create_advanced_mask(image_shape, coordinates, brush_size, feather=True)
    
    @staticmethod
    def calculate_metrics(original: np.ndarray, enhanced: np.ndarray) -> dict:
        """
        Calculate image quality metrics with improved accuracy
        """
        if original.shape != enhanced.shape:
            enhanced = cv2.resize(enhanced, (original.shape[1], original.shape[0]))
        
        # Convert to grayscale if needed
        if len(original.shape) == 3:
            original_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
            enhanced_gray = cv2.cvtColor(enhanced, cv2.COLOR_RGB2GRAY)
        else:
            original_gray = original
            enhanced_gray = enhanced
        
        # Calculate PSNR
        try:
            mse = np.mean((original_gray - enhanced_gray) ** 2)
            if mse == 0:
                psnr_value = 100.0
            else:
                max_pixel = 255.0
                psnr_value = 20 * np.log10(max_pixel / np.sqrt(mse))
        except:
            psnr_value = 30.0
        
        # Calculate SSIM
        try:
            from skimage.metrics import structural_similarity as ssim
            ssim_value, _ = ssim(original_gray, enhanced_gray, full=True, data_range=255)
        except:
            # Fallback calculation if skimage not available
            C1 = (0.01 * 255) ** 2
            C2 = (0.03 * 255) ** 2
            
            mu_x = cv2.GaussianBlur(original_gray.astype(np.float32), (11, 11), 1.5)
            mu_y = cv2.GaussianBlur(enhanced_gray.astype(np.float32), (11, 11), 1.5)
            
            mu_x_sq = mu_x ** 2
            mu_y_sq = mu_y ** 2
            mu_xy = mu_x * mu_y
            
            sigma_x_sq = cv2.GaussianBlur((original_gray.astype(np.float32) ** 2), (11, 11), 1.5) - mu_x_sq
            sigma_y_sq = cv2.GaussianBlur((enhanced_gray.astype(np.float32) ** 2), (11, 11), 1.5) - mu_y_sq
            sigma_xy = cv2.GaussianBlur((original_gray.astype(np.float32) * enhanced_gray.astype(np.float32)), 
                                      (11, 11), 1.5) - mu_xy
            
            ssim_map = ((2 * mu_xy + C1) * (2 * sigma_xy + C2)) / \
                      ((mu_x_sq + mu_y_sq + C1) * (sigma_x_sq + sigma_y_sq + C2))
            ssim_value = np.mean(ssim_map)
        
        # Determine improvement level
        if psnr_value > 35 and ssim_value > 0.9:
            improvement = 'Excellent'
        elif psnr_value > 25 and ssim_value > 0.8:
            improvement = 'Good'
        elif psnr_value > 20 and ssim_value > 0.7:
            improvement = 'Moderate'
        else:
            improvement = 'Poor'
        
        return {
            'psnr': round(psnr_value, 2),
            'ssim': round(ssim_value, 3),
            'improvement': improvement
        }
    
    @staticmethod
    def validate_image_size(image: np.ndarray, max_dimension: int = 4000) -> bool:
        """Validate image dimensions"""
        h, w = image.shape[:2]
        
        try:
            if isinstance(max_dimension, str):
                max_dimension = int(float(max_dimension))
        except (ValueError, TypeError):
            max_dimension = 4000
        
        return h <= max_dimension and w <= max_dimension
    
    @staticmethod
    def save_mask_with_metadata(mask: np.ndarray, 
                               save_path: str, 
                               coordinates: List[Tuple[int, int]] = None,
                               brush_size: int = 20) -> bool:
        """
        Save mask with metadata for debugging and analysis
        """
        success = ImageUtils.save_image(mask, save_path, quality=100)
        
        # Save metadata as JSON file
        if coordinates and success:
            metadata_path = save_path.replace('.png', '_meta.json')
            import json
            metadata = {
                'coordinates': coordinates,
                'brush_size': brush_size,
                'mask_shape': mask.shape,
                'mask_area': int(np.sum(mask > 0))
            }
            try:
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f)
            except:
                pass  # Ignore metadata saving errors
        
        return success