"""
NKP Cluster Visualizer - Application Entry Point
"""
import os
from app import create_app
from config import Config

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('BIND_PORT', 9090))
    print("=" * 60)
    print("NKP Cluster Visualizer Starting...")
    print("=" * 60)
    print(f"Environment: {Config.FLASK_ENV}")
    print(f"In-cluster mode: {Config.IN_CLUSTER}")
    print(f"Port: {port}")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=(Config.FLASK_ENV == 'development')
    )