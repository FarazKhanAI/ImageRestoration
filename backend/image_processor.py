import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional
from .enhancement import ImageEnhancer
from .scratch_removal import ScratchRestorer
from .utils import ImageUtils
import time

class ImageProcessor:
    def __init__(self):
        self.enhancer = ImageEnhancer()
        self.restorer = ScratchRestorer()
        self.utils = ImageUtils()
    
    def process_image(self, 
                     image_path: str, 
                     mask_path: Optional[str] = None,
                     parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Complete image processing pipeline
        
        Args:
            image_path: Path to input image
            mask_path: Path to mask image (optional)
            parameters: Dictionary of processing parameters
        
        Returns:
            Dictionary containing processed image and metrics
        """
        if parameters is None:
            parameters = {}
        
        # Start timing
        start_time = time.time()
        
        try:
            # Load original image
            original_image = self.utils.load_image(image_path, mode='color')
            
            # Resize if too large
            if not self.utils.validate_image_size(original_image):
                original_image = self.utils.resize_image(original_image, max_dimension=2000)
            
            # Initialize result with original
            processed = original_image.copy()
            
            # Apply enhancement pipeline
            processed = self._apply_enhancements(processed, parameters)
            
            # Apply scratch removal if mask is provided
            if mask_path:
                mask = self.utils.load_image(mask_path, mode='gray')
                # Resize mask to match image if needed
                if mask.shape != processed.shape[:2]:
                    mask = cv2.resize(mask, (processed.shape[1], processed.shape[0]))
                
                # Apply inpainting
                inpainting_method = parameters.get('inpainting_method', 'telea')
                inpainting_radius = parameters.get('inpainting_radius', 3)
                
                if inpainting_method == 'telea':
                    processed = self.restorer.inpaint_telea(processed, mask, inpainting_radius)
                elif inpainting_method == 'ns':
                    processed = self.restorer.inpaint_ns(processed, mask, inpainting_radius)
                else:
                    processed = self.restorer.neighbor_interpolation(processed, mask)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Calculate metrics
            metrics = self.utils.calculate_metrics(original_image, processed)
            metrics['processing_time'] = round(processing_time, 2)
            
            # Prepare result
            result = {
                'success': True,
                'original_image': original_image,
                'processed_image': processed,
                'metrics': metrics,
                'original_shape': original_image.shape,
                'processed_shape': processed.shape
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _apply_enhancements(self, image: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """Apply all requested enhancements"""
        result = image.copy()
        
        # Apply noise reduction if requested
        noise_reduction = parameters.get('noise_reduction', 0)
        if noise_reduction > 0:
            result = self.enhancer.reduce_noise(result, noise_reduction)
        
        # Apply brightness/contrast adjustment
        brightness = parameters.get('brightness', 0)
        contrast = parameters.get('contrast', 0)
        if brightness != 0 or contrast != 0:
            result = self.enhancer.adjust_brightness_contrast(result, brightness, contrast)
        
        # Apply sharpness enhancement
        sharpness = parameters.get('sharpness', 0)
        if sharpness != 0:
            result = self.enhancer.enhance_sharpness(result, sharpness)
        
        # Apply saturation adjustment
        saturation = parameters.get('saturation', 100)
        if saturation != 100:
            result = self.enhancer.adjust_saturation(result, saturation)
        
        # Apply detail enhancement
        detail_enhancement = parameters.get('detail_enhancement', 0)
        if detail_enhancement > 0:
            result = self.enhancer.enhance_details(result, detail_enhancement)
        
        # Apply auto white balance if requested
        if parameters.get('auto_white_balance', False):
            result = self.enhancer.auto_white_balance(result)
        
        # Apply gamma correction if requested
        gamma = parameters.get('gamma', 1.0)
        if gamma != 1.0:
            result = self.enhancer.adjust_gamma(result, gamma)
        
        return result
    
    def preview_enhancement(self, 
                           image: np.ndarray, 
                           enhancement_type: str,
                           value: float) -> np.ndarray:
        """
        Preview a single enhancement without modifying the original
        
        Args:
            image: Input image
            enhancement_type: Type of enhancement
            value: Enhancement value
        
        Returns:
            Preview image
        """
        if enhancement_type == 'brightness':
            return self.enhancer.adjust_brightness_contrast(image, brightness=value)
        elif enhancement_type == 'contrast':
            return self.enhancer.adjust_brightness_contrast(image, contrast=value)
        elif enhancement_type == 'sharpness':
            return self.enhancer.enhance_sharpness(image, int(value))
        elif enhancement_type == 'saturation':
            return self.enhancer.adjust_saturation(image, int(value))
        elif enhancement_type == 'noise_reduction':
            return self.enhancer.reduce_noise(image, int(value))
        elif enhancement_type == 'detail_enhancement':
            return self.enhancer.enhance_details(image, int(value))
        else:
            return image.copy()