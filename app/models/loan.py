from app import db
from datetime import datetime, timedelta

class Loan(db.Model):
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Time in seconds
    interest_rate = db.Column(db.Float, nullable=False)
    term_days = db.Column(db.Integer, nullable=False)
    remaining_amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='ACTIVE', nullable=False)  # ACTIVE, PAID, DEFAULTED
    repayment_strategy = db.Column(db.String(20), default='FIXED', nullable=False)  # FIXED, DYNAMIC
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    
    def __init__(self, **kwargs):
        super(Loan, self).__init__(**kwargs)
        if 'remaining_amount' not in kwargs:
            self.remaining_amount = self.calculate_total_repayment()
        if 'due_date' not in kwargs:
            self.due_date = datetime.utcnow() + timedelta(days=self.term_days)
    
    def calculate_total_repayment(self):
        """Calculate the total amount to be repaid including interest."""
        return int(self.amount * (1 + self.interest_rate))
    
    def make_payment(self, payment_amount):
        """Make a payment towards the loan."""
        if self.status != 'ACTIVE':
            raise ValueError("Cannot make payment on a non-active loan")
        
        if payment_amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        if payment_amount > self.remaining_amount:
            payment_amount = self.remaining_amount
        
        self.remaining_amount -= payment_amount
        self.updated_at = datetime.utcnow()
        
        # Check if loan is fully paid
        if self.remaining_amount == 0:
            self.status = 'PAID'
        
        return True
    
    def format_amount(self):
        """Format the loan amount in hours only."""
        # Convert seconds to hours (including decimal)
        hours = self.amount / 3600
        
        # Format with 2 decimal places
        return f"{hours:.2f} hour{'s' if hours != 1 else ''}"
    
    def format_remaining(self):
        """Format the remaining amount in hours only."""
        # Convert seconds to hours (including decimal)
        hours = self.remaining_amount / 3600
        
        # Format with 2 decimal places
        return f"{hours:.2f} hour{'s' if hours != 1 else ''}"
    
    def __repr__(self):
        return f"<Loan {self.id} Amount: {self.format_amount()} Status: {self.status}>"

class Investment(db.Model):
    __tablename__ = 'investments'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Time in seconds
    interest_rate = db.Column(db.Float, nullable=False)
    term_days = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='ACTIVE', nullable=False)  # ACTIVE, MATURED, WITHDRAWN
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    maturity_date = db.Column(db.DateTime, nullable=False)
    
    def __init__(self, **kwargs):
        super(Investment, self).__init__(**kwargs)
        if 'maturity_date' not in kwargs:
            self.maturity_date = datetime.utcnow() + timedelta(days=self.term_days)
    
    def calculate_return(self):
        """Calculate the total return on investment including interest.
        
        The return is calculated based on both the amount invested and the term length.
        Longer terms yield higher returns.
        """
        # Base return calculation
        base_return = self.amount * (1 + self.interest_rate)
        
        # Term multiplier: longer terms get better returns
        # For each month (30 days), add 2% to the return
        term_multiplier = 1.0 + (self.term_days / 30) * 0.02
        
        # Calculate final return with both factors
        final_return = int(base_return * term_multiplier)
        
        return final_return
    
    def withdraw(self):
        """Withdraw the investment with returns if matured."""
        if self.status != 'ACTIVE':
            raise ValueError("Investment has already been withdrawn or is not active")
        
        current_time = datetime.utcnow()
        
        if current_time < self.maturity_date:
            # Early withdrawal penalty
            return_amount = self.amount  # No interest for early withdrawal
            self.status = 'WITHDRAWN'
        else:
            # Matured investment
            return_amount = self.calculate_return()
            self.status = 'MATURED'
        
        self.updated_at = current_time
        
        # Return the calculated amount
        return return_amount
    
    def format_amount(self):
        """Format the investment amount in hours only."""
        # Convert seconds to hours (including decimal)
        hours = self.amount / 3600
        
        # Format with 2 decimal places
        return f"{hours:.2f} hour{'s' if hours != 1 else ''}"
    
    def __repr__(self):
        return f"<Investment {self.id} Amount: {self.format_amount()} Status: {self.status}>"
