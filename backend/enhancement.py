import cv2
import numpy as np

class ImageEnhancer:
    
    @staticmethod
    def auto_white_balance(image: np.ndarray) -> np.ndarray:
        """
        Simple auto white balance
        """
        if len(image.shape) != 3:
            return image.copy()
        
        result = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        avg_a = np.mean(result[:, :, 1])
        avg_b = np.mean(result[:, :, 2])
        result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
        result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
        result = cv2.cvtColor(result, cv2.COLOR_LAB2RGB)
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    @staticmethod
    def adjust_saturation(image: np.ndarray, saturation: int = 110) -> np.ndarray:
        """
        Adjust saturation to make colors more vibrant
        """
        saturation = max(50, min(200, saturation))
        
        if len(image.shape) != 3 or saturation == 100:
            return image.copy()
        
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        
        # Adjust saturation
        hsv[:, :, 1] = hsv[:, :, 1] * (saturation / 100.0)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        
        # Convert back to RGB
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        
        return result