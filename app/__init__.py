from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from .config import get_config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()

def create_app(config_class=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        config_class = get_config()
        
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    
    # Register API blueprints
    from app.api.auth import auth_bp
    from app.api.menu import menu_bp
    from app.api.order import order_bp
    from app.api.sync import sync_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(sync_bp)
    
    # Register web routes blueprints
    from app.routes.web import web_bp
    from app.routes.web_auth import auth_web_bp
    from app.routes.web_menu import menu_web_bp
    
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_web_bp)
    app.register_blueprint(menu_web_bp)
    
    # JWT error handler
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {
            'success': False,
            'message': 'Token has expired',
            'error': 'token_expired'
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {
            'success': False,
            'message': 'Invalid token',
            'error': 'invalid_token'
        }, 401
    
    # Simple route for testing
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}
    
    return app