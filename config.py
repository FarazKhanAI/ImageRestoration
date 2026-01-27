import os
from pathlib import Path

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'imagerestoration924502@flaskapp'
    
    # Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    
    # Paths
    BASE_DIR = Path(__file__).parent
    INSTANCE_PATH = BASE_DIR / 'instance'
    UPLOAD_PATH = INSTANCE_PATH / 'uploads'
    RAW_UPLOAD_PATH = UPLOAD_PATH / 'raw'
    MASK_UPLOAD_PATH = UPLOAD_PATH / 'masks'
    PROCESSED_PATH = INSTANCE_PATH / 'processed'
    
    # Processing Settings
    MAX_IMAGE_DIMENSION = 4000
    DEFAULT_QUALITY = 90
    ENABLE_CACHE = True
    THREADS = 4
    
    # Session Settings
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    @staticmethod
    def init_app(app):
        # Create necessary directories
        directories = [
            Config.INSTANCE_PATH,
            Config.UPLOAD_PATH,
            Config.RAW_UPLOAD_PATH,
            Config.MASK_UPLOAD_PATH,
            Config.PROCESSED_PATH
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)