import os
from pathlib import Path
from werkzeug.utils import secure_filename
from typing import Tuple, Optional
import magic

class ImageValidator:
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    
    @classmethod
    def validate_file(cls, file_stream, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file
        """
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"File type not allowed. Allowed types: {', '.join(cls.ALLOWED_EXTENSIONS)}"
        
        # Check file size
        file_stream.seek(0, os.SEEK_END)
        file_size = file_stream.tell()
        file_stream.seek(0)
        
        if file_size > cls.MAX_FILE_SIZE:
            return False, f"File too large. Maximum size is {cls.MAX_FILE_SIZE // (1024*1024)}MB"
        
        # Check file content using magic
        try:
            file_content = file_stream.read(2048)
            file_stream.seek(0)
            
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(file_content)
            
            if not mime_type.startswith('image/'):
                return False, "File is not a valid image"
        except Exception:
            # If magic fails, rely on extension
            pass
        
        return True, None
    
    @classmethod
    def get_safe_filename(cls, filename: str) -> str:
        """Generate a secure filename"""
        return secure_filename(filename)
    
    @staticmethod
    def _convert_to_int(value, default=0, min_val=None, max_val=None):
        """Safely convert value to integer"""
        try:
            if isinstance(value, str):
                result = int(float(value))
            else:
                result = int(value)
            
            if min_val is not None and result < min_val:
                return min_val
            if max_val is not None and result > max_val:
                return max_val
            return result
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _convert_to_float(value, default=1.0, min_val=None, max_val=None):
        """Safely convert value to float"""
        try:
            if isinstance(value, str):
                result = float(value)
            else:
                result = float(value)
            
            if min_val is not None and result < min_val:
                return min_val
            if max_val is not None and result > max_val:
                return max_val
            return result
        except (ValueError, TypeError):
            return default
    
    @classmethod
    def validate_processing_parameters(cls, params: dict) -> Tuple[bool, Optional[str]]:
        """
        Validate image processing parameters with new enhancements
        """
        try:
            # Create converted parameters dict
            converted_params = {}
            
            # Basic enhancements
            converted_params['brightness'] = cls._convert_to_int(
                params.get('brightness', 0), 0, -100, 100
            )
            
            converted_params['contrast'] = cls._convert_to_int(
                params.get('contrast', 0), 0, -100, 100
            )
            
            converted_params['sharpness'] = cls._convert_to_int(
                params.get('sharpness', 0), 0, -100, 100
            )
            
            converted_params['saturation'] = cls._convert_to_int(
                params.get('saturation', 100), 100, 0, 200
            )
            
            converted_params['noise_reduction'] = cls._convert_to_int(
                params.get('noise_reduction', 0), 0, 0, 100
            )
            
            converted_params['detail_enhancement'] = cls._convert_to_int(
                params.get('detail_enhancement', 0), 0, 0, 100
            )
            
            converted_params['inpainting_radius'] = cls._convert_to_int(
                params.get('inpainting_radius', 3), 3, 1, 20
            )
            
            converted_params['brush_size'] = cls._convert_to_int(
                params.get('brush_size', 20), 20, 5, 100
            )
            
            converted_params['gamma'] = cls._convert_to_float(
                params.get('gamma', 1.0), 1.0, 0.1, 3.0
            )
            
            # New parameters for advanced features
            converted_params['temperature'] = cls._convert_to_int(
                params.get('temperature', 0), 0, -100, 100
            )
            
            converted_params['tint'] = cls._convert_to_int(
                params.get('tint', 0), 0, -50, 50
            )
            
            converted_params['quality'] = cls._convert_to_int(
                params.get('quality', 90), 90, 10, 100
            )
            
            # Boolean parameters
            auto_wb = params.get('auto_white_balance', False)
            if isinstance(auto_wb, str):
                converted_params['auto_white_balance'] = auto_wb.lower() in ['true', '1', 'yes', 'on']
            else:
                converted_params['auto_white_balance'] = bool(auto_wb)
            
            # String parameter
            inpainting_method = str(params.get('inpainting_method', 'auto')).lower()
            if inpainting_method not in ['auto', 'telea', 'ns', 'patch', 'multiscale']:
                inpainting_method = 'auto'
            converted_params['inpainting_method'] = inpainting_method
            
            # Update original params with converted values
            params.clear()
            params.update(converted_params)
            
            return True, None
            
        except Exception as e:
            return False, f"Parameter validation error: {str(e)}"