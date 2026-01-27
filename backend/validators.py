import os
from pathlib import Path
from werkzeug.utils import secure_filename
from typing import Tuple, Optional

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
        
        return True, None
    
    @classmethod
    def validate_processing_parameters(cls, params: dict) -> Tuple[bool, Optional[str]]:
        """
        Validate image processing parameters
        """
        try:
            # Default parameters
            default_params = {
                'inpainting_method': 'multipass',
                'inpainting_radius': 3,
                'brush_size': 20
            }
            
            # Update with provided params
            for key, value in params.items():
                if key in default_params:
                    default_params[key] = value
            
            params.clear()
            params.update(default_params)
            
            return True, None
            
        except Exception as e:
            return False, f"Parameter validation error: {str(e)}"