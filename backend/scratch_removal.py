import cv2
import numpy as np
from numba import jit
from typing import Tuple, Optional
from scipy import ndimage
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

class ScratchRestorer:
    
    @staticmethod
    def preprocess_mask(mask: np.ndarray, feather_radius: int = 5) -> np.ndarray:
        """
        Enhanced mask preprocessing with morphological operations and feathering
        """
        # Ensure mask is binary
        mask_binary = (mask > 127).astype(np.uint8) * 255
        
        # Apply morphological operations to clean mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_processed = cv2.morphologyEx(mask_binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask_processed = cv2.morphologyEx(mask_processed, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Add feathering for soft edges
        if feather_radius > 0:
            mask_float = mask_processed.astype(np.float32) / 255.0
            mask_float = cv2.GaussianBlur(mask_float, (feather_radius*2+1, feather_radius*2+1), feather_radius/2)
            mask_processed = (mask_float * 255).astype(np.uint8)
        
        return mask_processed
    
    @staticmethod
    def advanced_inpaint_telea(image: np.ndarray, 
                              mask: np.ndarray, 
                              radius: int = 3,
                              iterations: int = 3) -> np.ndarray:
        """
        Enhanced Telea algorithm with iterative processing
        """
        if np.sum(mask) == 0:
            return image.copy()
        
        # Preprocess mask
        mask_processed = ScratchRestorer.preprocess_mask(mask)
        
        # Convert image to float for better precision
        image_float = image.astype(np.float32) / 255.0
        
        result = image_float.copy()
        
        for i in range(iterations):
            # Adaptive radius based on iteration
            current_radius = max(1, radius - i)
            
            if len(image.shape) == 3:
                # Process color image with channel correlation
                result_bgr = cv2.cvtColor((result * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
                inpainted = cv2.inpaint(result_bgr, mask_processed, current_radius, cv2.INPAINT_TELEA)
                inpainted = cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            else:
                # Grayscale
                inpainted_uint8 = cv2.inpaint((result * 255).astype(np.uint8), mask_processed, 
                                            current_radius, cv2.INPAINT_TELEA)
                inpainted = inpainted_uint8.astype(np.float32) / 255.0
            
            # Blend with original based on mask
            mask_weight = mask_processed.astype(np.float32) / 255.0
            if len(image.shape) == 3:
                mask_weight = np.stack([mask_weight] * 3, axis=2)
            
            result = result * (1 - mask_weight) + inpainted * mask_weight
        
        return (result * 255).astype(np.uint8)
    
    @staticmethod
    def advanced_inpaint_ns(image: np.ndarray, 
                           mask: np.ndarray, 
                           radius: int = 3) -> np.ndarray:
        """
        Enhanced Navier-Stokes with edge preservation
        """
        if np.sum(mask) == 0:
            return image.copy()
        
        # Preprocess mask
        mask_processed = ScratchRestorer.preprocess_mask(mask, feather_radius=3)
        
        # Calculate edge map to preserve important structures
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        edges = cv2.Canny(gray, 50, 150)
        edges_dilated = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
        
        # Protect edges from inpainting
        protected_mask = np.minimum(mask_processed, 255 - edges_dilated)
        
        if len(image.shape) == 3:
            # Process in LAB color space for better color preservation
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            channels = cv2.split(lab)
            inpainted_channels = []
            
            for i, channel in enumerate(channels):
                inpainted = cv2.inpaint(channel, protected_mask, radius, cv2.INPAINT_NS)
                
                # Special handling for L channel (lightness)
                if i == 0:
                    # Preserve original brightness distribution
                    hist_original = cv2.calcHist([channel], [0], None, [256], [0, 256])
                    hist_inpainted = cv2.calcHist([inpainted], [0], None, [256], [0, 256])
                    # Match histograms for smoother transition
                    inpainted = ScratchRestorer._match_histograms(inpainted, channel, mask_processed)
                
                inpainted_channels.append(inpainted)
            
            result_lab = cv2.merge(inpainted_channels)
            result = cv2.cvtColor(result_lab, cv2.COLOR_LAB2RGB)
        else:
            result = cv2.inpaint(image, protected_mask, radius, cv2.INPAINT_NS)
        
        return result
    
    @staticmethod
    def _match_histograms(source: np.ndarray, target: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Match histograms of inpainted areas to surrounding regions"""
        source_masked = source[mask > 0]
        target_masked = target[mask > 0]
        
        if len(source_masked) == 0 or len(target_masked) == 0:
            return source
        
        # Calculate histograms
        source_hist = np.histogram(source_masked, bins=256, range=(0, 256))[0]
        target_hist = np.histogram(target_masked, bins=256, range=(0, 256))[0]
        
        # Calculate CDFs
        source_cdf = source_hist.cumsum()
        target_cdf = target_hist.cumsum()
        
        # Normalize CDFs
        source_cdf = source_cdf / source_cdf[-1]
        target_cdf = target_cdf / target_cdf[-1]
        
        # Create mapping function
        mapping = np.zeros(256, dtype=np.uint8)
        for i in range(256):
            mapping[i] = np.argmin(np.abs(target_cdf - source_cdf[i]))
        
        # Apply mapping
        result = source.copy()
        mask_indices = mask > 0
        result[mask_indices] = mapping[source[mask_indices]]
        
        return result
    
    @staticmethod
    def patch_based_inpainting(image: np.ndarray, 
                              mask: np.ndarray, 
                              patch_size: int = 9) -> np.ndarray:
        """
        Simple patch-based inpainting algorithm
        """
        if np.sum(mask) == 0:
            return image.copy()
        
        mask_processed = ScratchRestorer.preprocess_mask(mask)
        result = image.copy()
        
        # Get coordinates of pixels to fill
        y_coords, x_coords = np.where(mask_processed > 0)
        
        if len(y_coords) == 0:
            return result
        
        half_patch = patch_size // 2
        
        for y, x in zip(y_coords, x_coords):
            # Define patch boundaries
            y_start = max(0, y - half_patch)
            y_end = min(image.shape[0], y + half_patch + 1)
            x_start = max(0, x - half_patch)
            x_end = min(image.shape[1], x + half_patch + 1)
            
            # Create patch mask
            patch_mask = mask_processed[y_start:y_end, x_start:x_end]
            
            # Skip if patch is completely masked
            if np.all(patch_mask > 0):
                continue
            
            # Find best matching patch from surrounding area
            search_radius = patch_size * 3
            search_y_start = max(0, y - search_radius)
            search_y_end = min(image.shape[0], y + search_radius + 1)
            search_x_start = max(0, x - search_radius)
            search_x_end = min(image.shape[1], x + search_radius + 1)
            
            best_patch = None
            best_distance = float('inf')
            
            for sy in range(search_y_start, search_y_end - patch_size):
                for sx in range(search_x_start, search_x_end - patch_size):
                    # Check if center of candidate patch is not masked
                    if mask_processed[sy + half_patch, sx + half_patch] > 0:
                        continue
                    
                    candidate_patch = image[sy:sy+patch_size, sx:sx+patch_size]
                    current_patch = image[y_start:y_end, x_start:x_end]
                    
                    # Calculate distance only on non-masked areas
                    valid_mask = (patch_mask == 0).astype(np.float32)
                    if np.sum(valid_mask) == 0:
                        continue
                    
                    if len(image.shape) == 3:
                        distance = np.sum((candidate_patch - current_patch) ** 2 * valid_mask[:, :, None]) / np.sum(valid_mask)
                    else:
                        distance = np.sum((candidate_patch - current_patch) ** 2 * valid_mask) / np.sum(valid_mask)
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_patch = candidate_patch
            
            if best_patch is not None:
                # Blend patch into result
                patch_weight = 1.0 - (patch_mask.astype(np.float32) / 255.0)
                if len(image.shape) == 3:
                    patch_weight = np.stack([patch_weight] * 3, axis=2)
                
                result[y_start:y_end, x_start:x_end] = (
                    result[y_start:y_end, x_start:x_end] * (1 - patch_weight) + 
                    best_patch * patch_weight
                ).astype(np.uint8)
        
        return result
    
    @staticmethod
    def multi_scale_inpainting(image: np.ndarray, 
                              mask: np.ndarray, 
                              scales: int = 3) -> np.ndarray:
        """
        Multi-scale inpainting for better large-area restoration
        """
        current_image = image.copy()
        current_mask = mask.copy()
        
        for scale in range(scales):
            scale_factor = 1.0 / (2 ** scale)
            
            if scale_factor < 0.25:  # Minimum scale
                break
            
            # Resize image and mask
            small_width = int(image.shape[1] * scale_factor)
            small_height = int(image.shape[0] * scale_factor)
            
            small_image = cv2.resize(current_image, (small_width, small_height))
            small_mask = cv2.resize(current_mask, (small_width, small_height))
            
            # Apply inpainting at this scale
            if scale == 0:
                # Use advanced algorithm for finest scale
                inpainted = ScratchRestorer.advanced_inpaint_telea(small_image, small_mask)
            else:
                # Use simpler algorithm for coarser scales
                small_mask_binary = (small_mask > 127).astype(np.uint8) * 255
                inpainted = cv2.inpaint(small_image, small_mask_binary, 3, cv2.INPAINT_TELEA)
            
            if scale < scales - 1:
                # Upsample and use as initialization for next scale
                current_image = cv2.resize(inpainted, (image.shape[1], image.shape[0]))
                # Refine mask for next scale
                current_mask = cv2.resize(mask, (image.shape[1], image.shape[0]))
            else:
                # Final result
                result = inpainted
        
        return result
    
    @staticmethod
    def smart_inpainting(image: np.ndarray, 
                        mask: np.ndarray, 
                        method: str = 'auto',
                        adaptive: bool = True) -> np.ndarray:
        """
        Smart inpainting that chooses the best method based on mask properties
        """
        # Calculate mask properties
        mask_area = np.sum(mask > 0)
        total_area = mask.shape[0] * mask.shape[1]
        mask_ratio = mask_area / total_area
        
        # Analyze mask shape complexity
        contours, _ = cv2.findContours((mask > 0).astype(np.uint8), 
                                      cv2.RETR_EXTERNAL, 
                                      cv2.CHAIN_APPROX_SIMPLE)
        contour_count = len(contours)
        
        if method == 'auto':
            # Choose method based on mask characteristics
            if mask_ratio < 0.05:  # Small damage
                method = 'telea'
            elif mask_ratio < 0.2:  # Medium damage
                method = 'patch'
            else:  # Large damage
                method = 'multiscale'
        
        # Apply chosen method
        if method == 'telea':
            return ScratchRestorer.advanced_inpaint_telea(image, mask)
        elif method == 'ns':
            return ScratchRestorer.advanced_inpaint_ns(image, mask)
        elif method == 'patch':
            return ScratchRestorer.patch_based_inpainting(image, mask)
        elif method == 'multiscale':
            return ScratchRestorer.multi_scale_inpainting(image, mask)
        else:
            return ScratchRestorer.advanced_inpaint_telea(image, mask)