import cv2
import numpy as np
from numba import jit
from typing import Tuple

class ImageEnhancer:
    
    @staticmethod
    def _safe_number(value, default=0, is_float=False):
        """Safely convert value to number"""
        if isinstance(value, (int, float)):
            return value
        try:
            if is_float:
                return float(value)
            return int(float(value))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def adjust_brightness_contrast(image: np.ndarray, 
                                  brightness: int = 0, 
                                  contrast: int = 0) -> np.ndarray:
        """
        Adjust brightness and contrast of an image
        """
        brightness = ImageEnhancer._safe_number(brightness, 0)
        contrast = ImageEnhancer._safe_number(contrast, 0)
        
        if brightness == 0 and contrast == 0:
            return image.copy()
        
        # Convert brightness and contrast to OpenCV parameters
        alpha = 1 + contrast / 100.0
        beta = brightness
        
        # Apply brightness/contrast adjustment
        adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        
        return adjusted
    
    @staticmethod
    def enhance_sharpness(image: np.ndarray, amount: int = 50) -> np.ndarray:
        """
        Enhance image sharpness using unsharp masking
        """
        amount = ImageEnhancer._safe_number(amount, 0)
        
        if amount == 0:
            return image.copy()
        
        # Convert amount to a suitable sigma value
        sigma = 1.0 + (amount / 100.0) * 4.0
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), sigma)
        
        # Calculate sharpened image
        sharpened = cv2.addWeighted(image, 1.5 + (amount / 200.0), 
                                   blurred, -0.5 - (amount / 200.0), 0)
        
        return np.clip(sharpened, 0, 255).astype(np.uint8)
    
    @staticmethod
    def adjust_saturation(image: np.ndarray, saturation: int = 100) -> np.ndarray:
        """
        Adjust color saturation
        """
        saturation = ImageEnhancer._safe_number(saturation, 100)
        
        if saturation == 100 or len(image.shape) != 3:
            return image.copy()
        
        # Convert to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        
        # Adjust saturation channel
        hsv[:, :, 1] = hsv[:, :, 1] * (saturation / 100.0)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        
        # Convert back to RGB
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        
        return result
    
    @staticmethod
    def reduce_noise(image: np.ndarray, strength: int = 50) -> np.ndarray:
        """
        Reduce noise while preserving edges
        """
        strength = ImageEnhancer._safe_number(strength, 0)
        
        if strength == 0:
            return image.copy()
        
        # Adaptive noise reduction based on image size
        h, w = image.shape[:2]
        if h * w > 2000 * 2000:  # Large image
            h_value = 5 + (strength / 100.0) * 15
        else:
            h_value = 10 + (strength / 100.0) * 30
        
        template_window = 7
        search_window = 21
        
        if len(image.shape) == 3:
            denoised = cv2.fastNlMeansDenoisingColored(
                image, None, h_value, h_value, 
                template_window, search_window
            )
        else:
            denoised = cv2.fastNlMeansDenoising(
                image, None, h_value, template_window, search_window
            )
        
        return denoised
    
    @staticmethod
    def auto_white_balance(image: np.ndarray) -> np.ndarray:
        """
        Improved automatic white balance using percentile method
        """
        if len(image.shape) != 3:
            return image.copy()
        
        # Convert to float for calculations
        image_float = image.astype(np.float32)
        
        # Use percentile method for better robustness
        percentiles = np.percentile(image_float.reshape(-1, 3), [1, 50, 99], axis=0)
        
        # Calculate scaling factors
        max_values = percentiles[2]  # 99th percentile
        min_values = percentiles[0]  # 1st percentile
        
        # Avoid division by zero
        max_values = np.maximum(max_values, 1.0)
        
        # Calculate dynamic range per channel
        dynamic_range = max_values - min_values
        avg_dynamic = np.mean(dynamic_range)
        
        # Calculate scaling to match dynamic ranges
        scale_b = avg_dynamic / max(dynamic_range[0], 1.0)
        scale_g = avg_dynamic / max(dynamic_range[1], 1.0)
        scale_r = avg_dynamic / max(dynamic_range[2], 1.0)
        
        # Apply scaling
        balanced = image_float.copy()
        balanced[:, :, 0] = balanced[:, :, 0] * scale_b
        balanced[:, :, 1] = balanced[:, :, 1] * scale_g
        balanced[:, :, 2] = balanced[:, :, 2] * scale_r
        
        # Clip and convert
        balanced = np.clip(balanced, 0, 255).astype(np.uint8)
        
        return balanced
    
    @staticmethod
    def enhance_details(image: np.ndarray, strength: int = 50) -> np.ndarray:
        """
        Enhance image details using local contrast enhancement
        """
        strength = ImageEnhancer._safe_number(strength, 0)
        
        if strength == 0:
            return image.copy()
        
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l_channel, a, b = cv2.split(lab)
        else:
            l_channel = image.copy()
        
        # Adaptive CLAHE based on image size
        h, w = l_channel.shape[:2]
        tile_size = max(8, min(h, w) // 64)
        
        clahe = cv2.createCLAHE(
            clipLimit=2.0 + (strength / 100.0) * 3.0,
            tileGridSize=(tile_size, tile_size)
        )
        enhanced_l = clahe.apply(l_channel)
        
        if len(image.shape) == 3:
            enhanced_lab = cv2.merge([enhanced_l, a, b])
            result = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
        else:
            result = enhanced_l
        
        return result
    
    @jit(nopython=True, parallel=True)
    def _apply_gamma_correction_numba(image: np.ndarray, gamma: float) -> np.ndarray:
        """Numba-accelerated gamma correction"""
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 
                         for i in np.arange(0, 256)]).astype("uint8")
        return table[image]
    
    @staticmethod
    def adjust_gamma(image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
        """
        Adjust image gamma
        """
        gamma = ImageEnhancer._safe_number(gamma, 1.0, is_float=True)
        
        if gamma == 1.0:
            return image.copy()
        
        gamma = max(0.1, min(3.0, gamma))
        
        return ImageEnhancer._apply_gamma_correction_numba(image, gamma)
    
    @staticmethod
    def color_correction(image: np.ndarray, 
                        temperature: int = 0, 
                        tint: int = 0) -> np.ndarray:
        """
        Advanced color correction with temperature and tint adjustments
        """
        if len(image.shape) != 3:
            return image.copy()
        
        temp = ImageEnhancer._safe_number(temperature, 0)
        tint_val = ImageEnhancer._safe_number(tint, 0)
        
        if temp == 0 and tint_val == 0:
            return image.copy()
        
        # Convert to float
        img_float = image.astype(np.float32)
        
        # Temperature adjustment (blue-yellow balance)
        if temp != 0:
            # Positive temp = warmer (more yellow/red)
            # Negative temp = cooler (more blue)
            temp_factor = 1.0 + (temp / 100.0)
            
            if temp > 0:
                # Warmer: increase red, decrease blue
                img_float[:, :, 0] = img_float[:, :, 0] / temp_factor  # Less blue
                img_float[:, :, 2] = img_float[:, :, 2] * temp_factor  # More red
            else:
                # Cooler: increase blue, decrease red
                img_float[:, :, 0] = img_float[:, :, 0] * abs(temp_factor)  # More blue
                img_float[:, :, 2] = img_float[:, :, 2] / abs(temp_factor)  # Less red
        
        # Tint adjustment (green-magenta balance)
        if tint_val != 0:
            tint_factor = 1.0 + (tint_val / 100.0)
            img_float[:, :, 1] = img_float[:, :, 1] * tint_factor  # Adjust green
        
        # Clip and convert
        result = np.clip(img_float, 0, 255).astype(np.uint8)
        
        return result