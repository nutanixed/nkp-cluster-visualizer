"""
Configuration management for NKP Cluster Visualizer
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Dashboard authentication
    DASHBOARD_USERNAME = os.getenv('DASHBOARD_USERNAME', 'nutanix')
    DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD', 'Nutanix/4u!')
    
    # Session configuration
    SESSION_TIMEOUT_HOURS = int(os.getenv('SESSION_TIMEOUT_HOURS', '24'))
    PERMANENT_SESSION_LIFETIME = SESSION_TIMEOUT_HOURS * 3600
    
    # Kubernetes configuration
    IN_CLUSTER = os.getenv('IN_CLUSTER', 'false').lower() == 'true'
    
    # Cluster configuration
    CLUSTER_NAME = os.getenv('CLUSTER_NAME', 'nkp-dev01')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        pass