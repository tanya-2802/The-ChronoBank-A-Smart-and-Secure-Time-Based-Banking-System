from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from app import db

class LoanRepaymentStrategy(ABC):
    """
    Strategy Pattern Implementation
    
    This abstract class defines the interface for different loan repayment strategies.
    """
    
    @abstractmethod
    def calculate_payment(self, loan, payment_date):
        """
        Calculate the payment amount for a loan.
        
        Args:
            loan: The loan to calculate the payment for
            payment_date: The date of the payment
            
        Returns:
            int: The payment amount in seconds
        """
        pass

class FixedRepaymentStrategy(LoanRepaymentStrategy):
    """
    Fixed repayment strategy implementation.
    
    This strategy divides the loan amount evenly over the term.
    """
    
    def calculate_payment(self, loan, payment_date):
        """
        Calculate the fixed payment amount for a loan.
        
        Args:
            loan: The loan to calculate the payment for
            payment_date: The date of the payment
            
        Returns:
            int: The payment amount in seconds
        """
        # Calculate the total number of payments
        total_payments = loan.term_days
        
        # Calculate the payment amount
        payment_amount = loan.calculate_total_repayment() // total_payments
        
        # Ensure the payment doesn't exceed the remaining amount
        if payment_amount > loan.remaining_amount:
            payment_amount = loan.remaining_amount
        
        return payment_amount

class DynamicRepaymentStrategy(LoanRepaymentStrategy):
    """
    Dynamic repayment strategy implementation.
    
    This strategy adjusts the payment amount based on the remaining term.
    """
    
    def calculate_payment(self, loan, payment_date):
        """
        Calculate the dynamic payment amount for a loan.
        
        Args:
            loan: The loan to calculate the payment for
            payment_date: The date of the payment
            
        Returns:
            int: The payment amount in seconds
        """
        # Calculate the remaining days until the due date
        remaining_days = (loan.due_date - payment_date).days
        
        if remaining_days <= 0:
            # Loan is due, pay the full remaining amount
            return loan.remaining_amount
        
        # Calculate the payment amount based on the remaining days
        payment_amount = loan.remaining_amount // (remaining_days + 1)
        
        # Ensure the payment doesn't exceed the remaining amount
        if payment_amount > loan.remaining_amount:
            payment_amount = loan.remaining_amount
        
        return payment_amount

class EarlyRepaymentStrategy(LoanRepaymentStrategy):
    """
    Early repayment strategy implementation.
    
    This strategy provides a discount for early repayment.
    """
    
    def calculate_payment(self, loan, payment_date):
        """
        Calculate the early repayment amount for a loan.
        
        Args:
            loan: The loan to calculate the payment for
            payment_date: The date of the payment
            
        Returns:
            int: The payment amount in seconds
        """
        # Calculate the remaining days until the due date
        remaining_days = (loan.due_date - payment_date).days
        
        if remaining_days <= 0:
            # Loan is due, pay the full remaining amount
            return loan.remaining_amount
        
        # Calculate the discount percentage based on the remaining days
        discount_percentage = min(remaining_days / loan.term_days * 0.1, 0.1)  # Max 10% discount
        
        # Calculate the discounted payment amount
        payment_amount = int(loan.remaining_amount * (1 - discount_percentage))
        
        return payment_amount

def get_repayment_strategy(strategy_name):
    """
    Factory method to get a repayment strategy by name.
    
    Args:
        strategy_name: The name of the strategy
        
    Returns:
        LoanRepaymentStrategy: The repayment strategy
    """
    strategies = {
        'FIXED': FixedRepaymentStrategy(),
        'DYNAMIC': DynamicRepaymentStrategy(),
        'EARLY': EarlyRepaymentStrategy()
    }
    
    return strategies.get(strategy_name, FixedRepaymentStrategy())
