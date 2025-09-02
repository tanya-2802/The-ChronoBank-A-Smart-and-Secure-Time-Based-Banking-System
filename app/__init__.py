from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    import os
    from app.custom_session import CustomSessionInterface
    
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Use custom session interface
    app.session_interface = CustomSessionInterface()
    
    # Configure the app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:admin@localhost/chronobank2')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Add context processors
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.utcnow()}
    
    # Add custom filters
    @app.template_filter('format_time')
    def format_time(seconds):
        """Format time in seconds to a human-readable format."""
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        result = []
        if days > 0:
            result.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            result.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            result.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 or not result:
            result.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        return ", ".join(result)
    
    # Register blueprints
    from app.routes.user_routes import auth_bp
    from app.routes.account_routes import account_bp
    from app.routes.transaction_routes import transaction_bp
    from app.routes.notification_routes import notification_bp
    from app.routes.loan_routes import loan_bp
    from app.routes.investment_routes import investment_bp
    from app.routes.fraud_routes import fraud_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(loan_bp)
    app.register_blueprint(investment_bp)
    app.register_blueprint(fraud_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
