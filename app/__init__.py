"""
NKP Cluster Visualizer - Flask Application Factory
"""
from flask import Flask
from datetime import timedelta
from config import Config


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config_class)
    
    # Set session configuration
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=config_class.SESSION_TIMEOUT_HOURS)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    return app