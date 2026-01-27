import cv2
import numpy as np
from numba import jit
from typing import Tuple, Optional

class ScratchRestorer:
    
    @staticmethod
    def inpaint_telea(image: np.ndarray, 
                     mask: np.ndarray, 
                     radius: int = 3) -> np.ndarray:
        """
        Inpainting using Telea's algorithm
        
        Args:
            image: Input image (RGB or grayscale)
            mask: Binary mask where white indicates damaged pixels
            radius: Inpainting radius
        
        Returns:
            Inpainted image
        """
        if np.sum(mask) == 0:
            return image.copy()
        
        # Make sure mask is binary
        mask_binary = (mask > 0).astype(np.uint8) * 255
        
        # Apply inpainting
        if len(image.shape) == 3:
            # Color image - process each channel separately for better results
            channels = cv2.split(image)
            inpainted_channels = []
            
            for channel in channels:
                inpainted = cv2.inpaint(channel, mask_binary, radius, cv2.INPAINT_TELEA)
                inpainted_channels.append(inpainted)
            
            result = cv2.merge(inpainted_channels)
        else:
            # Grayscale image
            result = cv2.inpaint(image, mask_binary, radius, cv2.INPAINT_TELEA)
        
        return result
    
    @staticmethod
    def inpaint_ns(image: np.ndarray, 
                  mask: np.ndarray, 
                  radius: int = 3) -> np.ndarray:
        """
        Inpainting using Navier-Stokes algorithm
        
        Args:
            image: Input image
            mask: Binary mask
            radius: Inpainting radius
        
        Returns:
            Inpainted image
        """
        if np.sum(mask) == 0:
            return image.copy()
        
        # Make sure mask is binary
        mask_binary = (mask > 0).astype(np.uint8) * 255
        
        # Apply inpainting
        if len(image.shape) == 3:
            # Color image
            channels = cv2.split(image)
            inpainted_channels = []
            
            for channel in channels:
                inpainted = cv2.inpaint(channel, mask_binary, radius, cv2.INPAINT_NS)
                inpainted_channels.append(inpainted)
            
            result = cv2.merge(inpainted_channels)
        else:
            # Grayscale image
            result = cv2.inpaint(image, mask_binary, radius, cv2.INPAINT_NS)
        
        return result
    
    @jit(nopython=True)
    def _neighbor_interpolation_kernel(image: np.ndarray, 
                                      mask: np.ndarray, 
                                      result: np.ndarray,
                                      window_size: int = 5):
        """
        JIT-compiled kernel for neighbor interpolation
        """
        h, w = image.shape[:2]
        
        for y in range(h):
            for x in range(w):
                if mask[y, x] > 0:  # Pixel needs to be filled
                    # Define search window boundaries
                    y_start = max(0, y - window_size)
                    y_end = min(h, y + window_size + 1)
                    x_start = max(0, x - window_size)
                    x_end = min(w, x + window_size + 1)
                    
                    # Collect valid neighbor pixels
                    neighbor_values = []
                    
                    for ny in range(y_start, y_end):
                        for nx in range(x_start, x_end):
                            # Skip the center pixel and invalid pixels
                            if (ny == y and nx == x) or mask[ny, nx] > 0:
                                continue
                            
                            neighbor_values.append(image[ny, nx])
                    
                    # If we have neighbors, compute weighted average
                    if neighbor_values:
                        # Simple average for now (can be enhanced with distance weighting)
                        result[y, x] = np.mean(neighbor_values)
                    else:
                        result[y, x] = image[y, x]
    
    @staticmethod
    def neighbor_interpolation(image: np.ndarray, 
                              mask: np.ndarray, 
                              window_size: int = 7) -> np.ndarray:
        """
        Custom neighbor pixel interpolation
        
        Args:
            image: Input image
            mask: Binary mask
            window_size: Size of neighborhood to consider
        
        Returns:
            Restored image
        """
        if np.sum(mask) == 0:
            return image.copy()
        
        result = image.copy()
        
        if len(image.shape) == 3:
            # Process each channel separately
            channels = cv2.split(image)
            mask_single = mask[:, :, 0] if len(mask.shape) == 3 else mask
            
            restored_channels = []
            for channel in channels:
                restored = channel.copy()
                ScratchRestorer._neighbor_interpolation_kernel(
                    channel, mask_single, restored, window_size
                )
                restored_channels.append(restored)
            
            result = cv2.merge(restored_channels)
        else:
            # Grayscale image
            ScratchRestorer._neighbor_interpolation_kernel(
                image, mask, result, window_size
            )
        
        return result
    
    @staticmethod
    def edge_aware_inpainting(image: np.ndarray, 
                             mask: np.ndarray,
                             method: str = 'telea') -> np.ndarray:
        """
        Edge-aware inpainting that preserves edges
        
        Args:
            image: Input image
            mask: Binary mask
            method: 'telea' or 'ns'
        
        Returns:
            Restored image
        """
        if method == 'telea':
            return ScratchRestorer.inpaint_telea(image, mask, radius=3)
        else:
            return ScratchRestorer.inpaint_ns(image, mask, radius=3)
    
    @staticmethod
    def detect_scratches_auto(image: np.ndarray, 
                            threshold: float = 30) -> np.ndarray:
        """
        Automatically detect scratches in an image
        
        Args:
            image: Input image
            threshold: Detection threshold
        
        Returns:
            Binary mask of detected scratches
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Apply morphological operations to connect edges
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Find lines using Hough Transform
        lines = cv2.HoughLinesP(
            edges, 
            rho=1, 
            theta=np.pi/180, 
            threshold=50, 
            minLineLength=30, 
            maxLineGap=10
        )
        
        # Create mask from lines
        mask = np.zeros_like(gray)
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(mask, (x1, y1), (x2, y2), 255, 2)
        
        # Apply threshold to get binary mask
        mask = (mask > threshold).astype(np.uint8) * 255
        
        return mask