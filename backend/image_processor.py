import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional
from .enhancement import ImageEnhancer
from .scratch_removal import ScratchRestorer
from .utils import ImageUtils
import time
from scipy import ndimage

class ImageProcessor:
    def __init__(self):
        self.enhancer = ImageEnhancer()
        self.restorer = ScratchRestorer()
        self.utils = ImageUtils()
    
    def analyze_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze image characteristics to determine optimal processing parameters
        """
        analysis = {
            'brightness': np.mean(image) / 255.0,
            'contrast': np.std(image) / 128.0,
            'noise_level': self._estimate_noise(image),
            'color_balance': self._check_color_balance(image),
            'edge_density': self._calculate_edge_density(image),
            'has_large_damage': False
        }
        
        return analysis
    
    def _estimate_noise(self, image: np.ndarray) -> float:
        """Estimate noise level in image"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Use Laplacian variance as noise estimate
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        noise_level = np.var(laplacian) / 1000.0
        
        return min(noise_level, 1.0)
    
    def _check_color_balance(self, image: np.ndarray) -> Dict[str, float]:
        """Check color balance of image"""
        if len(image.shape) != 3:
            return {'r': 1.0, 'g': 1.0, 'b': 1.0}
        
        avg_r = np.mean(image[:, :, 0])
        avg_g = np.mean(image[:, :, 1])
        avg_b = np.mean(image[:, :, 2])
        avg_total = (avg_r + avg_g + avg_b) / 3.0
        
        return {
            'r': avg_total / max(avg_r, 1.0),
            'g': avg_total / max(avg_g, 1.0),
            'b': avg_total / max(avg_b, 1.0)
        }
    
    def _calculate_edge_density(self, image: np.ndarray) -> float:
        """Calculate edge density for texture analysis"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
        
        return edge_density
    
    def process_image(self, 
                     image_path: str, 
                     mask_path: Optional[str] = None,
                     parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Smart image processing pipeline with adaptive algorithms
        """
        if parameters is None:
            parameters = {}
        
        start_time = time.time()
        
        try:
            # Load original image
            original_image = self.utils.load_image(image_path, mode='color')
            
            # Resize if too large (preserve aspect ratio)
            if not self.utils.validate_image_size(original_image):
                original_image = self.utils.resize_image(original_image, max_dimension=2000)
            
            # Analyze image characteristics
            image_analysis = self.analyze_image(original_image)
            
            # Start with original
            processed = original_image.copy()
            
            # Apply smart restoration if mask exists
            if mask_path and os.path.exists(mask_path):
                mask = self.utils.load_image(mask_path, mode='gray')
                
                # Ensure mask matches image dimensions
                if mask.shape != processed.shape[:2]:
                    mask = cv2.resize(mask, (processed.shape[1], processed.shape[0]))
                
                # Analyze mask to choose best algorithm
                mask_area = np.sum(mask > 0)
                total_pixels = mask.shape[0] * mask.shape[1]
                damage_ratio = mask_area / total_pixels
                
                # Choose inpainting method based on damage extent
                if damage_ratio < 0.05:  # Small damage
                    method = 'telea'
                elif damage_ratio < 0.2:  # Medium damage
                    method = 'patch'
                else:  # Large damage
                    method = 'multiscale'
                
                # Get inpainting parameters
                inpainting_radius = parameters.get('inpainting_radius', 3)
                
                # Apply smart inpainting
                processed = self.restorer.smart_inpainting(
                    processed, mask, 
                    method=method,
                    adaptive=True
                )
                
                # Store mask analysis in parameters
                parameters['mask_area'] = mask_area
                parameters['damage_ratio'] = round(damage_ratio, 3)
                parameters['inpainting_method_used'] = method
            
            # Apply adaptive enhancements based on image analysis
            processed = self._apply_adaptive_enhancements(processed, parameters, image_analysis)
            
            # Post-processing refinement
            processed = self._post_process(processed, original_image, parameters)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Calculate quality metrics
            metrics = self.utils.calculate_metrics(original_image, processed)
            metrics['processing_time'] = round(processing_time, 2)
            
            # Add image analysis to metrics
            metrics.update({
                'noise_level': round(image_analysis['noise_level'], 3),
                'edge_density': round(image_analysis['edge_density'], 3),
                'brightness_level': round(image_analysis['brightness'], 3)
            })
            
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
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _apply_adaptive_enhancements(self, 
                                    image: np.ndarray, 
                                    parameters: Dict[str, Any],
                                    analysis: Dict[str, Any]) -> np.ndarray:
        """
        Apply enhancements adaptively based on image analysis
        """
        result = image.copy()
        
        # 1. Noise reduction (adaptive based on noise level)
        noise_reduction = parameters.get('noise_reduction', 0)
        if noise_reduction > 0 or analysis['noise_level'] > 0.3:
            # Increase noise reduction for noisy images
            effective_noise_reduction = max(noise_reduction, int(analysis['noise_level'] * 50))
            result = self.enhancer.reduce_noise(result, min(effective_noise_reduction, 70))
        
        # 2. Auto white balance if requested or if color imbalance detected
        auto_wb = parameters.get('auto_white_balance', False)
        color_balance = analysis['color_balance']
        if auto_wb or max(color_balance.values()) > 1.3 or min(color_balance.values()) < 0.7:
            result = self.enhancer.auto_white_balance(result)
        
        # 3. Brightness/contrast adjustment
        brightness = parameters.get('brightness', 0)
        contrast = parameters.get('contrast', 0)
        
        # Adjust based on image brightness analysis
        if analysis['brightness'] < 0.3 and brightness == 0:
            brightness = 20  # Auto-brighten dark images
        elif analysis['brightness'] > 0.7 and brightness == 0:
            brightness = -10  # Auto-darken bright images
        
        if brightness != 0 or contrast != 0:
            result = self.enhancer.adjust_brightness_contrast(result, brightness, contrast)
        
        # 4. Gamma correction
        gamma = parameters.get('gamma', 1.0)
        if gamma != 1.0:
            result = self.enhancer.adjust_gamma(result, gamma)
        
        # 5. Saturation adjustment (careful not to oversaturate)
        saturation = parameters.get('saturation', 100)
        if saturation != 100:
            # Limit saturation boost for already colorful images
            if saturation > 100 and analysis['edge_density'] > 0.1:
                saturation = min(saturation, 130)
            result = self.enhancer.adjust_saturation(result, saturation)
        
        # 6. Detail enhancement (adaptive based on edge density)
        detail_enhancement = parameters.get('detail_enhancement', 0)
        if detail_enhancement > 0:
            # Reduce enhancement for already detailed images
            if analysis['edge_density'] > 0.15:
                detail_enhancement = int(detail_enhancement * 0.7)
            result = self.enhancer.enhance_details(result, detail_enhancement)
        
        # 7. Sharpness (apply last, but carefully)
        sharpness = parameters.get('sharpness', 0)
        if sharpness != 0:
            # Reduce sharpening for high-noise images
            if analysis['noise_level'] > 0.4:
                sharpness = int(sharpness * 0.5)
            result = self.enhancer.enhance_sharpness(result, sharpness)
        
        return result
    
    def _post_process(self, 
                     image: np.ndarray, 
                     original: np.ndarray,
                     parameters: Dict[str, Any]) -> np.ndarray:
        """
        Final post-processing for quality refinement
        """
        result = image.copy()
        
        # 1. Mild noise reduction to smooth artifacts
        if parameters.get('mask_area', 0) > 1000:
            # Apply light Gaussian blur to inpainted areas
            kernel_size = 3
            blurred = cv2.GaussianBlur(result, (kernel_size, kernel_size), 0.5)
            
            # Create soft mask for blending
            if 'mask_area' in parameters:
                # Light blending of original edges
                edges = cv2.Canny(original, 50, 150)
                edge_mask = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
                edge_mask = edge_mask.astype(np.float32) / 255.0
                if len(result.shape) == 3:
                    edge_mask = np.stack([edge_mask] * 3, axis=2)
                
                result = result * (1 - edge_mask * 0.3) + blurred * (edge_mask * 0.3)
        
        # 2. Ensure values are in valid range
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
    
    def preview_enhancement(self, 
                           image: np.ndarray, 
                           enhancement_type: str,
                           value: float) -> np.ndarray:
        """
        Preview a single enhancement without modifying the original
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
        elif enhancement_type == 'gamma':
            return self.enhancer.adjust_gamma(image, float(value))
        else:
            return image.copy() 