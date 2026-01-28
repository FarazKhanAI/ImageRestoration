import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Upload Configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
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
    MAX_IMAGE_DIMENSION = int(os.environ.get('MAX_IMAGE_DIMENSION', 4000))
    DEFAULT_QUALITY = int(os.environ.get('DEFAULT_QUALITY', 90))
    ENABLE_CACHE = os.environ.get('ENABLE_CACHE', 'True').lower() == 'true'
    THREADS = int(os.environ.get('THREADS', 4))
    
    # Session Settings
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('PERMANENT_SESSION_LIFETIME', 3600))  # 1 hour default
    
    # Railway/Production Settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Security Settings for Production
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    
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
        
        # Configure session for production
        app.config['SECRET_KEY'] = Config.SECRET_KEY
        app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
        app.config['SESSION_TYPE'] = Config.SESSION_TYPE
        app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME
        app.config['SESSION_COOKIE_SECURE'] = Config.SESSION_COOKIE_SECURE
        app.config['SESSION_COOKIE_HTTPONLY'] = Config.SESSION_COOKIE_HTTPONLY
        app.config['SESSION_COOKIE_SAMESITE'] = Config.SESSION_COOKIE_SAMESITE
        
        # Configure debug mode
        app.config['DEBUG'] = Config.DEBUG


class DevelopmentConfig(Config):
    """Development specific configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Disable in development for local testing
    ENABLE_CACHE = True
    
    def __init__(self):
        super().__init__()


class ProductionConfig(Config):
    """Production specific configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Enable in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Optimize for production
    THREADS = int(os.environ.get('THREADS', 2))  # Lower threads for Railway
    ENABLE_CACHE = True
    
    def __init__(self):
        super().__init__()


class TestingConfig(Config):
    """Testing specific configuration"""
    DEBUG = True
    TESTING = True
    ENABLE_CACHE = False
    
    def __init__(self):
        super().__init__()


def get_config():
    """Get appropriate configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return config_map.get(env, DevelopmentConfig)()


# Create global config instance
config = get_config()