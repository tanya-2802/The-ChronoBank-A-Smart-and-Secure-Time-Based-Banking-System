from app.models.loan import Investment
from app.models.account import Account
from app.patterns.structural.facade import BankingFacade
from app import db
from datetime import datetime, timedelta

class InvestmentService:
    """
    Service for managing investments.
    """
    
    def __init__(self):
        self.facade = BankingFacade()
    
    def get_investment_by_id(self, investment_id):
        """Get an investment by ID."""
        return Investment.query.get(investment_id)
    
    def get_investments_by_account(self, account_id, status=None):
        """Get all investments for an account, optionally filtered by status."""
        query = Investment.query.filter_by(account_id=account_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.all()
    
    def create_investment(self, account_id, amount, term_days, user_id=None, ip_address=None):
        """Create a new investment."""
        return self.facade.create_investment(
            account_id=account_id,
            amount=amount,
            term_days=term_days,
            user_id=user_id,
            ip_address=ip_address
        )
    
    def withdraw_investment(self, investment_id):
        """Withdraw an investment."""
        investment = self.get_investment_by_id(investment_id)
        
        if not investment:
            return {"success": False, "message": "Investment not found"}
        
        try:
            # Get the account
            account = Account.query.get(investment.account_id)
            
            if not account:
                return {"success": False, "message": "Account not found"}
            
            # Withdraw the investment
            return_amount = investment.withdraw()
            
            # Add the return amount to the account
            account.deposit(return_amount)
            
            # Save changes
            db.session.commit()
            
            # Format the return amount
            days, remainder = divmod(return_amount, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            formatted_return = []
            if days > 0:
                formatted_return.append(f"{days} day{'s' if days != 1 else ''}")
            if hours > 0:
                formatted_return.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0:
                formatted_return.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            if seconds > 0 or not formatted_return:
                formatted_return.append(f"{seconds} second{'s' if seconds != 1 else ''}")
            
            formatted_return_str = ", ".join(formatted_return)
            
            return {
                "success": True,
                "message": f"Investment withdrawn successfully. You received {formatted_return_str}.",
                "return_amount": return_amount
            }
        except ValueError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"An error occurred: {str(e)}"}
    
    def calculate_return(self, investment_id):
        """Calculate the return on an investment."""
        investment = self.get_investment_by_id(investment_id)
        
        if not investment:
            return {"success": False, "message": "Investment not found"}
        
        return_amount = investment.calculate_return()
        
        # Format the return amount
        days, remainder = divmod(return_amount, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        formatted_return = []
        if days > 0:
            formatted_return.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            formatted_return.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            formatted_return.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 or not formatted_return:
            formatted_return.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        formatted_return_str = ", ".join(formatted_return)
        
        return {
            "success": True,
            "message": f"Expected return: {formatted_return_str}",
            "return_amount": return_amount
        }
    
    def check_matured_investments(self):
        """Check for matured investments and update their status."""
        current_time = datetime.utcnow()
        
        # Find investments that have matured but are still active
        matured_investments = Investment.query.filter(
            Investment.status == 'ACTIVE',
            Investment.maturity_date <= current_time
        ).all()
        
        for investment in matured_investments:
            investment.status = 'MATURED'
        
        db.session.commit()
        
        return len(matured_investments)