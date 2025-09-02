from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import bcrypt

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    reputation_score = db.Column(db.Float, default=100.0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    accounts = db.relationship('Account', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash the password and store it in the database."""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        password_bytes = password.encode('utf-8')
        stored_hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, stored_hash_bytes)
    
    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<User {self.username}>"

@login_manager.user_loader
def load_user(user_id):
    """Load a user given the user ID."""
    return User.query.get(int(user_id))

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Notification {self.id} for User {self.user_id}>"
