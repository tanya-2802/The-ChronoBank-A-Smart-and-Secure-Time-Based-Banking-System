import os
from datetime import timedelta

class Config:
    """
    Configuration class for the ChronoBank application.
    """
    
    def __init__(self):
        # Database configuration
        self.SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///chronobank.db')
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        # Security configuration
        self.SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_for_development_only')
        self.JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt_dev_key_for_development_only')
        self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
        self.JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
        
        # Transaction limits
        self.MAX_TRANSACTION_AMOUNT = 10000.0  # Maximum amount for a single transaction
        self.DAILY_TRANSACTION_LIMIT = 50000.0  # Maximum total amount per day
        
        # Fraud detection thresholds
        self.FRAUD_RISK_THRESHOLD = 0.7  # Transactions with risk score above this are flagged
        
        # Interest rates (annual)
        self.SAVINGS_INTEREST_RATE = 0.02  # 2% annual interest for savings accounts
        self.LOAN_BASE_INTEREST_RATE = 0.05  # 5% base interest rate for loans
        
        # Fees
        self.WIRE_TRANSFER_FEE = 25.0  # Fee for wire transfers
        self.OVERDRAFT_FEE = 35.0  # Fee for overdrafts
        self.FOREIGN_TRANSACTION_FEE_PERCENT = 0.03  # 3% fee for foreign transactions
        
        # API rate limiting
        self.RATE_LIMIT_PER_MINUTE = 60  # Maximum number of API requests per minute
        
        # Notification settings
        self.EMAIL_NOTIFICATIONS_ENABLED = True
        self.SMS_NOTIFICATIONS_ENABLED = True
        
        # Logging configuration
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.environ.get('LOG_FILE', 'chronobank.log')
        
        # Session configuration
        self.SESSION_TYPE = 'filesystem'
        self.PERMANENT_SESSION_LIFETIME = timedelta(days=7)
        
        # File upload configuration
        self.UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        self.MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size