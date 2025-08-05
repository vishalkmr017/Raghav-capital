import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for Deribit API integration"""
    
    # Deribit API Configuration
    DERIBIT_CLIENT_ID = os.getenv('DERIBIT_CLIENT_ID')
    DERIBIT_CLIENT_SECRET = os.getenv('DERIBIT_CLIENT_SECRET')
    DERIBIT_BASE_URL = os.getenv('DERIBIT_BASE_URL', 'https://test.deribit.com')
    DERIBIT_WS_URL = os.getenv('DERIBIT_WS_URL', 'wss://test.deribit.com/ws/api/v2')
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'deribit_data.db')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'deribit_app.log')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.DERIBIT_CLIENT_ID:
            raise ValueError("DERIBIT_CLIENT_ID is required")
        if not cls.DERIBIT_CLIENT_SECRET:
            raise ValueError("DERIBIT_CLIENT_SECRET is required")
        
        return True