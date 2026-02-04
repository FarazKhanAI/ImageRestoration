import os
from pathlib import Path

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    
    # Paths - FIXED: Added all required attributes
    BASE_DIR = Path(__file__).parent
    INSTANCE_PATH = BASE_DIR / 'instance'
    
    # Main upload folder
    UPLOAD_FOLDER = INSTANCE_PATH / 'uploads'
    
    # Subdirectories
    UPLOAD_PATH = UPLOAD_FOLDER  # Alias for compatibility
    RAW_UPLOAD_PATH = UPLOAD_FOLDER / 'raw'
    MASK_UPLOAD_PATH = UPLOAD_FOLDER / 'masks'
    PROCESSED_PATH = INSTANCE_PATH / 'processed'
    
    # Processing Settings
    MAX_IMAGE_DIMENSION = 4000
    DEFAULT_QUALITY = 90
    ENABLE_CACHE = True
    THREADS = 4
        # Deployment settings
    @staticmethod
    def get_port():
        return int(os.environ.get('PORT', 5000))
    # Session Settings
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    @staticmethod
    def init_app(app):
        # Create necessary directories
        directories = [
            Config.INSTANCE_PATH,
            Config.UPLOAD_FOLDER,
            Config.RAW_UPLOAD_PATH,
            Config.MASK_UPLOAD_PATH,
            Config.PROCESSED_PATH
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Configure session
        app.config['SECRET_KEY'] = Config.SECRET_KEY
        app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
        app.config['SESSION_TYPE'] = Config.SESSION_TYPE
        app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME