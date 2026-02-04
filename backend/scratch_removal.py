import cv2
import numpy as np
from numba import jit
import time  
# Save mask to your desired location
import os
from datetime import datetime



class AdvancedInpainter:
    def __init__(self):
        self.debug = True
    
    def debug_print(self, msg):
        if self.debug:
            print(f"[DEBUG] {msg}")
    
    def create_precise_mask(self, image_shape, coordinates, brush_size=20):
        """
        Create accurate mask from frontend coordinates
        """
        if len(image_shape) == 3:  # If color image, get only height and width
            height, width = image_shape[0], image_shape[1]
        else:
            height, width = image_shape
        
        mask = np.zeros((height, width), dtype=np.uint8)
        
        self.debug_print(f"Creating mask: shape={(height, width)}, points={len(coordinates)}, brush={brush_size}")
        
        if not coordinates:
            return mask
        
        # Convert brush size
        try:
            brush_size = int(float(brush_size))
        except:
            brush_size = 20
        
        # Draw each coordinate point
        for i, point in enumerate(coordinates):
            try:
                # Handle coordinate format
                if isinstance(point, dict):
                    x = int(float(point.get('x', 0)))
                    y = int(float(point.get('y', 0)))
                elif isinstance(point, (list, tuple)) and len(point) >= 2:
                    x = int(float(point[0]))
                    y = int(float(point[1]))
                else:
                    continue
                
                # Ensure bounds
                x = np.clip(x, 0, width - 1)
                y = np.clip(y, 0, height - 1)
                
                # Draw circle
                cv2.circle(mask, (x, y), brush_size, 255, -1)
                
                if i < 2:  # Debug first points
                    self.debug_print(f"  Point {i}: ({x}, {y})")
                    
            except Exception as e:
                continue
        
        # Process mask for better inpainting
        mask = self._process_mask(mask)
        
        self.debug_print(f"Mask created: {np.sum(mask > 0)} white pixels")
        
        # Save mask to instance/uploads/masks directory
        import os
        from pathlib import Path
        
        # Create masks directory if it doesn't exist
        masks_dir = Path("instance/uploads/masks")
        masks_dir.mkdir(parents=True, exist_ok=True)
        
        # Save mask
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mask_filename = f"mask_{timestamp}_{np.random.randint(1000,9999)}.png"
        mask_save_path = masks_dir / mask_filename
        
        # Save the mask
        cv2.imwrite(str(mask_save_path), mask)
        print(f"Mask saved to: {mask_save_path}")
        
        return mask
   



    def _process_mask(self, mask):
        """Enhance mask for better inpainting results"""
        if np.sum(mask) == 0:
            return mask
        
        # 1. Dilate to connect nearby strokes
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        
        # 2. Add soft edges (feathering)
        mask_float = mask.astype(np.float32) / 255.0
        mask_float = cv2.GaussianBlur(mask_float, (5, 5), 1.5)
        mask = (mask_float * 255).astype(np.uint8)
        
        # 3. Ensure binary (0 or 255)
        mask = np.where(mask > 127, 255, 0).astype(np.uint8)
        
        return mask
    
    def multi_algorithm_inpaint(self, image, mask):
        """
        Hybrid inpainting using multiple algorithms for best results
        """
        start_time = time.time()
        
        if np.sum(mask) == 0:
            return image
        
        # Convert to BGR for OpenCV
        if len(image.shape) == 3:
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image.copy()
        
        self.debug_print(f"Inpainting: mask area={np.sum(mask > 0)} pixels")
        
        # Strategy based on mask size
        mask_area = np.sum(mask > 0)
        total_pixels = mask.shape[0] * mask.shape[1]
        ratio = mask_area / total_pixels
        
        self.debug_print(f"Damage ratio: {ratio:.3f}")
        
        if ratio < 0.01:  # Very small damage
            result = self._fast_inpaint(image_bgr, mask)
        elif ratio < 0.1:  # Medium damage
            result = self._quality_inpaint(image_bgr, mask)
        else:  # Large damage
            result = self._advanced_inpaint(image_bgr, mask)
        
        # Convert back to RGB
        if len(image.shape) == 3:
            result = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        
        # Color correction
        result = self._color_correction(result, image, mask)
        
        # Post-processing
        result = self._post_process(result, mask)
        
        elapsed = time.time() - start_time
        self.debug_print(f"Inpainting completed in {elapsed:.2f}s")
        
        return result
    
    def _fast_inpaint(self, image, mask):
        """Fast Telea algorithm for small areas"""
        return cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)
    
    def _quality_inpaint(self, image, mask):
        """Navier-Stokes for better quality"""
        # First pass
        result = cv2.inpaint(image, mask, 3, cv2.INPAINT_NS)
        
        # Second pass with smaller radius
        if np.sum(mask) > 100:
            result = cv2.inpaint(result, mask, 2, cv2.INPAINT_TELEA)
        
        return result
    
    def _advanced_inpaint(self, image, mask):
        """Multi-pass hybrid approach for large areas"""
        results = []
        
        # Pass 1: Telea
        r1 = cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)
        results.append(r1)
        
        # Pass 2: NS
        r2 = cv2.inpaint(image, mask, 3, cv2.INPAINT_NS)
        results.append(r2)
        
        # Pass 3: Telea with different radius
        r3 = cv2.inpaint(image, mask, 2, cv2.INPAINT_TELEA)
        results.append(r3)
        
        # Combine results
        combined = np.zeros_like(image, dtype=np.float32)
        weights = [0.4, 0.4, 0.2]  # Weight for each result
        
        for i, res in enumerate(results):
            combined += res.astype(np.float32) * weights[i]
        
        return np.clip(combined, 0, 255).astype(np.uint8)
    
    def _color_correction(self, inpainted, original, mask):
        """Match colors of inpainted area to surroundings"""
        if np.sum(mask) == 0 or len(inpainted.shape) != 3:
            return inpainted
        
        result = inpainted.copy()
        
        # Get border area around mask
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(mask, kernel, iterations=2)
        border = cv2.subtract(dilated, mask)
        
        if np.sum(border) == 0:
            return result
        
        # Adjust each color channel
        for channel in range(3):
            # Calculate average color in border
            border_values = original[:, :, channel][border > 0]
            if len(border_values) == 0:
                continue
            
            border_mean = np.mean(border_values)
            
            # Calculate average color in inpainted area
            inpainted_values = inpainted[:, :, channel][mask > 0]
            if len(inpainted_values) == 0:
                continue
            
            inpainted_mean = np.mean(inpainted_values)
            
            # Adjust if difference is significant
            if abs(border_mean - inpainted_mean) > 5:
                # Calculate adjustment
                if inpainted_mean > 0:
                    factor = border_mean / inpainted_mean
                    factor = np.clip(factor, 0.7, 1.3)  # Limit adjustment
                    
                    # Apply to inpainted area
                    channel_data = result[:, :, channel].astype(np.float32)
                    channel_data[mask > 0] *= factor
                    result[:, :, channel] = np.clip(channel_data, 0, 255).astype(np.uint8)
        
        return result
    
    def _post_process(self, image, mask):
        """Final enhancements"""
        result = image.copy()
        
        # Light sharpening on inpainted areas
        if np.sum(mask) > 0 and len(image.shape) == 3:
            # Create sharpening kernel
            kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]], dtype=np.float32) * 0.5
            
            # Apply only to inpainted areas
            for c in range(3):
                channel = result[:, :, c].astype(np.float32)
                sharpened = cv2.filter2D(channel, -1, kernel)
                
                # Blend: 30% sharpened, 70% original in masked area
                alpha = 0.3
                channel[mask > 0] = channel[mask > 0] * (1 - alpha) + sharpened[mask > 0] * alpha
                result[:, :, c] = np.clip(channel, 0, 255).astype(np.uint8)
        
        # Ensure proper range
        return np.clip(result, 0, 255).astype(np.uint8)