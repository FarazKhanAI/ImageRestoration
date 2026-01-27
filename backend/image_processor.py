import cv2
import numpy as np
import os
import time
from typing import Dict, Any
from .scratch_removal import AdvancedInpainter
from .utils import ImageUtils

class RobustImageProcessor:
    def __init__(self):
        self.inpainter = AdvancedInpainter()
        self.utils = ImageUtils()
    
    def process(self, image_path: str, mask_data: dict = None) -> Dict[str, Any]:
        """
        Complete image processing pipeline
        """
        start_time = time.time()
        
        try:
            print(f"\n{'='*50}")
            print("Starting image processing")
            print(f"{'='*50}")
            
            # 1. Load and validate image
            print(f"1. Loading image: {image_path}")
            image = self.utils.load_image(image_path)
            original_shape = image.shape
            print(f"   Image loaded: {original_shape}")
            
            # 2. Resize if too large (for performance)
            max_size = 2000
            h, w = image.shape[:2]
            if max(h, w) > max_size:
                print(f"2. Resizing image from {w}x{h} to max {max_size}")
                image = self.utils.resize_image(image, max_size)
                print(f"   Resized to: {image.shape}")
            


            # 3. Process mask if provided
            mask = None
            mask_created = False
            if mask_data and mask_data.get('coordinates'):
                print("3. Creating mask from coordinates")
                coordinates = mask_data['coordinates']
                brush_size = mask_data.get('brush_size', 20)
                
                print(f"   Points: {len(coordinates)}, Brush: {brush_size}")
                
                # Create mask
                mask = self.inpainter.create_precise_mask(
                    image.shape, 
                    coordinates, 
                    brush_size
                )
                
                # Check if mask has content
                mask_created = bool(mask is not None and np.sum(mask) > 0)
                
                # Save mask to the specified path (if provided in mask_data)
                if mask_created and 'save_path' in mask_data:
                    mask_save_path = mask_data['save_path']
                    success = self.utils.save_image(mask, mask_save_path, quality=100)
                    print(f"   Mask saved to {mask_save_path}: {success}, {np.sum(mask > 0)} white pixels")
                elif mask_created:
                    # Fallback: save to current directory for debugging
                    debug_path = "debug_mask_current.png"
                    self.utils.save_image(mask, debug_path, quality=100)
                    print(f"   Mask saved to debug file: {debug_path}, {np.sum(mask > 0)} white pixels")
                else:
                    print("   WARNING: Mask is empty!")









            # 4. Apply inpainting if mask exists
            processed = image.copy()
            if mask_created:
                print("4. Applying inpainting")
                processed = self.inpainter.multi_algorithm_inpaint(image, mask)
                print("   Inpainting completed")
            else:
                print("4. No mask provided, skipping inpainting")
            
            # 5. Final quality check
            processed = self._final_quality_check(processed, image)
            
            # 6. Calculate metrics (ensure they're Python native types)
            elapsed = time.time() - start_time
            metrics = self._calculate_metrics(image, processed, elapsed, mask_created)
            
            print(f"\nProcessing completed in {elapsed:.2f}s")
            print(f"{'='*50}\n")
            
            return {
                'success': True,
                'original_image': image,
                'processed_image': processed,
                'metrics': metrics,
                'mask_created': mask_created  # Python bool, not numpy bool
            }
            
        except Exception as e:
            print(f"\nERROR in processing: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _final_quality_check(self, processed, original):
        """Ensure output quality"""
        result = processed.copy()
        
        # Check for obvious issues
        if len(result.shape) == 3:
            # Ensure colors are valid
            for c in range(3):
                channel = result[:, :, c]
                if np.max(channel) - np.min(channel) < 10:  # Low contrast
                    # Boost contrast slightly
                    channel = cv2.normalize(channel, None, 0, 255, cv2.NORM_MINMAX)
                    result[:, :, c] = channel
        
        # Ensure proper data type
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
    
    def _calculate_metrics(self, original, processed, elapsed, mask_used):
        """Calculate processing metrics - all Python native types"""
        return {
            'processing_time': float(round(elapsed, 2)),  # Convert to Python float
            'image_size': f"{processed.shape[1]}x{processed.shape[0]}",
            'mask_used': bool(mask_used),  # Convert to Python bool
            'status': 'Success'
        }