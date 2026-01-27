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
            return int(float(value))  # Handle '30.0' strings
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def adjust_brightness_contrast(image: np.ndarray, 
                                  brightness: int = 0, 
                                  contrast: int = 0) -> np.ndarray:
        """
        Adjust brightness and contrast of an image
        
        Args:
            image: Input image (RGB or grayscale)
            brightness: -100 to 100
            contrast: -100 to 100
        
        Returns:
            Adjusted image
        """
        brightness = ImageEnhancer._safe_number(brightness, 0)
        contrast = ImageEnhancer._safe_number(contrast, 0)
        
        if brightness == 0 and contrast == 0:
            return image.copy()
        
        # Convert brightness and contrast to OpenCV parameters
        alpha = 1 + contrast / 100.0  # Contrast control (1.0-3.0)
        beta = brightness  # Brightness control (0-100)
        
        # Apply brightness/contrast adjustment
        adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        
        return adjusted
    
    @staticmethod
    def enhance_sharpness(image: np.ndarray, amount: int = 50) -> np.ndarray:
        """
        Enhance image sharpness using unsharp masking
        
        Args:
            image: Input image
            amount: 0-100, strength of sharpening
        
        Returns:
            Sharpened image
        """
        amount = ImageEnhancer._safe_number(amount, 0)
        
        if amount == 0:
            return image.copy()
        
        # Convert amount to a suitable sigma value
        sigma = 1.0 + (amount / 100.0) * 4.0
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), sigma)
        
        # Calculate sharpened image
        sharpened = cv2.addWeighted(image, 1.5, blurred, -0.5, 0)
        
        return np.clip(sharpened, 0, 255).astype(np.uint8)
    
    @staticmethod
    def adjust_saturation(image: np.ndarray, saturation: int = 100) -> np.ndarray:
        """
        Adjust color saturation
        
        Args:
            image: Input image (must be RGB)
            saturation: 0-200 (100 = no change)
        
        Returns:
            Image with adjusted saturation
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
        
        Args:
            image: Input image
            strength: 0-100, strength of noise reduction
        
        Returns:
            Denoised image
        """
        strength = ImageEnhancer._safe_number(strength, 0)
        
        if strength == 0:
            return image.copy()
        
        # Convert strength to parameters
        h = 10 + (strength / 100.0) * 30
        template_window = 7
        search_window = 21
        
        if len(image.shape) == 3:
            # Color image - use fast non-local means
            denoised = cv2.fastNlMeansDenoisingColored(
                image, 
                None, 
                h, h, 
                template_window, 
                search_window
            )
        else:
            # Grayscale image
            denoised = cv2.fastNlMeansDenoising(
                image, 
                None, 
                h, 
                template_window, 
                search_window
            )
        
        return denoised
    
    @staticmethod
    def auto_white_balance(image: np.ndarray) -> np.ndarray:
        """
        Automatic white balance using gray world assumption
        
        Args:
            image: Input image (RGB)
        
        Returns:
            White-balanced image
        """
        if len(image.shape) != 3:
            return image.copy()
        
        # Convert to float for calculations
        image_float = image.astype(np.float32)
        
        # Calculate average for each channel
        avg_b = np.mean(image_float[:, :, 0])
        avg_g = np.mean(image_float[:, :, 1])
        avg_r = np.mean(image_float[:, :, 2])
        
        # Calculate gray value (average of averages)
        avg_gray = (avg_b + avg_g + avg_r) / 3.0
        
        # Avoid division by zero
        avg_b = max(avg_b, 1.0)
        avg_g = max(avg_g, 1.0)
        avg_r = max(avg_r, 1.0)
        
        # Calculate scaling factors
        scale_b = avg_gray / avg_b
        scale_g = avg_gray / avg_g
        scale_r = avg_gray / avg_r
        
        # Apply scaling to each channel
        balanced = image_float.copy()
        balanced[:, :, 0] = balanced[:, :, 0] * scale_b
        balanced[:, :, 1] = balanced[:, :, 1] * scale_g
        balanced[:, :, 2] = balanced[:, :, 2] * scale_r
        
        # Clip values and convert back to uint8
        balanced = np.clip(balanced, 0, 255).astype(np.uint8)
        
        return balanced
    
    @staticmethod
    def enhance_details(image: np.ndarray, strength: int = 50) -> np.ndarray:
        """
        Enhance image details using local contrast enhancement
        
        Args:
            image: Input image
            strength: 0-100, strength of detail enhancement
        
        Returns:
            Image with enhanced details
        """
        strength = ImageEnhancer._safe_number(strength, 0)
        
        if strength == 0:
            return image.copy()
        
        if len(image.shape) == 3:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l_channel, a, b = cv2.split(lab)
        else:
            l_channel = image.copy()
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(
            clipLimit=2.0 + (strength / 100.0) * 3.0,
            tileGridSize=(8, 8)
        )
        enhanced_l = clahe.apply(l_channel)
        
        if len(image.shape) == 3:
            # Merge back to LAB and convert to RGB
            enhanced_lab = cv2.merge([enhanced_l, a, b])
            result = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
        else:
            result = enhanced_l
        
        return result
    
    @jit(nopython=True, parallel=True)
    def _apply_gamma_correction_numba(image: np.ndarray, gamma: float) -> np.ndarray:
        """Numba-accelerated gamma correction"""
        # Build lookup table
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 
                         for i in np.arange(0, 256)]).astype("uint8")
        
        # Apply lookup table
        return table[image]
    
    @staticmethod
    def adjust_gamma(image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
        """
        Adjust image gamma
        
        Args:
            image: Input image
            gamma: Gamma value (0.1-3.0)
        
        Returns:
            Gamma-corrected image
        """
        gamma = ImageEnhancer._safe_number(gamma, 1.0, is_float=True)
        
        if gamma == 1.0:
            return image.copy()
        
        # Ensure gamma is in valid range
        gamma = max(0.1, min(3.0, gamma))
        
        return ImageEnhancer._apply_gamma_correction_numba(image, gamma)